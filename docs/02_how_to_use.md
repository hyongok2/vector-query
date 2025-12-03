# Vector Search API 사용 가이드

이 문서는 Vector Search API의 설치, 설정, 실행 및 사용 방법을 설명합니다.

## 목차

1. [시스템 요구사항](#1-시스템-요구사항)
2. [설치 및 설정](#2-설치-및-설정)
3. [서버 실행](#3-서버-실행)
4. [API 사용법](#4-api-사용법)
5. [예제 코드](#5-예제-코드)
6. [문제 해결](#6-문제-해결)

---

## 1. 시스템 요구사항

### 하드웨어 요구사항

최소 사양:
- CPU: 4코어 이상
- RAM: 8GB (단일 모델 로드 시)
- 디스크: 20GB 이상 여유 공간

권장 사양:
- CPU: 8코어 이상
- RAM: 16GB (다중 모델 로드 시)
- GPU: CUDA 지원 GPU (선택사항, 성능 향상)
- 디스크: 50GB 이상 (모든 모델 설치 시)

### 소프트웨어 요구사항

- Python: 3.9 이상
- Docker: 20.10 이상 (Docker 사용 시)
- Docker Compose: 1.29 이상 (Docker Compose 사용 시)
- Qdrant: 벡터 데이터베이스 (별도 실행 필요)

---

## 2. 설치 및 설정

### 2.1 프로젝트 클론

```bash
git clone <repository-url>
cd vector-db/vector-search-api
```

### 2.2 Python 가상환경 설정

```bash
# 가상환경 생성
python -m venv venv

# 가상환경 활성화
# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 2.3 의존성 설치

```bash
pip install -r requirements.txt
```

주요 의존성:
- fastapi==0.117.1 - 웹 API 프레임워크
- uvicorn==0.36.0 - ASGI 서버
- qdrant-client==1.15.1 - Qdrant 클라이언트
- sentence-transformers==5.1.0 - 임베딩 모델 라이브러리
- torch==2.8.0 - 딥러닝 프레임워크
- pydantic==2.11.9 - 데이터 검증

### 2.4 환경 변수 설정

.env 파일을 생성하고 설정합니다:

```bash
# Qdrant 연결 설정
QDRANT_URL=http://localhost:6333
DEFAULT_COLLECTION=docs_2025

# 모델 허용 목록
ALLOW_MODELS=all

# API 보안 설정 (선택사항)
API_KEY=

# CORS 설정
CORS_ALLOW_ORIGINS=*

# 디바이스 설정
DEVICE=auto

# CPU 스레드 수
TORCH_NUM_THREADS=4
```

### 2.5 모델 설정

config/models_config.yaml 파일에서 사용할 모델을 설정합니다.

### 2.6 모델 다운로드

```bash
cd download
python download_models.py
```

다운로드되는 모델:
- bge-m3: 1024차원, 다국어
- mE5-small: 384차원, 다국어
- mE5-base: 768차원, 다국어
- mE5-large: 1024차원, 다국어
- paraphrase-ml: 384차원, 다국어
- ko-sbert: 768차원, 한국어
- ko-sroberta: 768차원, 한국어
- ko-simcse: 768차원, 한국어
- kure-v1: 1024차원, 한국어 (SOTA)
- bge-m3-ko: 1024차원, 한국어 fine-tuned
- ko-e5: 1024차원, 한국어

---

## 3. 서버 실행

### 3.1 로컬 실행

```bash
python main.py
```

서버 정보:
- Host: 0.0.0.0
- Port: 5200
- API Docs: http://localhost:5200/docs
- OpenAPI JSON: http://localhost:5200/openapi.json

### 3.2 Docker Compose 실행

```bash
docker-compose up -d
docker-compose logs -f
docker-compose down
```

### 3.3 서버 상태 확인

```bash
curl http://localhost:5200/health
```

---

## 4. API 사용법

### 4.1 API 엔드포인트

| 엔드포인트 | 메소드 | 설명 | 인증 필요 |
|-----------|--------|------|----------|
| /health | GET | 서버 상태 확인 | No |
| /models | GET | 사용 가능한 모델 목록 조회 | No |
| /search | POST | 벡터 검색 수행 | Yes (API_KEY 설정 시) |

### 4.2 모델 목록 조회

```bash
curl http://localhost:5200/models
```

### 4.3 벡터 검색 (기본)

```bash
curl -X POST http://localhost:5200/search \
  -H "Content-Type: application/json" \
  -d '{
    "text": "인공지능 기술의 발전",
    "top_k": 5,
    "preset_id": "bge-m3",
    "qdrant": {
      "url": "http://localhost:6333",
      "collection": "docs_2025"
    }
  }'
```

### 4.4 벡터 검색 (필터 사용)

Qdrant 필터를 사용하여 조건부 검색을 수행할 수 있습니다.

필터 연산자:
- must: AND 조건 (모두 만족)
- must_not: NOT 조건 (제외)
- should: OR 조건 (하나 이상 만족)
- match: 정확한 값 일치
- range: 범위 조건 (gte, gt, lte, lt)

### 4.5 API 인증

```bash
curl -X POST http://localhost:5200/search \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-secret-key" \
  -d '{ ... }'
```

### 4.6 요청 파라미터

SearchRequest:
- text: 검색할 텍스트 쿼리 (필수)
- top_k: 반환할 최대 결과 수 (기본값: 5, 범위: 1-100)
- threshold: 최소 유사도 점수 (기본값: 0.0, 범위: 0.0-1.0)
- with_payload: 메타데이터 포함 여부 (기본값: true)
- preset_id: 모델 프리셋 ID (선택)
- model: 모델 상세 설정 (선택)
- qdrant: Qdrant 연결 설정 (필수)

---

## 5. 예제 코드

### 5.1 Python 클라이언트

```python
import requests

def search_vectors(query_text, collection_name, top_k=5):
    url = "http://localhost:5200/search"
    
    payload = {
        "text": query_text,
        "top_k": top_k,
        "threshold": 0.5,
        "preset_id": "bge-m3",
        "qdrant": {
            "url": "http://localhost:6333",
            "collection": collection_name
        }
    }
    
    response = requests.post(url, json=payload)
    response.raise_for_status()
    return response.json()

# 사용 예제
results = search_vectors(
    query_text="머신러닝 알고리즘",
    collection_name="docs_2025",
    top_k=10
)

print(f"검색 시간: {results['took_ms']}ms")
for hit in results['hits']:
    print(f"[{hit['score']:.3f}] {hit['id']}")
```

### 5.2 JavaScript 클라이언트

```javascript
async function searchVectors(queryText, collectionName, topK = 5) {
  const response = await fetch('http://localhost:5200/search', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      text: queryText,
      top_k: topK,
      preset_id: 'bge-m3',
      qdrant: {
        url: 'http://localhost:6333',
        collection: collectionName
      }
    })
  });
  
  return response.json();
}

// 사용 예제
const results = await searchVectors('자연어 처리 기술', 'docs_2025', 5);
console.log(`검색 시간: ${results.took_ms}ms`);
```

---

## 6. 문제 해결

### 6.1 일반적인 오류

오류: "Model not allowed"
- 원인: 요청한 모델이 허용 목록에 없음
- 해결: .env 파일에서 ALLOW_MODELS=all 설정

오류: "Qdrant connection failed"
- 원인: Qdrant 서버에 연결할 수 없음
- 해결: curl http://localhost:6333/health로 Qdrant 상태 확인

오류: "Collection not found"
- 원인: 지정한 컬렉션이 Qdrant에 없음
- 해결: curl http://localhost:6333/collections로 컬렉션 목록 확인

오류: "Out of memory"
- 원인: 메모리 부족
- 해결: 작은 모델 사용 (mE5-small) 또는 max_cached_models 줄이기

### 6.2 성능 최적화

GPU 사용:
```bash
DEVICE=cuda
```

모델 캐싱:
```yaml
settings:
  cache_models: true
  max_cached_models: 5
```

### 6.3 API 테스트

Swagger UI: http://localhost:5200/docs
ReDoc: http://localhost:5200/redoc

---

## 다음 단계

1. 설정 방법 (03_setting_configuration.md)
2. API 상세 (04_api_detail.md)
3. 아키텍처 (05_architecture.md)
4. 배포 가이드 (06_deployment.md)

---

## 참고 자료

- FastAPI: https://fastapi.tiangolo.com/
- Qdrant: https://qdrant.tech/documentation/
- Sentence Transformers: https://www.sbert.net/
