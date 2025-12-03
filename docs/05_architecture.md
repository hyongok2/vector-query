# Vector Search API 시스템 아키텍처

이 문서는 Vector Search API의 시스템 아키텍처, 구성 요소, 데이터 흐름, 설계 패턴을 설명합니다.

## 목차

1. [시스템 개요](#1-시스템-개요)
2. [아키텍처 다이어그램](#2-아키텍처-다이어그램)
3. [핵심 구성 요소](#3-핵심-구성-요소)
4. [데이터 흐름](#4-데이터-흐름)
5. [기술 스택](#5-기술-스택)
6. [설계 패턴](#6-설계-패턴)
7. [확장성 전략](#7-확장성-전략)
8. [보안 아키텍처](#8-보안-아키텍처)

---

## 1. 시스템 개요

### 1.1 아키텍처 스타일

Vector Search API는 다음과 같은 아키텍처 스타일을 채택합니다:

- **RESTful API**: HTTP 기반의 상태 비저장 API
- **레이어드 아키텍처**: 명확한 계층 분리
- **마이크로서비스 지향**: 독립적인 배포 및 확장 가능
- **이벤트 기반**: 비동기 처리 및 확장성

### 1.2 핵심 설계 원칙

#### SOLID 원칙 적용

- **Single Responsibility**: 각 모듈은 단일 책임
- **Open/Closed**: 확장에 열려있고 수정에 닫혀있음
- **Dependency Inversion**: 추상화에 의존

#### 추가 원칙

- **Separation of Concerns**: API, 비즈니스 로직, 데이터 액세스 분리
- **DRY (Don't Repeat Yourself)**: 코드 중복 최소화
- **KISS (Keep It Simple)**: 단순성 유지

### 1.3 시스템 특징

- **고성능**: GPU/CPU 자동 감지 및 최적화
- **확장성**: 수평 확장 가능한 설계
- **유연성**: 다양한 임베딩 모델 지원
- **안정성**: 견고한 에러 핸들링
- **모니터링**: 상태 확인 및 로깅

---

## 2. 아키텍처 다이어그램

### 2.1 시스템 전체 구조

```
┌─────────────────────────────────────────────────────────────┐
│                         Client Layer                         │
│  (Web Browser, Mobile App, Backend Service, CLI Tools)      │
└──────────────────────┬──────────────────────────────────────┘
                       │ HTTP/HTTPS
                       │ JSON Request/Response
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                      API Gateway Layer                       │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  FastAPI Application (main.py)                       │   │
│  │  - CORS Middleware                                   │   │
│  │  - API Key Authentication                            │   │
│  │  - Request Validation                                │   │
│  │  - Error Handling                                    │   │
│  └──────────────────────────────────────────────────────┘   │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                     API Endpoint Layer                       │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  app/api.py                                          │   │
│  │  - GET  /health    → Health Check                   │   │
│  │  - GET  /models    → Model List                     │   │
│  │  - POST /search    → Vector Search                  │   │
│  └──────────────────────────────────────────────────────┘   │
└──────────────────────┬──────────────────────────────────────┘
                       │
       ┌───────────────┴───────────────┐
       ▼                               ▼
┌─────────────────┐          ┌──────────────────┐
│  Model Registry │          │  Embedding Layer │
│   (config.py)   │          │  (embeddings.py) │
│                 │          │                  │
│ - Load config   │◄─────────┤ - embed_query()  │
│ - Validate      │          │ - embed_many()   │
│ - Preset lookup │          │ - Model caching  │
└─────────────────┘          └────────┬─────────┘
                                      │
                      ┌───────────────┴───────────────┐
                      ▼                               ▼
              ┌──────────────┐              ┌──────────────┐
              │ Sentence     │              │    Torch     │
              │ Transformers │              │   Backend    │
              │              │              │              │
              │ - Model load │              │ - GPU/CPU    │
              │ - Encoding   │              │ - Threading  │
              └──────────────┘              └──────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                   Vector Database Layer                      │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Qdrant Client (qdrant_service.py)                   │   │
│  │  - Collection management                             │   │
│  │  - Vector search                                     │   │
│  │  - Filtering                                         │   │
│  │  - Metadata handling                                 │   │
│  └──────────────────────────────────────────────────────┘   │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
              ┌──────────────┐
              │   Qdrant     │
              │   Server     │
              │  (Port 6333) │
              │              │
              │ - Collections│
              │ - Indexes    │
              │ - Storage    │
              └──────────────┘
```

### 2.2 컴포넌트 간 통신

```
Request Flow (검색 요청):
───────────────────────

Client
  │
  │ POST /search
  │ {text, top_k, preset_id, qdrant: {...}}
  ▼
FastAPI App (main.py)
  │
  │ Validate API Key
  │ Validate Request Body
  ▼
API Handler (api.py)
  │
  ├──► Config Registry
  │    └──► Load preset_id → ModelSpec
  │
  ├──► Embedding Layer
  │    │ embed_query(text, spec)
  │    │
  │    ├──► Load/Cache Model
  │    │    └──► SentenceTransformer
  │    │
  │    └──► Generate Vector
  │         └──► [float, float, ...]
  │
  └──► Qdrant Service
       │ search(vector, collection, filter, top_k)
       │
       └──► Qdrant Server
            │ Find similar vectors
            │ Apply filters
            │ Return results
            ▼
Response
  {
    took_ms: 245,
    model: {...},
    collection: "...",
    hits: [...]
  }
```

---

## 3. 핵심 구성 요소

### 3.1 API 계층 (API Layer)

#### main.py
```python
역할: 애플리케이션 엔트리 포인트
책임:
  - Uvicorn ASGI 서버 실행
  - 호스트/포트 설정 (0.0.0.0:5200)
  - 로깅 설정

기술:
  - Uvicorn: ASGI 서버
  - FastAPI: 웹 프레임워크
```

#### app/api.py
```python
역할: API 엔드포인트 정의 및 요청 처리
책임:
  - 3개 엔드포인트 구현 (health, models, search)
  - 요청 검증 (Pydantic)
  - API 키 인증
  - 에러 핸들링
  - CORS 설정

주요 함수:
  - health() → 서버 상태 확인
  - list_models() → 사용 가능 모델 목록
  - search_vectors() → 벡터 검색 수행

의존성:
  - app/models.py (데이터 모델)
  - app/config.py (설정 관리)
  - app/embeddings.py (임베딩 생성)
  - app/qdrant_service.py (벡터 검색)
```

### 3.2 모델 계층 (Model Layer)

#### app/models.py
```python
역할: 데이터 모델 정의
책임:
  - 요청/응답 스키마 정의
  - 데이터 검증
  - 타입 안정성

주요 모델:
  - SearchRequest: 검색 요청 (text, top_k, preset_id, qdrant)
  - SearchResponse: 검색 응답 (took_ms, model, hits)
  - Hit: 검색 결과 (id, score, payload)
  - ModelSpec: 모델 사양 (backend, name, normalize, e5_mode)
  - QdrantCfg: Qdrant 설정 (url, collection, query_filter)

기술:
  - Pydantic: 데이터 검증
  - Type Hints: 타입 안정성
```

### 3.3 설정 관리 계층 (Configuration Layer)

#### app/config.py
```python
역할: 설정 로드 및 모델 레지스트리 관리
책임:
  - models_config.yaml 로드
  - 프리셋 ID 조회
  - 모델 허용 목록 검증
  - 환경 변수 처리

주요 함수:
  - load_models_config() → YAML 로드
  - get_model_by_preset(preset_id) → ModelSpec 반환
  - is_model_allowed(spec) → 허용 여부 확인

환경 변수:
  - ALLOW_MODELS: 모델 허용 목록
  - QDRANT_URL: Qdrant 서버 URL
  - DEFAULT_COLLECTION: 기본 컬렉션
```

#### config/models_config.yaml
```yaml
역할: 모델 프리셋 정의
구조:
  models:
    - preset_id: string
      backend: "st"
      name: string (모델 경로)
      normalize: boolean
      e5_mode: "auto" | "query" | "passage"

  settings:
    default_model: string
    trust_remote_code: boolean
    cache_models: boolean
    max_cached_models: integer
    batch_size: integer
    max_sequence_length: integer

지원 모델:
  - bge-m3 (1024차원, 다국어)
  - mE5-small/base/large (384/768/1024차원)
  - ko-sbert, ko-sroberta, ko-simcse (한국어)
  - kure-v1, bge-m3-ko, ko-e5 (한국어 SOTA)
```

### 3.4 임베딩 계층 (Embedding Layer)

#### app/embeddings.py
```python
역할: 텍스트를 벡터로 변환
책임:
  - 모델 로드 및 캐싱
  - 텍스트 → 벡터 변환
  - GPU/CPU 자동 감지
  - E5 모델 프롬프트 처리
  - 벡터 정규화

주요 함수:
  - embed_query(text, spec) → List[float]
  - embed_many(texts, spec, batch_size) → List[List[float]]
  - _load_st(name) → SentenceTransformer 모델
  - _pick_device() → "cuda" | "mps" | "cpu"
  - _e5_prefix(text, mode) → E5 프롬프트 처리
  - _norm(vec, enable) → 벡터 정규화

모델 캐싱:
  - _ST_CACHE: {(name, device, trust): model}
  - 메모리 효율적인 모델 재사용

최적화:
  - DEVICE 환경 변수 (auto, cuda, cpu, mps)
  - TORCH_NUM_THREADS 환경 변수
  - 배치 처리 지원
```

### 3.5 벡터 검색 계층 (Vector Search Layer)

#### app/qdrant_service.py
```python
역할: Qdrant와의 통신 및 벡터 검색
책임:
  - Qdrant 클라이언트 관리
  - 벡터 검색 수행
  - 필터 조건 처리
  - 결과 변환

주요 함수:
  - search_vectors(vector, cfg, top_k, threshold, with_payload)
    → List[Hit]

필터 처리:
  - must: AND 조건
  - must_not: NOT 조건
  - should: OR 조건
  - match: 값 일치
  - range: 범위 조건

에러 핸들링:
  - 연결 실패
  - 컬렉션 없음
  - 쿼리 실행 실패
```

---

## 4. 데이터 흐름

### 4.1 검색 요청 처리 흐름

```
1. 클라이언트 요청
   ├─ POST /search
   └─ Body: {text, top_k, preset_id, qdrant}

2. API Gateway (FastAPI)
   ├─ CORS 검증
   ├─ API 키 검증 (선택)
   └─ Request Body 검증 (Pydantic)

3. API Handler (api.py)
   ├─ 시작 시간 기록
   └─ search_vectors() 호출

4. 모델 조회 (config.py)
   ├─ preset_id로 ModelSpec 조회
   ├─ 모델 허용 목록 검증
   └─ ModelSpec 반환

5. 임베딩 생성 (embeddings.py)
   ├─ 모델 로드/캐시 확인
   │  ├─ 캐시 존재 → 재사용
   │  └─ 캐시 없음 → SentenceTransformer 로드
   ├─ E5 프롬프트 처리 (필요 시)
   ├─ 텍스트 인코딩 → 벡터
   └─ 벡터 정규화 (필요 시)

6. 벡터 검색 (qdrant_service.py)
   ├─ Qdrant 클라이언트 생성
   ├─ 필터 조건 변환
   ├─ search() 호출
   │  ├─ collection 지정
   │  ├─ vector 전달
   │  ├─ filter 적용
   │  ├─ limit (top_k)
   │  └─ score_threshold
   └─ 결과 변환 → List[Hit]

7. 응답 생성
   ├─ 소요 시간 계산 (took_ms)
   ├─ SearchResponse 생성
   │  ├─ model 정보
   │  ├─ collection 이름
   │  ├─ total_candidates
   │  └─ hits
   └─ JSON 응답 반환

8. 클라이언트 수신
   └─ {took_ms, model, collection, hits}
```

### 4.2 모델 목록 조회 흐름

```
1. GET /models 요청

2. config.py
   ├─ models_config.yaml 로드
   ├─ 허용 모델 필터링
   └─ 모델 목록 반환

3. JSON 응답
   └─ {models: [...]}
```

### 4.3 헬스 체크 흐름

```
1. GET /health 요청

2. api.py
   ├─ 서버 상태 확인
   └─ Qdrant URL 반환

3. JSON 응답
   └─ {ok: true, qdrant_url: "..."}
```

---

## 5. 기술 스택

### 5.1 백엔드 프레임워크

#### FastAPI (v0.117.1)
```
역할: 웹 API 프레임워크
특징:
  - 고성능 (Starlette 기반)
  - 자동 API 문서 (Swagger, ReDoc)
  - 타입 힌트 기반 검증
  - 비동기 지원

사용:
  - 엔드포인트 정의
  - 요청/응답 처리
  - 미들웨어 (CORS, 인증)
  - 에러 핸들링
```

#### Uvicorn (v0.36.0)
```
역할: ASGI 서버
특징:
  - 경량 고성능
  - HTTP/1.1, WebSocket 지원
  - 비동기 I/O

사용:
  - FastAPI 앱 실행
  - 0.0.0.0:5200 바인딩
```

### 5.2 데이터 검증

#### Pydantic (v2.11.9)
```
역할: 데이터 검증 및 직렬화
특징:
  - 타입 기반 검증
  - 자동 변환
  - JSON 스키마 생성

사용:
  - SearchRequest 검증
  - SearchResponse 생성
  - ModelSpec, QdrantCfg 정의
```

### 5.3 벡터 데이터베이스

#### Qdrant Client (v1.15.1)
```
역할: Qdrant 벡터 DB 클라이언트
특징:
  - 고성능 벡터 검색
  - 필터링 지원
  - 메타데이터 저장

사용:
  - 벡터 검색
  - 컬렉션 관리
  - 필터 쿼리
```

### 5.4 임베딩 모델

#### Sentence Transformers (v5.1.0)
```
역할: 텍스트 임베딩 라이브러리
특징:
  - 사전 학습 모델
  - 배치 처리
  - GPU/CPU 지원

사용:
  - 모델 로드
  - 텍스트 인코딩
  - 벡터 생성
```

#### PyTorch (v2.8.0)
```
역할: 딥러닝 프레임워크
특징:
  - GPU 가속
  - 자동 미분
  - 모델 학습/추론

사용:
  - 모델 백엔드
  - 디바이스 관리 (CUDA, MPS)
  - 스레드 최적화
```

### 5.5 환경 및 배포

#### Docker
```
역할: 컨테이너화
특징:
  - 환경 일관성
  - 의존성 격리
  - 쉬운 배포

사용:
  - Dockerfile (멀티스테이지 빌드)
  - docker-compose.yml
  - 볼륨 마운트
```

#### Python (3.9+)
```
역할: 프로그래밍 언어
특징:
  - 타입 힌트
  - 비동기 지원
  - 풍부한 생태계

사용:
  - 전체 애플리케이션
```

---

## 6. 설계 패턴

### 6.1 레이어드 아키텍처 (Layered Architecture)

```
계층 구조:
──────────

┌─────────────────────────┐
│   Presentation Layer    │ ← FastAPI, API Endpoints
├─────────────────────────┤
│   Application Layer     │ ← Business Logic, Orchestration
├─────────────────────────┤
│   Domain Layer          │ ← Models, Validation
├─────────────────────────┤
│   Infrastructure Layer  │ ← Embeddings, Qdrant, Config
└─────────────────────────┘

장점:
  - 명확한 책임 분리
  - 유지보수 용이
  - 테스트 가능성
```

### 6.2 레지스트리 패턴 (Registry Pattern)

```python
# app/config.py
class ModelsRegistry:
    def __init__(self):
        self._models = load_models_config()

    def get_by_preset(self, preset_id: str) -> ModelSpec:
        # 프리셋 ID로 모델 조회
        ...

용도:
  - 중앙화된 모델 관리
  - 런타임 모델 조회
  - 설정 변경 용이

장점:
  - 단일 진실 공급원 (Single Source of Truth)
  - 의존성 역전
  - 확장성
```

### 6.3 캐싱 패턴 (Caching Pattern)

```python
# app/embeddings.py
_ST_CACHE = {}  # key=(name, device, trust) -> model

def _load_st(name: str):
    key = (name_resolved, device, trust)
    if key in _ST_CACHE:
        return _ST_CACHE[key], device

    model = SentenceTransformer(name_resolved, device=device)
    _ST_CACHE[key] = model
    return model, device

장점:
  - 모델 재로드 방지
  - 메모리 효율
  - 응답 시간 단축
```

### 6.4 팩토리 패턴 (Factory Pattern)

```python
# 모델 생성 추상화
def _load_st(name: str):
    # 환경에 따라 적절한 디바이스 선택
    device = _pick_device()

    # 모델 생성
    return SentenceTransformer(name, device=device)

장점:
  - 객체 생성 로직 캡슐화
  - 디바이스 자동 감지
  - 확장성
```

### 6.5 의존성 주입 (Dependency Injection)

```python
# FastAPI의 의존성 주입
def verify_api_key(x_api_key: str = Header(None)):
    if api_key_required and x_api_key != required_key:
        raise HTTPException(401, "Invalid API key")

@app.post("/search")
async def search_vectors(
    req: SearchRequest,
    _: None = Depends(verify_api_key)  # DI
):
    ...

장점:
  - 테스트 용이
  - 느슨한 결합
  - 재사용성
```

### 6.6 전략 패턴 (Strategy Pattern)

```python
# 백엔드 전략 (현재는 ST만 지원하지만 확장 가능)
def embed_query(text: str, spec: ModelSpec):
    if spec.backend == "st":
        return _embed_with_st(text, spec)
    # 향후 다른 백엔드 추가 가능
    # elif spec.backend == "openai":
    #     return _embed_with_openai(text, spec)

장점:
  - 알고리즘 캡슐화
  - 런타임 전략 선택
  - 확장성
```

---

## 7. 확장성 전략

### 7.1 수평 확장 (Horizontal Scaling)

#### 무상태 설계 (Stateless Design)
```
특징:
  - 서버 간 상태 공유 없음
  - 세션 데이터 외부 저장
  - 모든 요청 독립적 처리

장점:
  - 로드 밸런서로 트래픽 분산
  - 인스턴스 추가/제거 용이
  - 장애 격리

구현:
  - API 키는 환경 변수로 관리
  - 모델 캐시는 로컬 (인스턴스별)
  - Qdrant는 외부 서비스
```

#### 로드 밸런싱
```
┌──────────┐
│  Client  │
└────┬─────┘
     │
     ▼
┌─────────────┐
│Load Balancer│ (Nginx, HAProxy, AWS ELB)
└─────┬───────┘
      │
      ├──────────┬──────────┬──────────┐
      ▼          ▼          ▼          ▼
   ┌────┐    ┌────┐    ┌────┐    ┌────┐
   │API1│    │API2│    │API3│    │API4│
   └────┘    └────┘    └────┘    └────┘

전략:
  - Round Robin
  - Least Connections
  - IP Hash
```

### 7.2 수직 확장 (Vertical Scaling)

#### GPU 활용
```yaml
device: cuda  # GPU 사용
torch_num_threads: 16  # CPU 코어 활용

성능 향상:
  - 임베딩 생성 10-50배 빠름
  - 배치 처리 효율 증가
  - 대규모 모델 지원
```

#### 메모리 최적화
```yaml
settings:
  cache_models: true
  max_cached_models: 3  # 메모리 제한
  batch_size: 64  # 배치 크기 조정

전략:
  - 모델 캐시 크기 제한
  - LRU 캐시 정책
  - 메모리 모니터링
```

### 7.3 캐싱 전략

#### 모델 캐싱
```python
# 앱 레벨 캐싱
_ST_CACHE = {}  # 모델 재사용

장점:
  - 모델 로드 시간 제거
  - 메모리 효율
```

#### 결과 캐싱 (향후 구현)
```python
# Redis/Memcached
cache_key = hash(text + preset_id)
if cached := redis.get(cache_key):
    return cached

vector = embed_query(text, spec)
redis.set(cache_key, vector, ttl=3600)
```

### 7.4 비동기 처리

#### 현재 구조
```python
# FastAPI는 비동기 지원
@app.post("/search")
async def search_vectors(req: SearchRequest):
    # 동기 함수 호출 (임베딩)
    vector = embed_query(req.text, spec)

    # 동기 함수 호출 (검색)
    hits = qdrant_search(vector, ...)
```

#### 향후 개선
```python
# 완전한 비동기 파이프라인
@app.post("/search")
async def search_vectors(req: SearchRequest):
    # 비동기 임베딩
    vector = await async_embed_query(req.text, spec)

    # 비동기 검색
    hits = await async_qdrant_search(vector, ...)

장점:
  - I/O 대기 시간 활용
  - 동시 처리 증가
  - 리소스 효율
```

### 7.5 마이크로서비스 분리 (향후)

```
현재 모놀리스:
┌──────────────────────┐
│  Vector Search API   │
│  - Embedding         │
│  - Search            │
│  - Config            │
└──────────────────────┘

향후 분리:
┌──────────────┐   ┌──────────────┐   ┌──────────────┐
│  API Gateway │──▶│  Embedding   │   │   Search     │
│              │   │   Service    │──▶│   Service    │
└──────────────┘   └──────────────┘   └──────────────┘

장점:
  - 독립적 확장
  - 기술 스택 다양화
  - 장애 격리
```

---

## 8. 보안 아키텍처

### 8.1 인증 및 권한

#### API 키 인증
```python
# app/api.py
def verify_api_key(x_api_key: str = Header(None)):
    if API_KEY and x_api_key != API_KEY:
        raise HTTPException(401, "Invalid API key")

특징:
  - 선택적 활성화 (API_KEY 환경 변수)
  - Header 기반 (X-API-Key)
  - 모든 /search 요청에 적용

보안 강화:
  - HTTPS 필수
  - 키 로테이션
  - 키 저장소 (환경 변수, Secrets Manager)
```

#### CORS 설정
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,  # 허용 도메인
    allow_methods=["*"],
    allow_headers=["*"]
)

목적:
  - 크로스 오리진 요청 제어
  - 허용 도메인 제한
```

### 8.2 입력 검증

#### Pydantic 검증
```python
class SearchRequest(BaseModel):
    text: str  # 필수
    top_k: int = Field(5, ge=1, le=100)  # 1-100 범위
    threshold: float = Field(0.0, ge=0.0, le=1.0)  # 0.0-1.0
    preset_id: Optional[str] = None

보호:
  - SQL Injection 방지
  - 타입 안정성
  - 범위 검증
```

#### 모델 허용 목록
```python
# config.py
ALLOW_MODELS = os.getenv("ALLOW_MODELS", "all")

def is_model_allowed(spec: ModelSpec) -> bool:
    if ALLOW_MODELS == "all":
        return True
    return spec.preset_id in allowed_list

목적:
  - 허용된 모델만 사용
  - 리소스 남용 방지
```

### 8.3 데이터 보호

#### 환경 변수 관리
```bash
# .env (Git에서 제외)
API_KEY=secret-key-here
QDRANT_URL=http://localhost:6333

보안:
  - .gitignore에 .env 추가
  - 프로덕션: AWS Secrets Manager, Vault
  - 민감 정보 로그 제외
```

#### 네트워크 격리
```yaml
# docker-compose.yml
networks:
  internal:
    driver: bridge

services:
  vector-api:
    networks:
      - internal

목적:
  - 컨테이너 격리
  - 외부 접근 제한
```

### 8.4 에러 처리

#### 정보 누출 방지
```python
try:
    result = qdrant_search(...)
except Exception as e:
    # 내부 에러 숨김
    raise HTTPException(500, "Internal server error")
    # 로그에만 상세 기록
    logger.error(f"Search failed: {e}")

원칙:
  - 클라이언트에 최소 정보
  - 로그에 상세 정보
  - 스택 트레이스 숨김
```

### 8.5 리소스 제한

#### 요청 제한
```python
# 향후 구현: Rate Limiting
from slowapi import Limiter

limiter = Limiter(key_func=get_remote_address)

@app.post("/search")
@limiter.limit("100/minute")
async def search_vectors(...):
    ...

목적:
  - DDoS 방지
  - 리소스 남용 방지
```

#### 타임아웃 설정
```python
# Qdrant 클라이언트
client = QdrantClient(url, timeout=30)

# Uvicorn
uvicorn.run(app, timeout_keep_alive=30)

목적:
  - 무한 대기 방지
  - 리소스 해제
```

---

## 다음 단계

1. [배포 가이드](06_deployment.md) - 프로덕션 배포 전략
2. [사용 가이드](02_how_to_use.md) - API 사용 방법

---

## 참고 자료

- Clean Architecture: <https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html>
- Microservices Patterns: <https://microservices.io/patterns/>
- FastAPI Best Practices: <https://fastapi.tiangolo.com/tutorial/>
- Docker Best Practices: <https://docs.docker.com/develop/dev-best-practices/>
