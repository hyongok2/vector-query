from typing import Any, Dict, List, Optional
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, ScoredPoint  # pydantic models
from .models import QdrantCfg

def _to_filter(maybe: Optional[Dict[str, Any]]) -> Optional[Filter]:
    if not maybe:
        return None
    # dict 구조가 Qdrant Filter 스키마와 호환된다는 가정
    # (예: {"must": [{"key": "source", "match": {"value": "file.pdf"}}]})
    return Filter(**maybe)

def get_client(url: str) -> QdrantClient:
    return QdrantClient(url=url)

def ensure_collection(client: QdrantClient, name: str) -> None:
    # 존재 확인 (없으면 예외)
    client.get_collection(name)

def query_points(cfg: QdrantCfg, vector: List[float], limit: int, with_payload: bool) -> List[ScoredPoint]:
    client = get_client(cfg.url)
    ensure_collection(client, cfg.collection)
    qf = _to_filter(cfg.query_filter)

    res = client.query_points(
        collection_name=cfg.collection,
        query=vector,
        limit=limit,
        query_filter=qf,
        with_payload=with_payload
    )
    # Python client는 QueryResponse(points=[...]) 형태를 반환
    return list(res.points or [])
