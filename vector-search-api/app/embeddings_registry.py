import os
import yaml
from pathlib import Path
from typing import Dict, Any
from loguru import logger

def load_models_config(config_path: str = "models_config.yaml") -> Dict[str, Any]:
    """
    YAML 설정 파일에서 모델 설정을 로드합니다.

    Args:
        config_path: 설정 파일 경로 (기본값: models_config.yaml)

    Returns:
        모델 프리셋 딕셔너리
    """
    config_file = Path(config_path)

    # 설정 파일이 없으면 기본값 반환
    if not config_file.exists():
        logger.warning(f"Models config file not found: {config_path}, using defaults")
        return {
            "bge-m3": {"backend": "st", "name": "./models/bge-m3", "normalize": True, "e5_mode": "auto"}
        }

    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        presets = {}
        models = config.get('models', {})

        for model_id, model_config in models.items():
            # 필수 필드만 추출 (description, dimension 등은 메타데이터로 제외)
            presets[model_id] = {
                "backend": model_config.get("backend", "st"),
                "name": model_config.get("path", f"./models/{model_id}"),
                "normalize": model_config.get("normalize", True),
                "e5_mode": model_config.get("e5_mode", "auto")
            }

        logger.info(f"Loaded {len(presets)} models from {config_path}")
        return presets

    except Exception as e:
        logger.error(f"Failed to load models config: {e}")
        # 에러 시 최소한의 기본값 반환
        return {
            "bge-m3": {"backend": "st", "name": "./models/bge-m3", "normalize": True, "e5_mode": "auto"}
        }

# 환경변수로 설정 파일 경로 지정 가능 (기본값: config/models_config.yaml)
CONFIG_PATH = os.getenv("MODELS_CONFIG_PATH", "config/models_config.yaml")

# 모듈 로드 시 설정 읽기
PRESETS = load_models_config(CONFIG_PATH)

# 설정 파일의 global settings도 로드
def get_global_settings() -> Dict[str, Any]:
    """전역 설정을 가져옵니다."""
    config_file = Path(CONFIG_PATH)
    if config_file.exists():
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                return config.get('settings', {})
        except Exception:
            pass
    return {}

GLOBAL_SETTINGS = get_global_settings()