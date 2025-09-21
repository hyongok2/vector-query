from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Optional

class Settings(BaseSettings):
    # Qdrant
    QDRANT_URL: str = "http://localhost:6333"
    DEFAULT_COLLECTION: str = "docs_2025"

    # 모델 화이트리스트: "backend:name,backend:name"
    ALLOW_MODELS: str = "fastembed:./models/bge-m3"

    # 보안/CORS
    API_KEY: Optional[str] = None
    CORS_ALLOW_ORIGINS: str = "*"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def allow_models(self) -> List[tuple]:
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
