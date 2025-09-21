import sys
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.http.models import Filter, FieldCondition, MatchValue

QDRANT_URL = "http://localhost:6333"

def encode_query(model, query: str):
    return model.encode([f"query: {query}"], normalize_embeddings=True)[0].tolist()

def search_question(collection: str, question: str, k: int = 5, source_filter: str | None = None):
    client = QdrantClient(QDRANT_URL)

    if not client.collection_exists(collection):
        raise SystemExit(f"컬렉션이 없습니다: {collection}")

    model = SentenceTransformer("intfloat/multilingual-e5-small")
    q_vec = encode_query(model, question)

    q_filter = None
    if source_filter:
        q_filter = Filter(must=[FieldCondition(key="source", match=MatchValue(value=source_filter))])

    # ✅ 버전 호환: 직접 인자로 전달
    res = client.query_points(
        collection_name=collection,
        query=q_vec,
        limit=k,
        query_filter=q_filter,   # ← 여기! filter=  →  query_filter=
        with_payload=True,
        with_vectors=False,
    )

    print(f"\n[Q] {question}\n[Collection] {collection}\n[Top-{k} results]")
    for i, p in enumerate(res.points, 1):
        payload = p.payload or {}
        page = payload.get("page")
        text = (payload.get("text") or "")[:200].replace("\n", " ")
        print(f"{i}. score={p.score:.4f}  page={page}  text={text}...")

if __name__ == "__main__":
    # 사용법: python query_pdf.py <collection_name> "<question>" [<source_filter>]
    if len(sys.argv) < 3:
        print('사용법: python query_pdf.py <collection_name> "<question>" [<source_filter>]')
        sys.exit(1)

    collection = sys.argv[1]
    question = sys.argv[2]
    source = sys.argv[3] if len(sys.argv) >= 4 else None

    search_question(collection, question, k=5, source_filter=source)
