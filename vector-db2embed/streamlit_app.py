import streamlit as st
import pandas as pd
import numpy as np
from sqlalchemy import create_engine
from jinja2 import Template
from qdrant_client import QdrantClient
from qdrant_client.http.models import VectorParams, Distance, PointStruct
from sentence_transformers import SentenceTransformer
import hashlib, math, time
import uuid
import yaml
import os
import json
import socket
import hashlib

# 사용자 IP 가져오기
def get_user_ip():
    """사용자 IP 또는 고유 식별자 가져오기"""
    try:
        # Streamlit Cloud에서 실행 중인 경우
        headers = st.context.headers if hasattr(st, 'context') else {}
        ip = headers.get('X-Forwarded-For', '')
        if ip:
            ip = ip.split(',')[0].strip()

        # 로컬에서 실행 중인 경우
        if not ip:
            hostname = socket.gethostname()
            ip = socket.gethostbyname(hostname)

        # IP를 해시하여 파일명으로 사용 (개인정보 보호)
        ip_hash = hashlib.md5(ip.encode()).hexdigest()[:8]
        return ip_hash
    except:
        return 'default'

# 사용자별 설정 파일 경로
def get_settings_file():
    user_id = get_user_ip()
    return f'user_settings_{user_id}.json'

def save_settings():
    """현재 설정을 사용자별 파일로 저장"""
    settings = {
        'db_uri': st.session_state.get('db_uri', ''),
        'sql': st.session_state.get('sql', 'SELECT * FROM EMSWO'),
        'pk_col': st.session_state.get('pk_col', 'id'),
        'template_str': st.session_state.get('template_str', '{{title}} - {{description}}'),
        'max_chars': st.session_state.get('max_chars', 800),
        'strip_ws': st.session_state.get('strip_ws', True),
        'q_host': st.session_state.get('q_host', 'localhost'),
        'q_port': st.session_state.get('q_port', 6333),
        'collection': st.session_state.get('collection', 'my_collection'),
        'batch_size': st.session_state.get('batch_size', 64)
    }

    try:
        settings_file = get_settings_file()
        with open(settings_file, 'w', encoding='utf-8') as f:
            json.dump(settings, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        st.error(f"설정 저장 실패: {e}")
        return False

def load_settings():
    """사용자별 저장된 설정을 파일에서 로드"""
    try:
        settings_file = get_settings_file()
        if os.path.exists(settings_file):
            with open(settings_file, 'r', encoding='utf-8') as f:
                settings = json.load(f)
                for key, value in settings.items():
                    st.session_state[key] = value
                return True
    except Exception as e:
        # 에러는 조용히 처리 (처음 사용하는 경우 파일이 없을 수 있음)
        pass
    return False

st.set_page_config(page_title="DB → Text → Embedding → Qdrant", layout="wide")
st.title("DB → Text → Embedding → Qdrant")

# 저장된 설정 파일에서 로드
if 'settings_loaded' not in st.session_state:
    load_settings()
    st.session_state.settings_loaded = True

# Session State 초기화 (파일에서 로드되지 않은 경우 기본값 사용)
if 'db_uri' not in st.session_state:
    st.session_state.db_uri = ""
if 'sql' not in st.session_state:
    st.session_state.sql = "SELECT * FROM EMSWO"
if 'pk_col' not in st.session_state:
    st.session_state.pk_col = "id"
if 'template_str' not in st.session_state:
    st.session_state.template_str = "{{title}} - {{description}}"
if 'max_chars' not in st.session_state:
    st.session_state.max_chars = 800
if 'strip_ws' not in st.session_state:
    st.session_state.strip_ws = True
if 'q_host' not in st.session_state:
    st.session_state.q_host = "localhost"
if 'q_port' not in st.session_state:
    st.session_state.q_port = 6333
if 'collection' not in st.session_state:
    st.session_state.collection = "my_collection"
if 'batch_size' not in st.session_state:
    st.session_state.batch_size = 64
if 'preview_rows' not in st.session_state:
    st.session_state.preview_rows = 50
if 'max_rows' not in st.session_state:
    st.session_state.max_rows = 0  # 0 = 제한 없음

with st.sidebar:
    # 설정 저장 버튼을 작게 배치
    col1, col2 = st.columns([1, 2])
    with col1:
        if st.button("💾", help="현재 설정 저장"):
            if save_settings():
                st.success("저장됨")

    st.header("1) DB 설정")
    db_uri = st.text_input(
        "DB URI",
        value=st.session_state.db_uri,
        placeholder="예) oracle+oracledb://system:oracle@localhost:1521/?service_name=XEPDB1",
        key='db_uri'
    )
    sql = st.text_area("SQL 쿼리", value=st.session_state.sql, key='sql')

    col1, col2 = st.columns(2)
    with col1:
        preview_rows = st.number_input(
            "미리보기 행 수",
            min_value=10,
            max_value=1000,
            value=st.session_state.preview_rows,
            step=10,
            key='preview_rows',
            help="미리보기에 표시할 행 개수"
        )
    with col2:
        max_rows = st.number_input(
            "처리 최대 행 수",
            min_value=0,
            max_value=1000000,
            value=st.session_state.max_rows,
            step=1000,
            key='max_rows',
            help="0 = 제한 없음, 임베딩할 최대 행 수"
        )

    preview_btn = st.button("쿼리 미리보기")

    pk_col = st.sidebar.text_input(
        "원본 PK 컬럼명(선택)",
        value=st.session_state.pk_col,
        key='pk_col',
        help="payload에 원본 PK 저장 및 포인트ID 구성에 사용"
    )

    st.divider()
    st.header("2) 텍스트 빌드/청킹")
    template_str = st.text_area(
        "Jinja 템플릿",
        value=st.session_state.template_str,
        height=100,
        key='template_str',
        help="예: {{id}} | {{title}} — {{description}}"
    )
    max_chars = st.slider(
        "청킹 최대 문자 수",
        200, 3000,
        value=st.session_state.max_chars,
        key='max_chars'
    )
    strip_ws = st.checkbox(
        "공백 정리(strip)",
        value=st.session_state.strip_ws,
        key='strip_ws'
    )

    st.divider()
    st.header("3) 임베딩 & Qdrant")

    # models_config.yaml에서 모델 정보 로드
    try:
        with open('models_config.yaml', 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
            models = config.get('models', {})
            model_list = list(models.keys())
            default_model = config.get('settings', {}).get('default_model', model_list[0] if model_list else None)
    except Exception as e:
        st.error(f"models_config.yaml 로드 실패: {e}")
        models = {}
        model_list = ["bge-m3"]
        default_model = "bge-m3"

    model_name = st.selectbox(
        "임베딩 모델",
        model_list,
        index=model_list.index(default_model) if default_model in model_list else 0,
        format_func=lambda x: f"{x} ({models[x]['description']})" if x in models else x
    )

    # 선택된 모델의 차원 정보 표시
    if model_name in models:
        model_info = models[model_name]
        st.info(f"벡터 차원: {model_info['dimension']} | 경로: {model_info['path']}")
    q_host = st.text_input(
        "Qdrant Host",
        value=st.session_state.q_host,
        key='q_host'
    )
    q_port = st.number_input(
        "Qdrant Port",
        min_value=1,
        max_value=65535,
        value=st.session_state.q_port,
        key='q_port'
    )
    collection = st.text_input(
        "컬렉션 이름",
        value=st.session_state.collection,
        key='collection'
    )
    batch_size = st.slider(
        "배치 크기(임베딩/업서트)",
        16, 512,
        value=st.session_state.batch_size,
        step=16,
        key='batch_size'
    )

    st.divider()
    run_btn = st.button("✨ 임베딩 & 업서트 실행", use_container_width=True)

# 상태 영역
log = st.container()
table_slot = st.empty()

def l2_normalize(vectors: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(vectors, axis=1, keepdims=True) + 1e-12
    return vectors / norms

def build_text_rows(df: pd.DataFrame, tmpl: Template, max_chars: int, strip_ws: bool, pk_col: str):
    texts = []
    for _, row in df.iterrows():
        row_dict = row.to_dict()
        txt = tmpl.render(**row_dict)
        if strip_ws:
            txt = " ".join(txt.split())

        # PK 값 가져오기
        pk_value = row_dict.get(pk_col, _) if pk_col and pk_col in row_dict else _

        # 청킹 (문자 기반)
        chunks = []
        for s in range(0, len(txt), max_chars):
            chunk = txt[s:s+max_chars]
            if chunk and chunk.strip():
                chunks.append(chunk)

        # 각 청크에 PK와 chunk_index 추가
        for chunk_idx, chunk_text in enumerate(chunks):
            texts.append({
                "row_index": int(_),
                "pk": pk_value,
                "chunk_index": chunk_idx,
                "text": chunk_text,
                "source_row": row_dict  # 원본 행 데이터 저장
            })
    return texts

if preview_btn:
    if not st.session_state.db_uri or not st.session_state.sql:
        st.error("DB URI와 SQL 쿼리를 입력하세요.")
    else:
        try:
            df = pd.read_sql(st.session_state.sql, create_engine(st.session_state.db_uri))
            table_slot.dataframe(df.head(st.session_state.preview_rows))
            with log:
                st.success(f"미리보기 성공: 총 {len(df)} rows 중 {min(len(df), st.session_state.preview_rows)}건 표시")
        except Exception as e:
            with log:
                st.error(f"미리보기 실패: {e}")

if run_btn:
    if not st.session_state.db_uri or not st.session_state.sql or not st.session_state.collection:
        st.error("DB URI, SQL, 컬렉션 이름을 입력하세요.")
        st.stop()

    try:
        engine = create_engine(st.session_state.db_uri)
        df = pd.read_sql(st.session_state.sql, engine)

        # 최대 행 수 제한 적용
        if st.session_state.max_rows > 0 and len(df) > st.session_state.max_rows:
            df = df.head(st.session_state.max_rows)
            with log:
                st.warning(f"최대 {st.session_state.max_rows}행만 처리합니다.")

        table_slot.dataframe(df.head(st.session_state.preview_rows))
        with log:
            st.info(f"쿼리 완료: {len(df)} rows")
    except Exception as e:
        st.error(f"DB 쿼리 실패: {e}")
        st.stop()

    # 텍스트 빌드 & 청킹
    try:
        tmpl = Template(st.session_state.template_str)
        docs = build_text_rows(df, tmpl, st.session_state.max_chars, st.session_state.strip_ws, st.session_state.pk_col)
        if not docs:
            st.warning("생성된 텍스트가 없습니다. 템플릿/쿼리를 확인하세요.")
            st.stop()
        st.info(f"청킹 결과 문서 수: {len(docs)}")
    except Exception as e:
        st.error(f"텍스트 빌드 실패: {e}")
        st.stop()

    # 임베딩 모델 로딩
    try:
        # models_config.yaml에서 모델 정보 가져오기
        with open('models_config.yaml', 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
            models = config.get('models', {})

        if model_name in models:
            model_info = models[model_name]
            model_path = model_info['path']
            dim = model_info['dimension']

            # 모델 경로가 존재하는지 확인
            if os.path.exists(model_path):
                st.info(f"모델 로딩: {model_name} from {model_path}")
                model = SentenceTransformer(model_path)
            else:
                st.warning(f"로컬 모델 경로 없음: {model_path}. HuggingFace에서 다운로드 시도...")
                # HuggingFace 모델 이름으로 변환 시도
                hf_model_map = {
                    'bge-m3': 'BAAI/bge-m3',
                    'mE5-small': 'intfloat/multilingual-e5-small',
                    'mE5-base': 'intfloat/multilingual-e5-base',
                    'mE5-large': 'intfloat/multilingual-e5-large',
                    'paraphrase-ml': 'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2'
                }
                hf_model = hf_model_map.get(model_name, model_name)
                model = SentenceTransformer(hf_model)
        else:
            st.error(f"모델 정보를 찾을 수 없음: {model_name}")
            st.stop()

    except Exception as e:
        st.error(f"임베딩 모델 로딩 실패: {e}")
        st.stop()

    # Qdrant 준비
    try:
        qc = QdrantClient(host=st.session_state.q_host, port=st.session_state.q_port, api_key=None)
        existing = [c.name for c in qc.get_collections().collections]
        if st.session_state.collection not in existing:
            qc.recreate_collection(
                collection_name=st.session_state.collection,
                vectors_config=VectorParams(size=dim, distance=Distance.COSINE),
            )
            st.success(f"컬렉션 생성: {st.session_state.collection} (size={dim}, distance=Cosine)")
        else:
            st.info(f"컬렉션 존재: {st.session_state.collection}")
    except Exception as e:
        st.error(f"Qdrant 연결/컬렉션 준비 실패: {e}")
        st.stop()

    # 진행률 바
    progress = st.progress(0, text="임베딩/업서트 진행 중…")
    total = len(docs)
    done = 0
    t0 = time.time()

    # 배치 처리
    try:
        for i in range(0, total, st.session_state.batch_size):
            part = docs[i:i+st.session_state.batch_size]
            texts = [d["text"] for d in part]
            vecs = model.encode(texts, convert_to_numpy=True, show_progress_bar=False)
            vecs = l2_normalize(vecs)  # 코사인용 정규화

            points = []
            for d, v in zip(part, vecs):
                # PK와 chunk_index를 기반으로 고정 ID 생성
                # 이렇게 하면 같은 PK의 같은 청크는 항상 같은 ID를 가짐
                pk_str = str(d["pk"])
                chunk_idx = d["chunk_index"]

                # PK와 chunk_index를 함께 해시하여 고유 ID 생성
                id_string = f"{pk_str}::{chunk_idx}"
                hash_bytes = hashlib.sha256(id_string.encode("utf-8")).digest()
                pid = int.from_bytes(hash_bytes[:8], "big") & ((1 << 64) - 1)  # uint64 정수

                points.append(PointStruct(
                    id=pid,
                    vector=v.tolist(),
                    payload={
                        "text": d["text"],
                        "pk": d["pk"],
                        "chunk_index": d["chunk_index"],
                        "row_index": d["row_index"],
                        "source_row": d.get("source_row", {})  # 원본 행 데이터
                    }
                ))

            qc.upsert(collection_name=st.session_state.collection, points=points)

            done += len(part)
            progress.progress(min(done/total, 1.0),
                              text=f"임베딩/업서트 {done}/{total} ({int(100*done/total)}%)")
        dt = time.time() - t0
        st.success(f"완료! 총 {total} 건, 소요 {dt:.1f}s")
    except Exception as e:
        st.error(f"업서트 중 오류: {e}")
