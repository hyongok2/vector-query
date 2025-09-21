# download_models_strong.py
import os, shutil, sys
from pathlib import Path

# 1) 사전: huggingface_hub + sentence-transformers 필요
try:
    from sentence_transformers import SentenceTransformer
except Exception as e:
    print("[!] sentence-transformers 미설치:", e, file=sys.stderr)
    print("    pip install sentence-transformers")
    sys.exit(1)

try:
    from huggingface_hub import snapshot_download
except Exception as e:
    print("[!] huggingface_hub 미설치:", e, file=sys.stderr)
    print("    pip install huggingface_hub")
    sys.exit(1)

# 2) 다운로드 목록 (preset_id -> (repo_id, trust_remote_code))
MODELS = {
    #fastembed 계열도 같이 받아두면 캐시/오프라인에 유리
    "bge-m3":            ("BAAI/bge-m3", False),
    "mE5-small":         ("intfloat/multilingual-e5-small", False),

    #ST 계열
    "mE5-base":          ("intfloat/multilingual-e5-base", False),
    "mE5-large":         ("intfloat/multilingual-e5-large", False),
    "paraphrase-ml":     ("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2", False),
    "ko-sbert":          ("snunlp/KR-SBERT-V40K-klueNLI-augSTS", False),
    "ko-sroberta":       ("jhgan/ko-sroberta-multitask", False),

    "ko-simcse":         ("BM-K/KoSimCSE-roberta-multitask", False),
    "ko-sentence":       ("snunlp/KR-SBERT-V40K-klueNLI-augSTS", False),  # 이미 위에 있지만, 프리셋 분리용으로 둬도 됨
    "nomic-embed":       ("nomic-ai/nomic-embed-text-v1", True),
}

OUT_DIR = Path("../models")
OUT_DIR.mkdir(parents=True, exist_ok=True)

def try_sentence_transformers(repo_id: str, out: Path, trust: bool):
    """
    1차 시도: ST로 로드 후 .save(out)
    """
    print(f"[ST] loading {repo_id} (trust_remote_code={trust})")
    m = SentenceTransformer(repo_id, trust_remote_code=trust)
    out.mkdir(parents=True, exist_ok=True)
    m.save(str(out))
    print(f"[ST] saved -> {out}")

def fallback_snapshot(repo_id: str, out: Path):
    """
    2차 시도: huggingface_hub로 스냅샷 다운로드(레포 전체 파일)
    """
    print(f"[HF] snapshot_download {repo_id}")
    # allow_patterns/ignore_patterns 로 가볍게 받을 수도 있음(필요시 조정)
    cached = snapshot_download(repo_id, local_dir=str(out), local_dir_use_symlinks=False)
    print(f"[HF] downloaded -> {cached}")

def download_one(preset_id: str, repo_id: str, trust: bool):
    target = OUT_DIR / preset_id
    # 기존이 있으면 넘어가고 싶으면 주석 해제
    # if target.exists():
    #     print(f"[SKIP] exists: {target}")
    #     return
    try:
        try_sentence_transformers(repo_id, target, trust)
        return
    except Exception as e:
        print(f"[ST] failed for {repo_id}: {e}")

    # ST 실패 시 HfHub로 통째 복제
    try:
        fallback_snapshot(repo_id, target)
        return
    except Exception as e:
        print(f"[HF] fallback failed for {repo_id}: {e}")
        raise

if __name__ == "__main__":
    # 프록시/토큰 필요한 환경이면 여기 설정
    # os.environ["HF_ENDPOINT"] = "https://huggingface.co"
    # os.environ["HF_HUB_ENABLE_HF_TRANSFER"] = "1"
    for pid, (repo, trust) in MODELS.items():
        print(f">>> downloading {pid} {repo}")
        try:
            download_one(pid, repo, trust)
        except Exception as e:
            print(f"[ERROR] {pid}: {e}")
