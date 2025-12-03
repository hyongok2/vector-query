py -3.11 -m venv .venv311

 . .\.venv311\Scripts\Activate.ps1

  python -m pip install --upgrade pip

  pip install fastapi uvicorn[standard] pydantic pydantic-settings python-dotenv loguru qdrant-client fastembed numpy orjson
  

  pip install sentence-transformers

  pip install torch --index-url https://download.pytorch.org/whl/cpu

  모델 다운로드는 download_models.py  / 실행

  gpu의 경우는 torch를 다른버전을 받아야 하고, 그 전에 기존 cpu 버전은 삭제해야 함.