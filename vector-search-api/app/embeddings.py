# app/embeddings.py
import os
from functools import lru_cache
from typing import Iterable, List
import numpy as np

# fastembed (PyTorch 불필요 / ONNXRuntime)
from fastembed import TextEmbedding

# sentence-transformers (선택: ST 백엔드 쓸 때만)
try:
    from sentence_transformers import SentenceTransformer  # pragma: no cover
    import torch  # pragma: no cover
except Exception:
    SentenceTransformer = None  # type: ignore
    torch = None  # type: ignore

from .models import ModelSpec


# --------- 유틸 ---------
def _e5_prefix(text: str, mode: str) -> str:
    """E5 계열 쿼리/패시지 프롬프트 처리."""
    if mode == "query":
        return f"query: {text}"
    if mode == "passage":
        return f"passage: {text}"
    # auto: 검색 쿼리에서는 query 기본
    return f"query: {text}"


def _resolve_name(name: str) -> str:
    """상대경로/환경변수/홈(~)를 안전하게 확장."""
    if not name:
        return name
    # fastembed/ST 모두 로컬 디렉터리 경로를 허용하므로 확장만 해준다
    name = os.path.expandvars(name)
    name = os.path.expanduser(name)
    return name


def _pick_device() -> str:
    """DEVICE=auto|cuda|cpu|mps (기본 auto)"""
    prefer = os.getenv("DEVICE", "auto").lower()
    if SentenceTransformer is None or torch is None:
        return "cpu"
    if prefer == "cpu":
        return "cpu"
    if prefer == "cuda":
        return "cuda" if torch.cuda.is_available() else "cpu"
    if prefer == "mps":
        avail = getattr(torch.backends, "mps", None) and torch.backends.mps.is_available()
        return "mps" if avail else "cpu"

    # auto: cuda → mps → cpu
    if torch.cuda.is_available():
        return "cuda"
    if getattr(torch.backends, "mps", None) and torch.backends.mps.is_available():
        return "mps"
    return "cpu"


def _norm(vec: List[float], enable: bool) -> List[float]:
    if not enable:
        return vec
    v = np.asarray(vec, dtype=np.float32)
    n = np.linalg.norm(v)
    if n > 0:
        v = v / n
    return v.astype(np.float32).tolist()


# --------- fastembed 로더 (경량/CPU 우선) ---------
@lru_cache(maxsize=8)
def _load_fastembed(name: str) -> TextEmbedding:
    name = _resolve_name(name)
    return TextEmbedding(model_name=name)


# --------- ST 로더 (GPU/CPU 자동, trust_remote_code 지원) ---------
_ST_CACHE = {}  # key=(name_resolved, device, trust) -> model

def _load_st(name: str):
    if SentenceTransformer is None or torch is None:
        raise RuntimeError(
            "sentence-transformers/torch 미설치. "
            "pip install sentence-transformers && pip install torch(환경에 맞는 빌드)"
        )
    name_resolved = _resolve_name(name)
    device = _pick_device()
    trust = os.getenv("ST_TRUST_REMOTE_CODE", "0").lower() in ("1", "true", "yes")
    key = (name_resolved, device, trust)
    if key in _ST_CACHE:
        return _ST_CACHE[key], device

    # 스레드 최적화(옵션)
    try:
        n_threads = int(os.getenv("TORCH_NUM_THREADS", "0")) or None
        if n_threads:
            torch.set_num_threads(n_threads)
    except Exception:
        pass

    model = SentenceTransformer(name_resolved, device=device, trust_remote_code=trust)
    _ST_CACHE[key] = model
    return model, device


# --------- 공개 API ---------
def embed_query(text: str, spec: ModelSpec) -> List[float]:
    """
    단일 쿼리 텍스트 → 벡터.
    - fastembed: ONNXRuntime 기반 (CPU)
    - st: PyTorch 기반 (GPU/CPU 자동)
    """
    name = _resolve_name(spec.name)
    t = _e5_prefix(text, spec.e5_mode) if "e5" in name.lower() else text

    if spec.backend == "fastembed":
        model = _load_fastembed(name)
        vec_gen: Iterable[List[float]] = model.embed([t])  # generator
        vec = next(iter(vec_gen))
        return _norm(vec, spec.normalize)

    # ST
    model, device = _load_st(name)
    vec = model.encode(
        t,
        normalize_embeddings=False,
        convert_to_numpy=True,
        device=device
    ).tolist()
    return _norm(vec, spec.normalize)


def embed_many(texts: List[str], spec: ModelSpec, batch_size: int = 64) -> List[List[float]]:
    """
    배치 임베딩 유틸 (인덱싱/대량 처리용).
    """
    name = _resolve_name(spec.name)

    if spec.backend == "fastembed":
        model = _load_fastembed(name)
        out: List[List[float]] = []
        for vec in model.embed(texts, batch_size=batch_size):
            out.append(_norm(vec, spec.normalize))
        return out

    # ST
    model, device = _load_st(name)
    # 디바이스에 따라 배치 조정(대략적인 안전치)
    bs = batch_size
    if device == "cpu":
        bs = min(batch_size, 32)
    arr = model.encode(
        texts,
        batch_size=bs,
        normalize_embeddings=False,
        convert_to_numpy=True,
        device=device
    )
    return [_norm(v.tolist(), spec.normalize) for v in arr]
