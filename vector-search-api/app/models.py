from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional

class QdrantCfg(BaseModel):
    url: str
    collection: str
    query_filter: Optional[Dict[str, Any]] = None

class ModelSpec(BaseModel):
    backend: str = Field(default="st", pattern="^(fastembed|st)$")
    name: str = "BAAI/bge-m3"
    normalize: bool = True
    e5_mode: str = Field(default="auto", pattern="^(auto|query|passage)$")

class SearchRequest(BaseModel):
    text: str
    top_k: int = Field(default=5, ge=1, le=100)
    threshold: float = Field(default=0.0, ge=0.0)
    with_payload: bool = True
    qdrant: QdrantCfg
    model: ModelSpec = ModelSpec()
    # 새로 추가: 프리셋 한 줄로 선택 가능 (들어오면 preset 우선 적용)
    preset_id: Optional[str] = None

class Hit(BaseModel):
    id: Any
    score: float
    payload: Optional[Dict[str, Any]] = None

class SearchResponse(BaseModel):
    took_ms: int
    model: ModelSpec
    collection: str
    total_candidates: int
    hits: List[Hit]
