"""Reusable UI components for Streamlit application"""
import streamlit as st
import pandas as pd
import time
from typing import List, Dict, Any, Optional, Callable, Tuple

from src.model_management.embedding_model import EmbeddingModelFactory, ModelConfig
from src.services.qdrant_service import QdrantService
from src.utils.config_manager import AppSettings


class DatabaseConfigComponent:
    """Database configuration UI component"""

    @staticmethod
    def render(settings: AppSettings) -> Tuple[str, str]:
        """Render database configuration UI"""
        st.subheader("🗄️ 데이터베이스 설정")

        db_uri = st.text_input(
            "DB URI",
            value=settings.get('db_uri', ''),
            placeholder="예: sqlite:///test.db",
            help="데이터베이스 연결 문자열을 입력하세요",
            key="db_uri"
        )

        sql_query = st.text_area(
            "SQL 쿼리",
            value=settings.get('sql', 'SELECT * FROM EMSWO'),
            height=100,
            help="실행할 SQL SELECT 쿼리를 입력하세요",
            key="sql"
        )

        return st.session_state.get('db_uri', ''), st.session_state.get('sql', '')


class TextProcessingConfigComponent:
    """Text processing configuration UI component"""

    @staticmethod
    def render(settings: AppSettings) -> Tuple[str, str, int, bool]:
        """Render text processing configuration UI"""
        st.subheader("📝 텍스트 처리 설정")

        pk_col = st.text_input(
            "원본 PK 컬럼명",
            value=settings.get('pk_col', 'id'),
            help="업데이트 기준이 되는 Primary Key 컬럼명",
            key="pk_col"
        )

        template_str = st.text_area(
            "텍스트 템플릿 (Jinja2)",
            value=settings.get('template_str', '{{title}} - {{description}}'),
            height=80,
            help="Jinja2 템플릿 문법을 사용하여 텍스트를 구성하세요",
            key="template_str"
        )

        col1, col2 = st.columns(2)
        with col1:
            max_chars = st.number_input(
                "청킹 최대 문자 수",
                min_value=200,
                max_value=3000,
                value=settings.get('max_chars', 800),
                step=100,
                help="긴 텍스트를 나누는 기준 문자 수",
                key="max_chars"
            )

        with col2:
            strip_ws = st.checkbox(
                "공백 정리",
                value=settings.get('strip_ws', True),
                help="과도한 공백을 정리합니다",
                key="strip_ws"
            )

        return (st.session_state.get('pk_col', 'id'),
                st.session_state.get('template_str', '{{title}} - {{description}}'),
                st.session_state.get('max_chars', 800),
                st.session_state.get('strip_ws', True))


class EmbeddingModelComponent:
    """Embedding model selection UI component"""

    @staticmethod
    def render(settings: AppSettings, model_factory: EmbeddingModelFactory) -> Tuple[str, int]:
        """Render embedding model selection UI"""
        st.subheader("🤖 임베딩 모델")

        available_models = model_factory.get_available_models()
        model_names = [name for name, _ in available_models]
        model_descriptions = {name: desc for name, desc in available_models}

        current_model = settings.get('model', 'mE5-base')
        if current_model not in model_names and model_names:
            current_model = model_names[0]

        model_name = st.selectbox(
            "임베딩 모델",
            model_names,
            index=model_names.index(current_model) if current_model in model_names else 0,
            format_func=lambda x: f"{x} ({model_descriptions.get(x, x)})",
            key="model"
        )

        # Display model dimension info
        model_config = model_factory.config
        dimension = model_config.get_model_dimension(model_name)
        if dimension:
            st.info(f"🎯 벡터 차원: {dimension}")

        selected_model = st.session_state.get('model', 'mE5-base')
        dimension = model_config.get_model_dimension(selected_model)
        return selected_model, dimension or 768


class QdrantConfigComponent:
    """Qdrant configuration UI component"""

    @staticmethod
    def render(settings: AppSettings) -> Tuple[str, int, str]:
        """Render Qdrant configuration UI"""
        st.subheader("🎯 Qdrant 설정")

        col1, col2 = st.columns(2)
        with col1:
            q_host = st.text_input(
                "Qdrant 호스트",
                value=settings.get('q_host', 'localhost'),
                key="q_host"
            )

        with col2:
            q_port = st.number_input(
                "Qdrant 포트",
                min_value=1,
                max_value=65535,
                value=settings.get('q_port', 6333),
                key="q_port"
            )

        collection = st.text_input(
            "컬렉션 이름",
            value=settings.get('collection', 'my_collection'),
            help="벡터를 저장할 컬렉션 이름",
            key="collection"
        )

        return (st.session_state.get('q_host', 'localhost'),
                st.session_state.get('q_port', 6333),
                st.session_state.get('collection', 'my_collection'))


class ProcessingOptionsComponent:
    """Processing options UI component"""

    @staticmethod
    def render(settings: AppSettings) -> Tuple[int, int, int]:
        """Render processing options UI"""
        st.subheader("⚙️ 처리 옵션")

        col1, col2, col3 = st.columns(3)

        with col1:
            preview_rows = st.number_input(
                "미리보기 행 수",
                min_value=10,
                max_value=1000,
                value=settings.get('preview_rows', 50),
                step=10,
                help="화면에 표시할 데이터 개수",
                key="preview_rows"
            )

        with col2:
            max_rows = st.number_input(
                "처리 최대 행 수",
                min_value=0,
                max_value=100000,
                value=settings.get('max_rows', 0),
                step=100,
                help="0 = 제한 없음",
                key="max_rows"
            )

        with col3:
            batch_size = st.number_input(
                "배치 크기",
                min_value=1,
                max_value=256,
                value=settings.get('batch_size', 64),
                step=8,
                help="한 번에 처리할 텍스트 개수",
                key="batch_size"
            )

        return (st.session_state.get('preview_rows', 50),
                st.session_state.get('max_rows', 0),
                st.session_state.get('batch_size', 64))


class CollectionInfoComponent:
    """Collection information display component"""

    @staticmethod
    def render(qdrant_service: QdrantService, collection_name: str):
        """Render collection information"""
        try:
            if qdrant_service.test_connection():
                collection_info = qdrant_service.get_collection_info(collection_name)
                if collection_info:
                    st.info(
                        f"📊 **{collection_name}**: "
                        f"{collection_info['vector_size']}차원, "
                        f"{collection_info['count']}개 벡터"
                    )
        except Exception:
            pass  # Silently ignore connection failures


class ProgressComponent:
    """Progress tracking component"""

    def __init__(self):
        self.progress_bar = None
        self.start_time = None

    def initialize(self, total_items: int):
        """Initialize progress tracking"""
        self.progress_bar = st.progress(0, text="임베딩/업서트 진행 중…")
        self.start_time = time.time()

    def update(self, completed: int, total: int):
        """Update progress with real-time remaining time calculation"""
        if not self.progress_bar or not self.start_time:
            return

        progress_ratio = min(completed / total, 1.0)
        elapsed_time = time.time() - self.start_time

        if completed > 0:
            avg_time_per_item = elapsed_time / completed
            remaining_items = total - completed
            remaining_time = avg_time_per_item * remaining_items

            # 시간 표시 형식 변환 (기존 코드와 동일한 로직)
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

            progress_text = f"임베딩/업서트 {completed}/{total} ({int(100 * progress_ratio)}%) - 남은 시간: {time_str}"
        else:
            progress_text = f"임베딩/업서트 {completed}/{total} ({int(100 * progress_ratio)}%)"

        self.progress_bar.progress(progress_ratio, text=progress_text)

    def update_embedding_progress(self, completed: int, total: int):
        """Update progress for embedding generation phase"""
        if not self.progress_bar:
            return

        progress_ratio = (completed / total) * 0.5  # 임베딩은 전체의 50%
        progress_text = f"임베딩 생성 중... {completed}/{total} ({progress_ratio*100:.1f}%)"
        self.progress_bar.progress(progress_ratio, text=progress_text)

    def update_upsert_progress(self, completed: int, total: int):
        """Update progress for upsert phase"""
        if not self.progress_bar:
            return

        progress_ratio = 0.5 + (completed / total) * 0.5  # 업서트는 50-100%
        elapsed_time = time.time() - self.start_time if self.start_time else 0

        if completed > 0 and elapsed_time > 0:
            # 업서트 단계에서의 시간 계산
            upsert_elapsed = elapsed_time * 0.5  # 대략적인 업서트 시간
            avg_time_per_item = upsert_elapsed / completed
            remaining_items = total - completed
            remaining_time = avg_time_per_item * remaining_items

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

            progress_text = f"업서트 진행 중... {completed}/{total} ({progress_ratio*100:.1f}%) - 남은 시간: {time_str}"
        else:
            progress_text = f"업서트 진행 중... {completed}/{total} ({progress_ratio*100:.1f}%)"

        self.progress_bar.progress(progress_ratio, text=progress_text)

    def complete(self, total: int, elapsed_time: float):
        """Mark progress as complete"""
        if self.progress_bar:
            self.progress_bar.progress(1.0, text="완료!")
        st.success(f"완료! 총 {total} 건, 소요 {elapsed_time:.3f}s")


class CollectionManagerComponent:
    """Collection management UI component"""

    @staticmethod
    def render(qdrant_service: QdrantService):
        """Render collection management interface"""
        st.divider()
        st.header("📁 Qdrant 컬렉션 관리")

        try:
            collections = qdrant_service.get_collections()

            if collections:
                st.subheader("컬렉션 정보")

                # Convert to DataFrame for display
                df_collections = pd.DataFrame(collections)
                df_collections.columns = ["컬렉션", "벡터 차원", "거리 측정", "벡터 개수", "상태"]
                st.dataframe(df_collections, use_container_width=True)

                # Collection deletion interface
                st.subheader("컬렉션 삭제")
                collection_names = [coll["name"] for coll in collections]

                col1, col2 = st.columns(2)
                with col1:
                    st.write("사용 가능한 컬렉션:")
                    for name in collection_names:
                        st.write(f"- {name}")

                with col2:
                    target_collection = st.text_input(
                        "삭제할 컬렉션 이름 입력",
                        placeholder="예: my_collection",
                        key="target_collection_input"
                    )

                    if target_collection:
                        if st.button("🗑️ 삭제", key="delete_collection_btn"):
                            if target_collection in collection_names:
                                st.session_state.pending_delete = target_collection
                                st.rerun()
                            else:
                                st.error(f"{target_collection}은(는) 존재하지 않는 컬렉션입니다.")

                # Deletion confirmation dialog
                if "pending_delete" in st.session_state:
                    delete_name = st.session_state.pending_delete
                    st.error(f"⚠️ **{delete_name}** 컬렉션을 삭제하시겠습니까?")
                    col_yes, col_no = st.columns(2)

                    with col_yes:
                        if st.button("확인 - 삭제"):
                            try:
                                qdrant_service.delete_collection(delete_name)
                                st.success(f"{delete_name} 삭제됨")
                                if st.session_state.get('collection') == delete_name:
                                    st.session_state.collection = "my_collection"
                                del st.session_state.pending_delete
                                st.rerun()
                            except Exception as e:
                                st.error(f"삭제 실패: {e}")

                    with col_no:
                        if st.button("취소"):
                            del st.session_state.pending_delete
                            st.rerun()

            else:
                st.info("컬렉션이 없습니다.")

        except Exception as e:
            st.error(f"Qdrant 연결 실패: {e}")
            st.write("위의 Qdrant 호스트와 포트 설정을 확인하세요.")


class SettingsComponent:
    """Settings save/load UI component"""

    @staticmethod
    def render(settings: AppSettings):
        """Render settings save button"""
        col1, col2 = st.columns([1, 2])
        with col1:
            if st.button("💾", help="현재 설정 저장"):
                if settings.save():
                    st.success("설정 저장됨")
                else:
                    st.error("설정 저장 실패")