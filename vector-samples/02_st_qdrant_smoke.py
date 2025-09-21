from qdrant_client import QdrantClient
from qdrant_client.http.models import VectorParams, Distance, PointStruct
from sentence_transformers import SentenceTransformer

COLLECTION = "docs"
client = QdrantClient("http://localhost:6333")

# 1) 임베딩 모델(384차원)
model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

docs = [
    "Qdrant는 오픈소스 벡터 DB로 의미 기반 검색을 지원한다.",
    "RAG는 LLM이 답하기 전에 관련 문서를 검색해 컨텍스트로 제공한다.",
    "Kafka 이벤트를 임베딩하여 검색 품질을 개선했다.",
    "Docker로 Qdrant를 띄우고 Python으로 업서트했다.",
    "A10 GPU에서 로컬 LLM 추론 속도를 측정했다."
]

# 2) 임베딩(코사인 안정화)
vecs = model.encode(docs, normalize_embeddings=True)
dim = vecs.shape[1]

# 3) 컬렉션 재생성
client.recreate_collection(
    collection_name=COLLECTION,
    vectors_config=VectorParams(size=dim, distance=Distance.COSINE),
)

# 4) 업서트
points = [
    PointStruct(id=i, vector=vecs[i].tolist(), payload={"text": docs[i]})
    for i in range(len(docs))
]
client.upsert(collection_name=COLLECTION, points=points)

# 5) 검색
query = "RAG에서 벡터 DB가 필요한 이유?"
q_vec = model.encode([query], normalize_embeddings=True)[0].tolist()
hits = client.search(collection_name=COLLECTION, query_vector=q_vec, limit=3)

print(f"\n[Query] {query}\n[Top-3]")
for i, h in enumerate(hits, 1):
    print(f"{i}. score={h.score:.4f} text={h.payload.get('text')}")
