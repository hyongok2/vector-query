# Vector Search API

벡터 검색 API 서버 - FastAPI 기반의 임베딩 및 벡터 검색 서비스

## 주요 기능

- 다양한 임베딩 모델 지원 (한국어 특화 모델 포함)
- Qdrant 벡터 데이터베이스 통합
- RESTful API 제공
- Docker 컨테이너 지원
- 볼륨 마운트 기반 모델 관리

## 시작하기

### 1. 환경 설정

```bash
# 환경 변수 파일 생성
cp .env.example .env

# Python 가상 환경 생성 및 활성화
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt
```

### 2. 모델 다운로드

```bash
# 모델 다운로드 스크립트 실행
python download/download_models.py
```

### 3. 실행

#### 로컬 실행
```bash
python main.py
```

#### Docker Compose 실행
```bash
docker-compose up -d
```

## 새 모델 추가 가이드

새로운 임베딩 모델을 추가하려면 다음 단계를 따르세요:

### 1. 모델 다운로드

`download/download_models.py` 파일에 새 모델 추가:

```python
# 예시: 새로운 모델 추가
models_to_download = [
    # ... 기존 모델들 ...
    {
        "name": "your-organization/your-model-name",
        "backend": "st",  # 또는 "fastembed"
        "save_path": "./models/your-model"
    }
]
```

다운로드 실행:
```bash
python download/download_models.py
```

### 2. 환경 변수 업데이트

`.env` 파일의 `ALLOW_MODELS`에 새 모델 추가:

```env
# backend:path 형식으로 추가 (콤마로 구분)
ALLOW_MODELS=...,st:./models/your-model
```

### 3. 모델 레지스트리 등록

`app/embeddings_registry.py` 파일의 `PRESETS` 딕셔너리에 추가:

```python
PRESETS = {
    # ... 기존 모델들 ...
    "your-model": {
        "backend": "st",          # "st" 또는 "fastembed"
        "name": "./models/your-model",
        "normalize": True,         # 정규화 여부
        "e5_mode": "auto"         # "auto", "query", 또는 "passage"
    }
}
```

### 4. 모델 설정 옵션

- **backend**:
  - `"st"`: Sentence Transformers 백엔드 (대부분의 Hugging Face 모델)
  - `"fastembed"`: FastEmbed 백엔드 (ONNX 최적화 모델)

- **normalize**:
  - `True`: 벡터 정규화 (코사인 유사도 사용 시)
  - `False`: 원본 벡터 (L2 거리 사용 시)

- **e5_mode**:
  - `"auto"`: 자동 감지
  - `"query"`: 쿼리 임베딩 (검색용)
  - `"passage"`: 문서 임베딩 (인덱싱용)

### 5. 검증

서버 재시작 후 새 모델 확인:

```bash
# 사용 가능한 모델 목록 확인
curl http://localhost:5200/models

# 새 모델로 임베딩 생성
curl -X POST http://localhost:5200/embed \
  -H "Content-Type: application/json" \
  -d '{
    "model": "your-model",
    "texts": ["테스트 텍스트"]
  }'
```

## API 엔드포인트

### 모델 관련

- `GET /models` - 사용 가능한 모델 목록 조회
- `POST /embed` - 텍스트 임베딩 생성

### 벡터 검색

- `POST /search` - 벡터 검색 수행
- `POST /bulk_embed` - 대량 임베딩 생성

### 상태 확인

- `GET /health` - 서버 상태 확인
- `GET /stats` - 통계 정보 조회

## Docker 볼륨 구조

```
./models/           # 로컬 모델 디렉토리 (읽기 전용 마운트)
├── bge-m3/
├── mE5-base/
├── ko-sbert/
└── ...

/app/models/        # 컨테이너 내부 경로
/app/.cache/        # Hugging Face 캐시 (영구 볼륨)
```

## 주의사항

1. **모델 크기**: 각 모델은 수백 MB ~ 수 GB의 용량을 차지합니다
2. **메모리 사용**: 여러 모델 동시 로드 시 메모리 사용량이 증가합니다
3. **초기 로딩**: 첫 요청 시 모델 로딩으로 지연이 발생할 수 있습니다
4. **볼륨 권한**: Docker 사용 시 모델 디렉토리 읽기 권한 확인

## 트러블슈팅

### 모델을 찾을 수 없을 때
- 모델 경로가 올바른지 확인
- `.env` 파일의 `ALLOW_MODELS`에 등록되었는지 확인
- Docker 사용 시 볼륨 마운트가 정상적인지 확인

### 메모리 부족
- `DEVICE=cpu` 설정으로 GPU 메모리 사용 비활성화
- 동시 로드 모델 수 제한
- 더 작은 모델 사용 고려

### 성능 최적화
- FastEmbed 백엔드 사용 (ONNX 최적화)
- GPU 사용 (`DEVICE=cuda`)
- 배치 처리 활용 (`/bulk_embed`)

## 라이선스

[라이선스 정보]