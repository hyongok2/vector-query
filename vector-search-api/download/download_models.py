# download_models.py  (외부망 PC에서 실행)
from sentence_transformers import SentenceTransformer

MODELS = {
    "mE5-base": "intfloat/multilingual-e5-base",
    "mE5-large": "intfloat/multilingual-e5-large",
    "paraphrase-ml": "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
    "ko-sbert": "snunlp/KR-SBERT-V40K-klueNLI-augSTS",
    "ko-sroberta": "jhgan/ko-sroberta-multitask",
    #"gte-multilingual": "thenlper/gte-multilingual-base",
    #"jina-v2-base": "jinaai/jina-embeddings-v2-base-multilingual",
    #"nomic-embed": "nomic-ai/nomic-embed-text-v1",
    "bge-m3": "BAAI/bge-m3",
    "mE5-small": "intfloat/multilingual-e5-small",
}

for k, repo in MODELS.items():
    print(">>> downloading", k, repo)
    try:
        m = SentenceTransformer(repo)
        m.save(f"../models/{k}")
    except Exception as e:
        print("skip ST load error:", e)
