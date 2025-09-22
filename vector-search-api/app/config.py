from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Optional

class Settings(BaseSettings):
    # Qdrant
    QDRANT_URL: str = "http://localhost:6333"
    DEFAULT_COLLECTION: str = "sample_docs"

    # 모델 화이트리스트: "all" 또는 "backend:name,backend:name"
    ALLOW_MODELS: str = "all"  # "all"이면 models_config.yaml의 모든 모델 허용

    # 보안/CORS
    API_KEY: Optional[str] = None
    CORS_ALLOW_ORIGINS: str = "*"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def allow_models(self) -> List[tuple]:
        # "all"이면 모든 모델 허용
        if self.ALLOW_MODELS.strip().lower() == "all":
            from .embeddings_registry import PRESETS
            return [(spec["backend"], spec["name"]) for spec in PRESETS.values()]

        # 기존 방식: 특정 모델만 허용
        items = []
        for token in self.ALLOW_MODELS.split(","):
            token = token.strip()
            if not token:
                continue
            if ":" not in token:
                continue
            backend, name = token.split(":", 1)
            items.append((backend.strip(), name.strip()))
        return items

settings = Settings()
