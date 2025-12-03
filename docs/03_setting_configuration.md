# Vector Search API 설정 및 구성 가이드

이 문서는 Vector Search API의 상세한 설정 방법과 구성 옵션을 설명합니다.

## 목차

1. [환경 변수 설정](#1-환경-변수-설정)
2. [모델 구성](#2-모델-구성)
3. [Qdrant 연결 설정](#3-qdrant-연결-설정)
4. [성능 튜닝](#4-성능-튜닝)
5. [보안 설정](#5-보안-설정)
6. [Docker 구성](#6-docker-구성)

---

## 1. 환경 변수 설정

### 1.1 .env 파일 구조

Vector Search API는 .env 파일을 통해 환경 변수를 관리합니다.

```bash
# Qdrant 데이터베이스 설정
QDRANT_URL=http://localhost:6333
DEFAULT_COLLECTION=docs_2025

# 모델 접근 제어
ALLOW_MODELS=all

# 보안 설정
API_KEY=
CORS_ALLOW_ORIGINS=*

# 성능 설정
DEVICE=auto
TORCH_NUM_THREADS=4

# 고급 설정 (선택사항)
ST_TRUST_REMOTE_CODE=0
HF_HOME=/app/.cache/huggingface
TRANSFORMERS_CACHE=/app/.cache/huggingface
SENTENCE_TRANSFORMERS_HOME=/app/.cache/huggingface

# 오프라인 모드 (폐쇄망 환경)
HF_HUB_OFFLINE=1
TRANSFORMERS_OFFLINE=1
```

### 1.2 환경 변수 상세 설명

#### Qdrant 연결 설정

**QDRANT_URL**

- 설명: Qdrant 서버 URL
- 기본값: http://localhost:6333
- 예제:
  - 로컬: http://localhost:6333
  - 원격: http://192.168.1.100:6333
  - Docker 네트워크: http://qdrant:6333

**DEFAULT_COLLECTION**

- 설명: 기본 컬렉션 이름
- 기본값: docs_2025
- 참고: 요청 시 다른 컬렉션을 지정할 수 있음

#### 모델 접근 제어

**ALLOW_MODELS**

- 설명: 허용할 모델 목록
- 옵션:
  - all: 모든 모델 허용 (권장)
  - backend:name,backend:name: 특정 모델만 허용
- 예제:

```bash
# 모든 모델 허용
ALLOW_MODELS=all

# 특정 모델만 허용
ALLOW_MODELS=st:./models/bge-m3,st:./models/ko-sroberta
```

#### 보안 설정

**API_KEY**

- 설명: API 인증 키 (선택사항)
- 기본값: 빈 문자열 (인증 비활성화)
- 사용법:

```bash
# .env 파일
API_KEY=your-secret-key-here

# API 호출 시
curl -H "X-API-Key: your-secret-key-here" ...
```

**CORS_ALLOW_ORIGINS**

- 설명: CORS 허용 오리진
- 기본값: * (모든 오리진 허용)
- 예제:

```bash
# 모든 오리진 허용
CORS_ALLOW_ORIGINS=*

# 특정 도메인만 허용
CORS_ALLOW_ORIGINS=https://example.com,https://app.example.com
```

#### 성능 설정

**DEVICE**

- 설명: 연산 디바이스 선택
- 옵션:
  - auto: 자동 선택 (CUDA > MPS > CPU)
  - cuda: NVIDIA GPU 사용
  - mps: Apple Silicon GPU 사용
  - cpu: CPU만 사용
- 기본값: auto
- 예제:

```bash
# GPU 강제 사용 (NVIDIA)
DEVICE=cuda

# Apple Silicon GPU 사용
DEVICE=mps

# CPU만 사용 (호환성 최대)
DEVICE=cpu
```

**TORCH_NUM_THREADS**

- 설명: PyTorch CPU 스레드 수
- 기본값: 4
- 권장값:
  - 저사양: 2-4
  - 일반: 4-8
  - 고사양: 8-16
- 예제:

```bash
# CPU 코어가 8개인 경우
TORCH_NUM_THREADS=8
```

#### 고급 설정

**ST_TRUST_REMOTE_CODE**

- 설명: Sentence Transformers 원격 코드 실행 허용
- 기본값: 0 (비활성화)
- 보안: 신뢰할 수 있는 모델만 1로 설정
- 예제:

```bash
# 비활성화 (권장)
ST_TRUST_REMOTE_CODE=0

# 활성화 (신뢰할 수 있는 모델만)
ST_TRUST_REMOTE_CODE=1
```

**HF_HOME, TRANSFORMERS_CACHE, SENTENCE_TRANSFORMERS_HOME**

- 설명: Hugging Face 캐시 디렉토리
- 기본값: ~/.cache/huggingface
- 용도: 모델 캐시 위치 변경
- 예제:

```bash
HF_HOME=/data/models/cache
TRANSFORMERS_CACHE=/data/models/cache
SENTENCE_TRANSFORMERS_HOME=/data/models/cache
```

**HF_HUB_OFFLINE, TRANSFORMERS_OFFLINE**

- 설명: 오프라인 모드 (폐쇄망 환경)
- 기본값: 0 (온라인 모드)
- 용도: 인터넷 없이 로컬 모델만 사용
- 예제:

```bash
# 오프라인 모드 활성화
HF_HUB_OFFLINE=1
TRANSFORMERS_OFFLINE=1
```

---

## 2. 모델 구성

### 2.1 models_config.yaml 구조

모델 설정은 config/models_config.yaml 파일에서 관리합니다.

```yaml
# 모델 정의
models:
  # 모델 ID (preset_id로 사용)
  bge-m3:
    backend: st                    # 백엔드 타입
    path: ./models/bge-m3          # 모델 경로
    normalize: true                # 벡터 정규화 여부
    e5_mode: auto                  # E5 모델 모드
    description: "BGE-M3 model"    # 설명 (메타데이터)
    dimension: 1024                # 벡터 차원 (메타데이터)

# 전역 설정
settings:
  default_model: bge-m3
  trust_remote_code: false
  cache_models: true
  max_cached_models: 5
  batch_size: 32
  max_sequence_length: 512
```

### 2.2 모델 파라미터 설명

#### 필수 파라미터

**backend**

- 설명: 임베딩 백엔드
- 옵션:
  - st: Sentence Transformers (권장)
  - fastembed: FastEmbed (실험적)
- 기본값: st

**path**

- 설명: 모델 파일 경로
- 형식:
  - 상대 경로: ./models/model-name
  - 절대 경로: /data/models/model-name
  - Hugging Face: organization/model-name
- 예제:

```yaml
# 로컬 경로
path: ./models/bge-m3

# Hugging Face Hub
path: BAAI/bge-m3
```

**normalize**

- 설명: 벡터 정규화 (L2 normalization)
- 기본값: true
- 권장: true (코사인 유사도 사용 시)
- 예제:

```yaml
# 정규화 활성화 (권장)
normalize: true

# 정규화 비활성화
normalize: false
```

**e5_mode**

- 설명: E5 모델 프리픽스 모드
- 옵션:
  - auto: 자동 (query 기본)
  - query: "query: " 프리픽스 추가
  - passage: "passage: " 프리픽스 추가
- 기본값: auto
- 참고: E5 계열 모델에서만 적용
- 예제:

```yaml
# E5 모델
e5_mode: query

# 일반 모델
e5_mode: auto
```

#### 메타데이터 파라미터

**description**

- 설명: 모델 설명
- 용도: API 응답 및 문서화
- 선택사항

**dimension**

- 설명: 벡터 차원 수
- 용도: Qdrant 컬렉션 생성 시 참고
- 선택사항

### 2.3 전역 설정 (settings)

**default_model**

- 설명: 기본 모델 preset_id
- 기본값: bge-m3
- 용도: preset_id 미지정 시 사용

**trust_remote_code**

- 설명: 원격 코드 실행 허용
- 기본값: false
- 보안: false 권장

**cache_models**

- 설명: 모델 메모리 캐싱
- 기본값: true
- 권장: true (성능 향상)

**max_cached_models**

- 설명: 최대 캐시 모델 수
- 기본값: 5
- 메모리: 모델당 약 500MB-2GB

**batch_size**

- 설명: 배치 처리 크기
- 기본값: 32
- 권장값:
  - CPU: 16-32
  - GPU (8GB): 32-64
  - GPU (16GB+): 64-128

**max_sequence_length**

- 설명: 최대 토큰 길이
- 기본값: 512
- 참고: 모델별로 다를 수 있음

### 2.4 새 모델 추가 예제

#### 한국어 모델 추가

```yaml
models:
  ko-custom:
    backend: st
    path: ./models/ko-custom-model
    normalize: true
    e5_mode: auto
    description: "Custom Korean embedding model"
    dimension: 768
```

#### Hugging Face 모델 직접 사용

```yaml
models:
  hf-model:
    backend: st
    path: sentence-transformers/all-MiniLM-L6-v2
    normalize: true
    e5_mode: auto
    description: "Lightweight multilingual model"
    dimension: 384
```

---

## 3. Qdrant 연결 설정

### 3.1 로컬 Qdrant 설정

```bash
# Docker로 Qdrant 실행
docker run -p 6333:6333 qdrant/qdrant

# .env 설정
QDRANT_URL=http://localhost:6333
```

### 3.2 원격 Qdrant 설정

```bash
# .env 설정
QDRANT_URL=http://192.168.1.100:6333

# 또는 도메인
QDRANT_URL=http://qdrant.example.com:6333
```

### 3.3 Qdrant Cloud 설정

```bash
# Qdrant Cloud URL
QDRANT_URL=https://your-cluster.cloud.qdrant.io

# API 키가 필요한 경우 코드 수정 필요
```

### 3.4 컬렉션 생성

```python
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

client = QdrantClient("http://localhost:6333")

# 컬렉션 생성
client.create_collection(
    collection_name="docs_2025",
    vectors_config=VectorParams(
        size=1024,              # 벡터 차원 (모델에 맞게)
        distance=Distance.COSINE  # 유사도 측정 방식
    )
)
```

---

## 4. 성능 튜닝

### 4.1 GPU 최적화

```bash
# NVIDIA GPU 사용
DEVICE=cuda
TORCH_NUM_THREADS=4

# 배치 크기 증가 (GPU 메모리에 따라)
# config/models_config.yaml
settings:
  batch_size: 64
```

### 4.2 CPU 최적화

```bash
# CPU 스레드 수 조정
TORCH_NUM_THREADS=8

# 배치 크기 감소
settings:
  batch_size: 16
```

### 4.3 메모리 최적화

```yaml
# config/models_config.yaml
settings:
  # 캐시 모델 수 제한
  max_cached_models: 3

  # 시퀀스 길이 제한
  max_sequence_length: 256
```

### 4.4 모델 선택 전략

속도 우선:

- mE5-small (384차원)
- paraphrase-ml (384차원)

품질 우선:

- bge-m3 (1024차원)
- mE5-large (1024차원)

한국어 최적화:

- ko-sroberta (768차원)
- kure-v1 (1024차원)

균형:

- mE5-base (768차원)
- ko-sbert (768차원)

---

## 5. 보안 설정

### 5.1 API 키 인증

```bash
# .env 파일
API_KEY=your-strong-secret-key-here
```

API 호출 시:

```bash
curl -H "X-API-Key: your-strong-secret-key-here" \
     -X POST http://localhost:5200/search \
     -d '{...}'
```

### 5.2 CORS 설정

```bash
# 특정 도메인만 허용
CORS_ALLOW_ORIGINS=https://app.example.com,https://admin.example.com

# 프로덕션 환경에서는 * 사용 금지
# CORS_ALLOW_ORIGINS=*  # 개발 환경에서만
```

### 5.3 모델 접근 제어

```bash
# 특정 모델만 허용
ALLOW_MODELS=st:./models/bge-m3,st:./models/ko-sroberta

# 실험적 모델 차단
```

### 5.4 원격 코드 실행 제한

```bash
# 원격 코드 실행 비활성화 (권장)
ST_TRUST_REMOTE_CODE=0
```

---

## 6. Docker 구성

### 6.1 docker-compose.yml 구조

```yaml
services:
  vector-api:
    env_file:
      - .env
    build:
      context: .
      dockerfile: Dockerfile
    image: vector-search-api:v1.0.2
    container_name: vector-search-api
    ports:
      - "5200:5200"
    environment:
      - QDRANT_URL=http://localhost:6333
      - DEVICE=auto
    volumes:
      - ./models:/app/models:ro
      - ./config:/app/config:ro
      - model_cache:/app/.cache/huggingface
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5200/health"]
      interval: 30s
      timeout: 10s
      retries: 5

volumes:
  model_cache:
    driver: local
```

### 6.2 볼륨 구성

```yaml
volumes:
  # 모델 파일 (읽기 전용)
  - ./models:/app/models:ro

  # 설정 파일 (읽기 전용)
  - ./config:/app/config:ro

  # 모델 캐시 (읽기/쓰기)
  - model_cache:/app/.cache/huggingface

  # 로그 파일 (읽기/쓰기)
  - ./logs:/app/logs
```

### 6.3 네트워크 설정

```yaml
# Qdrant와 같은 네트워크 사용
services:
  qdrant:
    image: qdrant/qdrant
    ports:
      - "6333:6333"
    networks:
      - vector-net

  vector-api:
    environment:
      - QDRANT_URL=http://qdrant:6333
    networks:
      - vector-net

networks:
  vector-net:
    driver: bridge
```

### 6.4 리소스 제한

```yaml
services:
  vector-api:
    deploy:
      resources:
        limits:
          cpus: '4'
          memory: 8G
        reservations:
          cpus: '2'
          memory: 4G
```

---

## 다음 단계

1. API 상세 (04_api_detail.md)
2. 아키텍처 (05_architecture.md)
3. 배포 가이드 (06_deployment.md)

---

## 참고 자료

- Qdrant 설정: <https://qdrant.tech/documentation/guides/configuration/>
- PyTorch 성능 튜닝: <https://pytorch.org/tutorials/recipes/recipes/tuning_guide.html>
- Sentence Transformers: <https://www.sbert.net/>
