"""Embedding model management with clean interface"""
import os
from typing import Dict, List, Optional, Tuple
try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False
from sentence_transformers import SentenceTransformer
import numpy as np
from abc import ABC, abstractmethod


class EmbeddingModelInterface(ABC):
    """Abstract interface for embedding models"""

    @abstractmethod
    def encode(self, texts: List[str]) -> np.ndarray:
        """Encode texts to embeddings"""
        pass

    @abstractmethod
    def get_dimension(self) -> int:
        """Get embedding dimension"""
        pass

    @abstractmethod
    def get_model_name(self) -> str:
        """Get model name"""
        pass


class SentenceTransformerModel(EmbeddingModelInterface):
    """Sentence transformer implementation"""

    def __init__(self, model_name: str, model_path: Optional[str] = None):
        self.model_name = model_name
        self._model = self._load_model(model_path)
        self._dimension = self._detect_dimension()

    def _load_model(self, model_path: Optional[str]) -> SentenceTransformer:
        """Load model from local path or HuggingFace"""
        if model_path and os.path.exists(model_path):
            return SentenceTransformer(model_path)

        # Fallback to HuggingFace
        hf_model_map = {
            'bge-m3': 'BAAI/bge-m3',
            'mE5-small': 'intfloat/multilingual-e5-small',
            'mE5-base': 'intfloat/multilingual-e5-base',
            'mE5-large': 'intfloat/multilingual-e5-large',
            'paraphrase-ml': 'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2'
        }
        hf_model = hf_model_map.get(self.model_name, self.model_name)
        return SentenceTransformer(hf_model)

    def _detect_dimension(self) -> int:
        """Detect embedding dimension"""
        test_embedding = self._model.encode(["test"], convert_to_numpy=True)
        return test_embedding.shape[1]

    def encode(self, texts: List[str]) -> np.ndarray:
        """Encode texts to normalized embeddings"""
        embeddings = self._model.encode(texts, convert_to_numpy=True, show_progress_bar=False)
        return self._l2_normalize(embeddings)

    def _l2_normalize(self, vectors: np.ndarray) -> np.ndarray:
        """L2 normalize vectors for cosine similarity"""
        norms = np.linalg.norm(vectors, axis=1, keepdims=True) + 1e-12
        return vectors / norms

    def get_dimension(self) -> int:
        return self._dimension

    def get_model_name(self) -> str:
        return self.model_name


class ModelConfig:
    """Model configuration management"""

    def __init__(self, config_path: str = "models_config.yaml"):
        self.config_path = config_path
        self._config = self._load_config()

    def _load_config(self) -> Dict:
        """Load model configuration from YAML"""
        try:
            if HAS_YAML and os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    return yaml.safe_load(f)
        except Exception:
            pass

        # Default fallback config
        return {
            'models': {
                'bge-m3': {
                    'path': './models/bge-m3',
                    'dimension': 1024,
                    'description': 'BAAI BGE-M3 (다국어, 고성능)'
                }
            },
            'default_model': 'bge-m3'
        }

    def get_available_models(self) -> List[str]:
        """Get list of available model names"""
        return list(self._config.get('models', {}).keys())

    def get_model_info(self, model_name: str) -> Optional[Dict]:
        """Get model information"""
        return self._config.get('models', {}).get(model_name)

    def get_default_model(self) -> str:
        """Get default model name"""
        return self._config.get('default_model', 'bge-m3')

    def get_model_path(self, model_name: str) -> Optional[str]:
        """Get model local path"""
        model_info = self.get_model_info(model_name)
        return model_info.get('path') if model_info else None

    def get_model_dimension(self, model_name: str) -> Optional[int]:
        """Get model dimension"""
        model_info = self.get_model_info(model_name)
        return model_info.get('dimension') if model_info else None


class EmbeddingModelFactory:
    """Factory for creating embedding models"""

    def __init__(self, config: ModelConfig):
        self.config = config

    def create_model(self, model_name: str) -> EmbeddingModelInterface:
        """Create embedding model instance"""
        model_path = self.config.get_model_path(model_name)
        return SentenceTransformerModel(model_name, model_path)

    def get_available_models(self) -> List[Tuple[str, str]]:
        """Get available models with descriptions"""
        models = []
        for name in self.config.get_available_models():
            info = self.config.get_model_info(name)
            description = info.get('description', name) if info else name
            models.append((name, description))
        return models