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

st.set_page_config(page_title="DB → Text → Embedding → Qdrant", layout="wide")
st.title("DB → Text → Embedding → Qdrant")

with st.sidebar:
    st.header("1) DB 설정")
    db_uri = st.text_input(
        "DB URI",
        placeholder="예) oracle+oracledb://system:oracle@localhost:1521/?service_name=XEPDB1"
    )
    sql = st.text_area("SQL 쿼리", "SELECT * FROM EMSWO")
    preview_btn = st.button("쿼리 미리보기")

    pk_col = st.sidebar.text_input("원본 PK 컬럼명(선택)", value="id", help="payload에 원본 PK 저장 및 포인트ID 구성에 사용")
    rowwise = st.sidebar.toggle("한 행씩 처리(Sequential per-row)", value=True)

    st.divider()
    st.header("2) 텍스트 빌드/청킹")
    template_str = st.text_area("Jinja 템플릿", "{{title}} - {{description}}", height=100,
                                help="예: {{id}} | {{title}} — {{description}}")
    max_chars = st.slider("청킹 최대 문자 수", 200, 3000, 800)
    strip_ws = st.checkbox("공백 정리(strip)", True)

    st.divider()
    st.header("3) 임베딩 & Qdrant")
    model_name = st.selectbox("임베딩 모델", [
        "BAAI/bge-m3",
        "intfloat/multilingual-e5-base",
        "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    ], index=1)
    q_host = st.text_input("Qdrant Host", "localhost")
    q_port = st.number_input("Qdrant Port", min_value=1, max_value=65535, value=6333)
    q_api  = st.text_input("Qdrant API Key (선택)", type="password")
    collection = st.text_input("컬렉션 이름", "my_collection")
    batch_size = st.slider("배치 크기(임베딩/업서트)", 16, 1024, 512, step=16)

    run_btn = st.button("임베딩 & 업서트 실행")

# 상태 영역
log = st.container()
table_slot = st.empty()

def process_one_row(row: dict, tmpl: Template, max_chars: int, strip_ws: bool,
                    model: SentenceTransformer, qc: QdrantClient, collection: str,
                    pk_col: str | None):
    # 1) 텍스트 생성
    txt = Template(tmpl.source).render(**row) if hasattr(tmpl, "source") else tmpl.render(**row)
    if strip_ws:
        txt = " ".join(txt.split())

    # 2) 청킹 (문자 기준)
    chunks = []
    for s in range(0, len(txt), max_chars):
        ch = txt[s:s+max_chars]
        if ch.strip():
            chunks.append(ch)

    if not chunks:
        return {"row_ok": True, "chunks": 0}

    # 3) 임베딩 (이 행의 모든 청크)
    vecs = model.encode(chunks, convert_to_numpy=True, show_progress_bar=False)
    # 코사인 정규화
    vecs = vecs / (np.linalg.norm(vecs, axis=1, keepdims=True) + 1e-12)

    # 4) 업서트
    from qdrant_client.http.models import PointStruct
    import numpy as np, hashlib

    # Qdrant는 포인트ID로 "부호 없는 정수(uint64)" 또는 "UUID"만 허용
    # => 여기서는 항상 "정수(uint64)"를 사용
    UINT64_MAX = (1 << 64) - 1

    def make_int_id(row_pk, chunk_index: int, chunk_text: str) -> int:
        """
        1) pk가 정수이고 (0 <= pk < 2^48) 이면:  (pk << 16) | chunk_index  (chunk_index는 0~65535 가정)
        2) 그 외(pk가 문자열/범위 초과 등)에는:  SHA1(pk:chunk_index:chunk_text)의 상위 8바이트를 uint64로 사용
        """
        # 케이스 1: pk를 안전한 정수로 사용
        try:
            pk_val = int(row_pk)
            if 0 <= pk_val < (1 << 48) and 0 <= chunk_index < (1 << 16):
                return (pk_val << 16) | chunk_index
        except Exception:
            pass

        # 케이스 2: 64비트 해시로 폴백
        h = hashlib.sha1(f"{row_pk}:{chunk_index}:{chunk_text}".encode("utf-8")).digest()
        val = int.from_bytes(h[:8], "big")  # 상위 8바이트 => 0 ~ 2^64-1
        return val & UINT64_MAX

    points = []
    row_pk = row.get(pk_col) if pk_col else None

    # vecs: np.ndarray (num_chunks, dim), chunks: List[str]
    if isinstance(vecs, list):
        vecs = np.asarray(vecs, dtype=float)

    for idx, (ch, v) in enumerate(zip(chunks, vecs)):
        pid = make_int_id(row_pk, idx, ch)  # ✅ 항상 uint64 정수
        points.append(
            PointStruct(
                id=pid,
                vector=np.asarray(v, dtype=float).tolist(),
                payload={
                    "text": ch,
                    "pk": row_pk,
                    "chunk_index": idx,
                    "source_row": row,   # 민감정보 주의. 필요 필드만 저장 권장
                },
            )
        )

    # 즉시 적용 확인 위해 wait=True 권장
    qc.upsert(collection_name=collection, points=points, wait=True)
    return {"row_ok": True, "chunks": len(chunks)}


def l2_normalize(vectors: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(vectors, axis=1, keepdims=True) + 1e-12
    return vectors / norms

def build_text_rows(df: pd.DataFrame, tmpl: Template, max_chars: int, strip_ws: bool):
    texts = []
    for _, row in df.iterrows():
        txt = tmpl.render(**row.to_dict())
        if strip_ws:
            txt = " ".join(txt.split())
        # 청킹 (문자 기반)
        for s in range(0, len(txt), max_chars):
            chunk = txt[s:s+max_chars]
            if chunk and chunk.strip():
                texts.append({
                    "row_index": int(_),
                    "text": chunk
                })
    return texts

if preview_btn:
    try:
        df = pd.read_sql(sql, create_engine(db_uri))
        table_slot.dataframe(df.head(50))
        with log:
            st.success(f"미리보기 성공: {len(df)} rows")
    except Exception as e:
        with log:
            st.error(f"미리보기 실패: {e}")

if run_btn:
    if not db_uri or not sql or not collection:
        st.error("DB URI, SQL, 컬렉션 이름을 입력하세요.")
        st.stop()

    try:
        engine = create_engine(db_uri)
        df = pd.read_sql(sql, engine)
        table_slot.dataframe(df.head(50))
        with log:
            st.info(f"쿼리 완료: {len(df)} rows")
    except Exception as e:
        st.error(f"DB 쿼리 실패: {e}")
        st.stop()

    # 텍스트 빌드 & 청킹
    try:
        tmpl = Template(template_str)
        docs = build_text_rows(df, tmpl, max_chars, strip_ws)
        if not docs:
            st.warning("생성된 텍스트가 없습니다. 템플릿/쿼리를 확인하세요.")
            st.stop()
        st.info(f"청킹 결과 문서 수: {len(docs)}")
    except Exception as e:
        st.error(f"텍스트 빌드 실패: {e}")
        st.stop()

    # 임베딩 모델 로딩
    try:
        st.info(f"모델 로딩: {model_name}")
        model = SentenceTransformer(model_name)
        dim = model.get_sentence_embedding_dimension()
    except Exception as e:
        st.error(f"임베딩 모델 로딩 실패: {e}")
        st.stop()

    # Qdrant 준비
    try:
        qc = QdrantClient(host=q_host, port=q_port, api_key=q_api or None)
        existing = [c.name for c in qc.get_collections().collections]
        if collection not in existing:
            qc.recreate_collection(
                collection_name=collection,
                vectors_config=VectorParams(size=dim, distance=Distance.COSINE),
            )
            st.success(f"컬렉션 생성: {collection} (size={dim}, distance=Cosine)")
        else:
            st.info(f"컬렉션 존재: {collection}")
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
        for i in range(0, total, batch_size):
            part = docs[i:i+batch_size]
            texts = [d["text"] for d in part]
            vecs = model.encode(texts, convert_to_numpy=True, show_progress_bar=False)
            vecs = l2_normalize(vecs)  # 코사인용 정규화

            points = []
            for d, v in zip(part, vecs):
                # Qdrant는 정수 또는 UUID만 허용 - SHA256 해시의 상위 8바이트를 정수로 변환
                hash_bytes = hashlib.sha256(d["text"].encode("utf-8")).digest()
                pid = int.from_bytes(hash_bytes[:8], "big") & ((1 << 64) - 1)  # uint64 정수
                points.append(PointStruct(
                    id=pid,
                    vector=v.tolist(),
                    payload={
                        "text": d["text"],
                        "row_index": d["row_index"]
                    }
                ))

            qc.upsert(collection_name=collection, points=points)

            done += len(part)
            progress.progress(min(done/total, 1.0),
                              text=f"임베딩/업서트 {done}/{total} ({int(100*done/total)}%)")
        dt = time.time() - t0
        st.success(f"완료! 총 {total} 건, 소요 {dt:.1f}s")
    except Exception as e:
        st.error(f"업서트 중 오류: {e}")
