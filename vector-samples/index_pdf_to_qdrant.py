from typing import List
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.http.models import VectorParams, Distance, PointStruct
from pdf_chunker import pdf_to_chunks
import sys
import hashlib
import re
from pathlib import Path

QDRANT_URL = "http://localhost:6333"

def stable_id(s: str) -> int:
    return int(hashlib.md5(s.encode("utf-8")).hexdigest()[:12], 16)

def make_collection_name_from_file(pdf_path: str) -> str:
    # 파일명 기반 + 안전한 문자만 사용 (영문/숫자/언더스코어/대시)
    fname = Path(pdf_path).name
    base = f"pdf__{fname}"
    safe = re.sub(r"[^A-Za-z0-9_\-\.]", "_", base)
    # 점(.)도 허용되지만 너무 많으면 보기 안 좋을 수 있어 간단히 유지
    return safe

def main(pdf_path: str):
    # 1) 청크 생성
    chunks: List[dict] = pdf_to_chunks(pdf_path, max_chars=900, overlap=150)
    if not chunks:
        print("PDF에서 텍스트를 추출하지 못했습니다.")
        return

    # 2) 임베딩 모델 (다국어, 384차원)
    model = SentenceTransformer("intfloat/multilingual-e5-small")
    texts = [f"passage: {c['text']}" for c in chunks]
    vectors = model.encode(texts, normalize_embeddings=True)

    # 3) Qdrant 컬렉션 준비 (이름 안전화)
    collection = make_collection_name_from_file(pdf_path)
    client = QdrantClient(QDRANT_URL)

    if client.collection_exists(collection):
        # 기존 컬렉션 드롭 후 재생성 (원치 않으면 스킵 가능)
        client.delete_collection(collection)

    client.create_collection(
        collection_name=collection,
        vectors_config=VectorParams(size=vectors.shape[1], distance=Distance.COSINE),
    )

    # 4) 업서트 (배치)
    points = []
    for vec, c in zip(vectors, chunks):
        pid = stable_id(f"{c['source']}|p{c['page']}|i{c['chunk_index']}|{c['text'][:32]}")
        points.append(PointStruct(
            id=pid,
            vector=vec.tolist(),
            payload=c  # text, page, chunk_index, source
        ))

    client.upsert(collection_name=collection, points=points)
    print(f"업서트 완료: {len(points)}건 → 컬렉션: {collection}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("사용법: python index_pdf_to_qdrant.py <PDF경로>")
        sys.exit(1)
    main(sys.argv[1])
