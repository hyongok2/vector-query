from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
import time
from typing import Optional, List

from .config import settings
from .models import SearchRequest, SearchResponse, Hit, ModelSpec
from .embeddings import embed_query
from .qdrant_wrapper import query_points
from .embeddings_registry import PRESETS

app = FastAPI(title="Vector Search WebAPI", version="0.1.0")

# CORS
origins = [o.strip() for o in settings.CORS_ALLOW_ORIGINS.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def _require_key(x_api_key: Optional[str]):
    if settings.API_KEY and x_api_key != settings.API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")

@app.get("/health")
def health():
    return {"ok": True, "qdrant_url": settings.QDRANT_URL}

@app.get("/models")
def models():
    allow = set(settings.allow_models)  # {(backend,name), ...}
    items = []
    # 프리셋 중 허용된 것만 노출
    for pid, spec in PRESETS.items():
        pair = (spec["backend"], spec["name"])
        if pair in allow:
            items.append({"preset_id": pid, **spec})
    return {"models": items}

@app.post("/search", response_model=SearchResponse)
def search(req: SearchRequest, x_api_key: Optional[str] = Header(default=None, alias="X-API-Key")):
    _require_key(x_api_key)

    # 1) preset_id가 있으면 우선 적용
    model_spec: ModelSpec = req.model
    if req.preset_id:
        if req.preset_id not in PRESETS:
            raise HTTPException(status_code=400, detail="Unknown preset_id")
        p = PRESETS[req.preset_id]
        model_spec = ModelSpec(**p)

    # 2) 허용목록 체크
    if (model_spec.backend, model_spec.name) not in settings.allow_models:
        raise HTTPException(status_code=400, detail="Model not allowed")

    t0 = time.time()
    try:
        vec = embed_query(req.text, model_spec)
    except Exception as e:
        logger.exception("Embedding failed")
        raise HTTPException(status_code=500, detail=f"Embedding error: {e}")

    try:
        points = query_points(
            cfg=req.qdrant,
            vector=vec,
            limit=req.top_k,
            with_payload=req.with_payload
        )
    except Exception as e:
        logger.exception("Qdrant query failed")
        raise HTTPException(status_code=404, detail=f"Qdrant error: {e}")

    hits: List[Hit] = []
    for p in points:
        score = float(p.score) if getattr(p, "score", None) is not None else 0.0
        if score < req.threshold:
            continue
        hits.append(Hit(id=p.id, score=score, payload=getattr(p, "payload", None)))

    took_ms = int((time.time() - t0) * 1000)
    logger.info({
        "event": "search",
        "took_ms": took_ms,
        "backend": model_spec.backend,
        "model": model_spec.name,
        "collection": req.qdrant.collection,
        "top_k": req.top_k,
        "threshold": req.threshold,
        "result_count": len(hits)
    })
    return SearchResponse(
        took_ms=took_ms,
        model=model_spec,
        collection=req.qdrant.collection,
        total_candidates=len(points),
        hits=hits
    )
