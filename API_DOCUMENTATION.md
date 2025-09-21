# Vector Search API Documentation

벡터 검색 API 완전 가이드 - 임베딩 모델과 Qdrant를 활용한 의미 기반 검색

## 📋 목차

- [API 개요](#api-개요)
- [인증](#인증)
- [엔드포인트](#엔드포인트)
  - [GET /health](#get-health)
  - [GET /models](#get-models)
  - [POST /search](#post-search)
- [데이터 모델](#데이터-모델)
- [사용 예제](#사용-예제)
- [오류 처리](#오류-처리)

## 🌐 API 개요

**Base URL**: `http://localhost:5200`
**Content-Type**: `application/json`
**API 버전**: `0.1.0`

### 지원 기능
- 다중 임베딩 모델 지원 (FastEmbed, SentenceTransformers)
- Qdrant 벡터 데이터베이스 통합
- 프리셋 모델 설정
- 유연한 검색 매개변수
- 실시간 성능 모니터링

## 🔐 인증

API 키 기반 인증 (선택사항)

```http
X-API-Key: your-api-key-here
```

환경변수 `API_KEY`가 설정된 경우에만 인증이 필요합니다.

## 🛠 엔드포인트

### GET /health

서버 상태 및 Qdrant 연결 확인

#### 요청
```http
GET /health
```

#### 응답
```json
{
  "ok": true,
  "qdrant_url": "http://localhost:6333"
}
```

#### 상태 코드
- `200`: 서비스 정상
- `500`: 서버 오류

---

### GET /models

사용 가능한 임베딩 모델 목록 조회

#### 요청
```http
GET /models
```

#### 응답
```json
{
  "models": [
    {
      "preset_id": "bge-m3",
      "backend": "fastembed",
      "name": "./models/bge-m3",
      "normalize": true,
      "e5_mode": "auto"
    },
    {
      "preset_id": "ko-sbert",
      "backend": "st",
      "name": "./models/ko-sbert",
      "normalize": true,
      "e5_mode": "auto"
    }
  ]
}
```

#### 필드 설명
- **preset_id**: 프리셋 모델 식별자
- **backend**: 백엔드 타입 (`fastembed` | `st`)
- **name**: 모델 경로 또는 이름
- **normalize**: 벡터 정규화 여부
- **e5_mode**: E5 모델 모드 (`auto` | `query` | `passage`)

---

### POST /search

벡터 유사도 검색 수행

#### 요청

##### 헤더
```http
Content-Type: application/json
X-API-Key: your-api-key-here  # 선택사항
```

##### 본문 (프리셋 사용)
```json
{
  "text": "사용자 검색 쿼리",
  "preset_id": "ko-sbert",
  "top_k": 10,
  "threshold": 0.7,
  "with_payload": true,
  "qdrant": {
    "url": "http://localhost:6333",
    "collection": "documents",
    "query_filter": {
      "must": [
        {
          "key": "category",
          "match": {"value": "tech"}
        }
      ]
    }
  }
}
```

##### 본문 (모델 직접 지정)
```json
{
  "text": "검색할 텍스트",
  "model": {
    "backend": "st",
    "name": "./models/mE5-base",
    "normalize": true,
    "e5_mode": "query"
  },
  "top_k": 5,
  "threshold": 0.5,
  "with_payload": false,
  "qdrant": {
    "url": "http://localhost:6333",
    "collection": "my_docs"
  }
}
```

#### 요청 매개변수

| 필드 | 타입 | 필수 | 기본값 | 설명 |
|------|------|------|--------|------|
| `text` | string | ✅ | - | 검색할 텍스트 쿼리 |
| `preset_id` | string | ❌ | null | 프리셋 모델 ID (우선순위 높음) |
| `model` | ModelSpec | ❌ | bge-m3 | 모델 설정 객체 |
| `top_k` | integer | ❌ | 5 | 반환할 최대 결과 수 (1-100) |
| `threshold` | float | ❌ | 0.0 | 최소 유사도 점수 (0.0-1.0) |
| `with_payload` | boolean | ❌ | true | 메타데이터 포함 여부 |
| `qdrant` | QdrantCfg | ✅ | - | Qdrant 설정 |

#### ModelSpec 객체

| 필드 | 타입 | 기본값 | 설명 |
|------|------|--------|------|
| `backend` | string | "fastembed" | 백엔드 타입 (`fastembed` \| `st`) |
| `name` | string | "BAAI/bge-m3" | 모델 이름 또는 경로 |
| `normalize` | boolean | true | L2 정규화 적용 여부 |
| `e5_mode` | string | "auto" | E5 모델 모드 (`auto` \| `query` \| `passage`) |

#### QdrantCfg 객체

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `url` | string | ✅ | Qdrant 서버 URL |
| `collection` | string | ✅ | 검색할 컬렉션 이름 |
| `query_filter` | object | ❌ | Qdrant 필터 조건 |

#### 응답
```json
{
  "took_ms": 45,
  "model": {
    "backend": "st",
    "name": "./models/ko-sbert",
    "normalize": true,
    "e5_mode": "auto"
  },
  "collection": "documents",
  "total_candidates": 100,
  "hits": [
    {
      "id": "doc_123",
      "score": 0.8756,
      "payload": {
        "title": "문서 제목",
        "content": "문서 내용 일부...",
        "category": "tech",
        "created_at": "2024-01-15"
      }
    },
    {
      "id": 456,
      "score": 0.8234,
      "payload": {
        "title": "다른 문서",
        "url": "https://example.com"
      }
    }
  ]
}
```

#### 응답 필드

| 필드 | 타입 | 설명 |
|------|------|------|
| `took_ms` | integer | 검색 소요 시간 (밀리초) |
| `model` | ModelSpec | 사용된 모델 정보 |
| `collection` | string | 검색된 컬렉션 이름 |
| `total_candidates` | integer | 필터링 전 총 후보 수 |
| `hits` | Hit[] | 검색 결과 배열 |

#### Hit 객체

| 필드 | 타입 | 설명 |
|------|------|------|
| `id` | any | 문서 ID (string, number 등) |
| `score` | float | 유사도 점수 (0.0-1.0) |
| `payload` | object | 문서 메타데이터 (optional) |

#### 상태 코드
- `200`: 검색 성공
- `400`: 잘못된 요청 (모델 불허용, 잘못된 파라미터)
- `401`: 인증 실패
- `404`: Qdrant 연결 오류 또는 컬렉션 없음
- `500`: 임베딩 또는 서버 오류

## 📊 데이터 모델

### 지원 모델 백엔드

#### FastEmbed (권장 - CPU 최적화)
- **특징**: ONNX Runtime 기반, 빠른 CPU 추론
- **장점**: 낮은 메모리 사용, 빠른 시작 시간
- **단점**: 모델 선택권 제한

```json
{
  "backend": "fastembed",
  "name": "./models/bge-m3"
}
```

#### SentenceTransformers (유연성)
- **특징**: PyTorch 기반, GPU/CPU 지원
- **장점**: 모든 Hugging Face 모델 지원
- **단점**: 더 많은 메모리 사용

```json
{
  "backend": "st",
  "name": "./models/ko-sbert"
}
```

### 프리셋 모델 목록

| Preset ID | 백엔드 | 용도 | 언어 | 차원 |
|-----------|---------|------|------|------|
| `bge-m3` | fastembed | 범용 다국어 | 다국어 | 1024 |
| `mE5-small` | fastembed | 경량 다국어 | 다국어 | 384 |
| `mE5-base` | st | 균형 다국어 | 다국어 | 768 |
| `mE5-large` | st | 고성능 다국어 | 다국어 | 1024 |
| `ko-sbert` | st | 한국어 특화 | 한국어 | 768 |
| `ko-sroberta` | st | 한국어 RoBERTa | 한국어 | 768 |
| `ko-simcse` | st | 한국어 SimCSE | 한국어 | 768 |
| `ko-sentence` | st | 한국어 문장 | 한국어 | 768 |
| `paraphrase-ml` | st | 의역 다국어 | 다국어 | 768 |
| `nomic-embed` | st | Nomic 임베딩 | 영어 | 768 |

