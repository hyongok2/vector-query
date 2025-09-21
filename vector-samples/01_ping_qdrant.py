from qdrant_client import QdrantClient
client = QdrantClient("http://localhost:6333")
print("Qdrant 연결 OK:", client.get_collections() is not None)