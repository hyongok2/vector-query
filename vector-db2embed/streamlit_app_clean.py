"""Clean, refactored Streamlit application for DB to Vector embedding"""
import streamlit as st
import pandas as pd
import time
from typing import Optional

# Import our clean modules
from model_management.embedding_model import EmbeddingModelFactory, ModelConfig
from services.database_service import DatabaseServiceFactory, QueryValidator
from services.qdrant_service import QdrantServiceFactory, BatchProcessor
from services.text_processor import TextProcessorFactory
from utils.config_manager import ConfigManagerFactory
from components.ui_components import (
    DatabaseConfigComponent,
    TextProcessingConfigComponent,
    EmbeddingModelComponent,
    QdrantConfigComponent,
    ProcessingOptionsComponent,
    CollectionInfoComponent,
    ProgressComponent,
    CollectionManagerComponent,
    SettingsComponent
)


class EmbeddingApp:
    """Main application controller"""

    def __init__(self):
        self.setup_page_config()
        self.initialize_services()
        self.initialize_session_state()

    def setup_page_config(self):
        """Setup Streamlit page configuration"""
        st.set_page_config(
            page_title="DB → Text → Embedding → Qdrant",
            layout="wide"
        )
        st.title("DB → Text → Embedding → Qdrant")

    def initialize_services(self):
        """Initialize all services and components"""
        # Configuration
        self.config_manager = ConfigManagerFactory.create_file_manager()
        self.settings = ConfigManagerFactory.create_app_settings(self.config_manager)

        # Model management
        self.model_config = ModelConfig()
        self.model_factory = EmbeddingModelFactory(self.model_config)

        # Services (will be created as needed)
        self.database_service = None
        self.qdrant_service = None
        self.text_processor = TextProcessorFactory.create_processor()

    def initialize_session_state(self):
        """Initialize Streamlit session state with saved settings"""
        if 'settings_loaded' not in st.session_state:
            # Load all settings into session state
            for key, value in self.settings.get_all().items():
                if key not in st.session_state:
                    st.session_state[key] = value
            st.session_state.settings_loaded = True

    def render_sidebar(self):
        """Render sidebar with all configuration options"""
        with st.sidebar:
            # Settings save button
            SettingsComponent.render(self.settings)

            # Database configuration
            db_uri, sql_query = DatabaseConfigComponent.render(self.settings)

            # Text processing configuration
            pk_col, template_str, max_chars, strip_ws = TextProcessingConfigComponent.render(self.settings)

            # Embedding model selection
            model_name, dimension = EmbeddingModelComponent.render(self.settings, self.model_factory)

            # Qdrant configuration
            q_host, q_port, collection = QdrantConfigComponent.render(self.settings)

            # Processing options
            preview_rows, max_rows, batch_size = ProcessingOptionsComponent.render(self.settings)

            # Update settings with current values
            self.settings.update({
                'db_uri': db_uri,
                'sql': sql_query,
                'pk_col': pk_col,
                'template_str': template_str,
                'max_chars': max_chars,
                'strip_ws': strip_ws,
                'model': model_name,
                'q_host': q_host,
                'q_port': q_port,
                'collection': collection,
                'preview_rows': preview_rows,
                'max_rows': max_rows,
                'batch_size': batch_size
            })

    def render_main_content(self):
        """Render main content area"""
        # Collection info display
        self.render_collection_info()

        # Action buttons
        col1, col2 = st.columns(2)
        with col1:
            preview_btn = st.button("👁️ 데이터 미리보기", use_container_width=True)
        with col2:
            run_btn = st.button("✨ 임베딩 & 업서트 실행", use_container_width=True)

        # Status area
        log = st.container()
        table_slot = st.empty()

        # Handle button clicks
        if preview_btn:
            self.handle_preview(log, table_slot)

        if run_btn:
            self.handle_embedding_process(log, table_slot)

    def render_collection_info(self):
        """Render collection information if available"""
        try:
            qdrant_service = self.get_qdrant_service()
            CollectionInfoComponent.render(qdrant_service, self.settings.get('collection'))
        except Exception:
            pass  # Silently ignore if Qdrant is not available

    def handle_preview(self, log, table_slot):
        """Handle data preview request"""
        db_uri = self.settings.get('db_uri')
        sql_query = self.settings.get('sql')

        if not db_uri or not sql_query:
            st.error("DB URI와 SQL 쿼리를 입력하세요.")
            return

        try:
            # Validate query
            QueryValidator.validate_query(sql_query)

            # Execute query
            database_service = self.get_database_service()
            df = database_service.execute_query(sql_query)

            # Display preview
            preview_rows = self.settings.get('preview_rows', 50)
            table_slot.dataframe(df.head(preview_rows))

            with log:
                st.success(f"미리보기 성공: 총 {len(df)} rows 중 {min(len(df), preview_rows)}건 표시")

        except Exception as e:
            with log:
                st.error(f"미리보기 실패: {e}")

    def handle_embedding_process(self, log, table_slot):
        """Handle the complete embedding and upserting process"""
        # Validate inputs
        db_uri = self.settings.get('db_uri')
        sql_query = self.settings.get('sql')
        collection = self.settings.get('collection')

        if not db_uri or not sql_query or not collection:
            st.error("DB URI, SQL, 컬렉션 이름을 입력하세요.")
            return

        try:
            # Step 1: Execute query and get data
            with log:
                st.info("🔍 데이터베이스에서 데이터 가져오는 중...")

            database_service = self.get_database_service()
            QueryValidator.validate_query(sql_query)
            df = database_service.execute_query(sql_query)

            # Apply max rows limit
            max_rows = self.settings.get('max_rows', 0)
            if max_rows > 0 and len(df) > max_rows:
                df = df.head(max_rows)
                with log:
                    st.warning(f"최대 {max_rows}행만 처리합니다.")

            # Display data
            preview_rows = self.settings.get('preview_rows', 50)
            table_slot.dataframe(df.head(preview_rows))

            with log:
                st.info(f"쿼리 완료: {len(df)} rows")

            # Step 2: Process text documents
            with log:
                st.info("📝 텍스트 처리 및 청킹 중...")

            documents = self.text_processor.build_text_documents(
                df=df,
                template=self.settings.get('template_str'),
                pk_column=self.settings.get('pk_col'),
                max_chars=self.settings.get('max_chars'),
                strip_whitespace=self.settings.get('strip_ws')
            )

            if not documents:
                st.error("처리된 텍스트가 없습니다. 템플릿이나 데이터를 확인하세요.")
                return

            with log:
                st.info(f"텍스트 처리 완료: {len(documents)} 개 청크 생성")

            # Step 3: Load embedding model
            with log:
                st.info("🤖 임베딩 모델 로딩 중...")

            model_name = self.settings.get('model')
            embedding_model = self.model_factory.create_model(model_name)
            dimension = embedding_model.get_dimension()

            with log:
                st.info(f"모델 로딩 완료: {model_name} ({dimension}차원)")

            # Step 4: Prepare Qdrant
            with log:
                st.info("🎯 Qdrant 컬렉션 준비 중...")

            qdrant_service = self.get_qdrant_service()
            created = qdrant_service.ensure_collection(collection, dimension)

            with log:
                if created:
                    st.success(f"컬렉션 생성: {collection} (size={dimension}, distance=Cosine)")
                else:
                    st.info(f"컬렉션 존재: {collection}")

            # Step 5: Generate embeddings and upsert
            with log:
                st.info("⚡ 임베딩 생성 및 업서트 중...")

            # 전체 시간 측정 시작
            total_start_time = time.time()

            # Create progress bar directly
            progress_bar = st.progress(0, text="시작 중...")
            status_text = st.empty()

            # Prepare batch processor
            batch_size = self.settings.get('batch_size', 64)
            batch_processor = BatchProcessor(qdrant_service, batch_size)

            # Generate embeddings in batches with progress
            texts = [doc["text"] for doc in documents]
            embeddings = []
            total_texts = len(texts)

            # Create status placeholder
            status_placeholder = st.empty()

            # Variables for time estimation
            avg_time_per_batch = None
            batches_completed = 0
            total_batches = (total_texts + batch_size - 1) // batch_size

            for i in range(0, total_texts, batch_size):
                batch_texts = texts[i:i + batch_size]
                current_batch_size = len(batch_texts)
                current_batch_num = batches_completed + 1

                # Show status before processing current batch
                if avg_time_per_batch and batches_completed > 0:
                    # 현재 배치 처리 예상 시간
                    estimated_batch_time = avg_time_per_batch
                    remaining_batches = total_batches - current_batch_num
                    remaining_time_total = avg_time_per_batch * remaining_batches

                    if estimated_batch_time < 60:
                        batch_time_str = f"{estimated_batch_time:.1f}초"
                    else:
                        minutes = int(estimated_batch_time // 60)
                        seconds = int(estimated_batch_time % 60)
                        batch_time_str = f"{minutes}분 {seconds}초"

                    if remaining_time_total < 60:
                        remaining_str = f"{remaining_time_total:.1f}초"
                    elif remaining_time_total < 3600:
                        minutes = int(remaining_time_total // 60)
                        seconds = int(remaining_time_total % 60)
                        remaining_str = f"{minutes}분 {seconds}초"
                    else:
                        hours = int(remaining_time_total // 3600)
                        minutes = int((remaining_time_total % 3600) // 60)
                        remaining_str = f"{hours}시간 {minutes}분"

                    status_placeholder.info(f"🤖 임베딩 생성 중... {i}/{total_texts} (배치 {current_batch_num}/{total_batches}) - 배치 예상: {batch_time_str}, 전체 남은 시간: {remaining_str}")
                else:
                    status_placeholder.info(f"🤖 임베딩 생성 중... {i}/{total_texts} (배치 {current_batch_num}/{total_batches})")

                embedding_progress = (i / total_texts) * 0.5
                progress_bar.progress(embedding_progress, text=f"임베딩 생성: {i}/{total_texts}")

                # Process batch (시간이 걸리는 실제 작업)
                batch_start_time = time.time()
                batch_embeddings = embedding_model.encode(batch_texts)
                embeddings.extend(batch_embeddings)
                batch_end_time = time.time()

                # Update after processing with remaining time
                completed_texts = i + current_batch_size
                batches_completed += 1
                embedding_progress = (completed_texts / total_texts) * 0.5

                # Calculate timing statistics
                elapsed_time = time.time() - total_start_time
                avg_time_per_batch = elapsed_time / batches_completed

                if batches_completed < total_batches:
                    remaining_batches = total_batches - batches_completed
                    remaining_time = avg_time_per_batch * remaining_batches

                    # Format time string
                    if remaining_time < 60:
                        time_str = f"{remaining_time:.1f}초"
                    elif remaining_time < 3600:
                        minutes = int(remaining_time // 60)
                        seconds = int(remaining_time % 60)
                        time_str = f"{minutes}분 {seconds}초"
                    else:
                        hours = int(remaining_time // 3600)
                        minutes = int((remaining_time % 3600) // 60)
                        time_str = f"{hours}시간 {minutes}분"

                    status_text = f"🤖 임베딩 완료... {completed_texts}/{total_texts} ({embedding_progress*100:.1f}%) - 남은 시간: {time_str}"
                    progress_text = f"임베딩: {completed_texts}/{total_texts} - 남은 시간: {time_str}"
                else:
                    status_text = f"🤖 임베딩 완료... {completed_texts}/{total_texts} ({embedding_progress*100:.1f}%)"
                    progress_text = f"임베딩: {completed_texts}/{total_texts}"

                status_placeholder.info(status_text)
                progress_bar.progress(embedding_progress, text=progress_text)

            status_placeholder.success("✅ 임베딩 생성 완료, 업서트 시작...")

            # Process in batches with progress updates
            upsert_start_time = time.time()
            def progress_callback(processed, total, elapsed):
                upsert_progress = 0.5 + (processed / total) * 0.5  # 50-100%

                # Calculate remaining time for upsert
                upsert_elapsed = time.time() - upsert_start_time
                if processed > 0:
                    avg_time_per_item = upsert_elapsed / processed
                    remaining_items = total - processed
                    remaining_time = avg_time_per_item * remaining_items

                    # Format time string
                    if remaining_time < 60:
                        time_str = f"{remaining_time:.1f}초"
                    elif remaining_time < 3600:
                        minutes = int(remaining_time // 60)
                        seconds = int(remaining_time % 60)
                        time_str = f"{minutes}분 {seconds}초"
                    else:
                        hours = int(remaining_time // 3600)
                        minutes = int((remaining_time % 3600) // 60)
                        time_str = f"{hours}시간 {minutes}분"

                    status_text = f"⚡ 업서트 진행 중... {processed}/{total} ({upsert_progress*100:.1f}%) - 남은 시간: {time_str}"
                    progress_text = f"업서트: {processed}/{total} - 남은 시간: {time_str}"
                else:
                    status_text = f"⚡ 업서트 진행 중... {processed}/{total} ({upsert_progress*100:.1f}%)"
                    progress_text = f"업서트: {processed}/{total}"

                status_placeholder.info(status_text)
                progress_bar.progress(upsert_progress, text=progress_text)

            import numpy as np
            embeddings_array = np.array(embeddings)
            processed_count, batch_elapsed_time = batch_processor.process_batches(
                collection_name=collection,
                documents=documents,
                embeddings=embeddings_array,
                progress_callback=progress_callback
            )

            # 전체 소요 시간 계산 (임베딩 + 업서트)
            total_elapsed_time = time.time() - total_start_time

            # Complete
            progress_bar.progress(1.0, text="완료!")
            status_placeholder.success(f"🎉 완료! 총 {processed_count} 건, 소요 {total_elapsed_time:.3f}s")

        except Exception as e:
            st.error(f"처리 중 오류 발생: {e}")

    def get_database_service(self):
        """Get or create database service"""
        db_uri = self.settings.get('db_uri')
        if self.database_service is None or getattr(self.database_service, 'connection_uri', None) != db_uri:
            self.database_service = DatabaseServiceFactory.create_service(db_uri)
        return self.database_service

    def get_qdrant_service(self):
        """Get or create Qdrant service"""
        q_host = self.settings.get('q_host')
        q_port = self.settings.get('q_port')

        if (self.qdrant_service is None or
                getattr(self.qdrant_service, 'host', None) != q_host or
                getattr(self.qdrant_service, 'port', None) != q_port):
            self.qdrant_service = QdrantServiceFactory.create_service(q_host, q_port)

        return self.qdrant_service

    def render_collection_management(self):
        """Render collection management section"""
        try:
            qdrant_service = self.get_qdrant_service()
            CollectionManagerComponent.render(qdrant_service)
        except Exception as e:
            st.error(f"컬렉션 관리 오류: {e}")

    def run(self):
        """Run the complete application"""
        self.render_sidebar()
        self.render_main_content()
        self.render_collection_management()


def main():
    """Main application entry point"""
    app = EmbeddingApp()
    app.run()


if __name__ == "__main__":
    main()