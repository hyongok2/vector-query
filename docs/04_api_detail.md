# Vector Search API 상세 레퍼런스

이 문서는 Vector Search API의 모든 엔드포인트와 데이터 모델에 대한 상세한 레퍼런스를 제공합니다.

## 목차

1. [API 개요](#1-api-개요)
2. [인증](#2-인증)
3. [엔드포인트](#3-엔드포인트)
4. [데이터 모델](#4-데이터-모델)
5. [오류 코드](#5-오류-코드)
6. [예제 시나리오](#6-예제-시나리오)

---

## 1. API 개요

### 1.1 기본 정보

- Base URL: http://localhost:5200
- Protocol: HTTP/HTTPS
- Content-Type: application/json
- API Version: v1.0.2

### 1.2 API 특징

- RESTful 설계
- JSON 요청/응답
- 선택적 API 키 인증
- CORS 지원
- OpenAPI 3.0 스펙 제공

### 1.3 API 문서

- Swagger UI: http://localhost:5200/docs
- ReDoc: http://localhost:5200/redoc
- OpenAPI JSON: http://localhost:5200/openapi.json

---

## 2. 인증

### 2.1 API 키 인증

API_KEY 환경 변수가 설정된 경우에만 인증이 필요합니다.

헤더 형식:

```http
X-API-Key: your-secret-key-here
```

예제:

```bash
curl -H "X-API-Key: your-secret-key" \
     http://localhost:5200/search
```

### 2.2 인증 오류

401 Unauthorized

```json
{
  "detail": "Invalid API key"
}
```

---

## 3. 엔드포인트

### 3.1 Health Check

시스템 상태를 확인합니다.

Endpoint:

```http
GET /health
```

인증 필요: No

요청 예제:

```bash
curl http://localhost:5200/health
```

응답 예제:

```json
{
  "ok": true,
  "qdrant_url": "http://localhost:6333"
}
```

응답 필드:

| 필드 | 타입 | 설명 |
|------|------|------|
| ok | boolean | 서버 상태 (true: 정상) |
| qdrant_url | string | Qdrant 서버 URL |

---

### 3.2 Models List

사용 가능한 임베딩 모델 목록을 조회합니다.

Endpoint:

```http
GET /models
```

인증 필요: No

요청 예제:

```bash
curl http://localhost:5200/models
```

응답 예제:

```json
{
  "models": [
    {
      "preset_id": "bge-m3",
      "backend": "st",
      "name": "./models/bge-m3",
      "normalize": true,
      "e5_mode": "auto"
    },
    {
      "preset_id": "ko-sroberta",
      "backend": "st",
      "name": "./models/ko-sroberta",
      "normalize": true,
      "e5_mode": "auto"
    }
  ]
}
```

응답 필드:

| 필드 | 타입 | 설명 |
|------|------|------|
| models | array | 사용 가능한 모델 목록 |
| models[].preset_id | string | 모델 프리셋 ID |
| models[].backend | string | 백엔드 타입 |
| models[].name | string | 모델 경로 또는 이름 |
| models[].normalize | boolean | 벡터 정규화 여부 |
| models[].e5_mode | string | E5 모델 모드 |

---

### 3.3 Vector Search

텍스트 쿼리로 벡터 검색을 수행합니다.

Endpoint:

```http
POST /search
```

인증 필요: Yes (API_KEY 설정 시)

Content-Type: application/json

#### 요청 본문

```json
{
  "text": "검색할 텍스트",
  "top_k": 5,
  "threshold": 0.0,
  "with_payload": true,
  "preset_id": "bge-m3",
  "qdrant": {
    "url": "http://localhost:6333",
    "collection": "docs_2025",
    "query_filter": {
      "must": [
        {
          "key": "category",
          "match": {"value": "technology"}
        }
      ]
    }
  }
}
```

#### 요청 파라미터

최상위 필드:

| 필드 | 타입 | 필수 | 기본값 | 설명 |
|------|------|------|--------|------|
| text | string | Yes | - | 검색할 텍스트 쿼리 |
| top_k | integer | No | 5 | 반환할 최대 결과 수 (1-100) |
| threshold | float | No | 0.0 | 최소 유사도 점수 (0.0-1.0) |
| with_payload | boolean | No | true | 메타데이터 포함 여부 |
| preset_id | string | No | null | 모델 프리셋 ID |
| qdrant | object | Yes | - | Qdrant 연결 설정 |

QdrantCfg 객체:

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| url | string | Yes | Qdrant 서버 URL |
| collection | string | Yes | 컬렉션 이름 |
| query_filter | object | No | Qdrant 필터 조건 |

#### 응답

성공 응답 (200 OK):

```json
{
  "took_ms": 245,
  "model": {
    "backend": "st",
    "name": "./models/bge-m3",
    "normalize": true,
    "e5_mode": "auto"
  },
  "collection": "docs_2025",
  "total_candidates": 10,
  "hits": [
    {
      "id": "doc_001",
      "score": 0.8934,
      "payload": {
        "title": "인공지능 기술 동향",
        "content": "최신 AI 기술의 발전...",
        "category": "technology",
        "date": "2025-01-15"
      }
    }
  ]
}
```

응답 필드:

| 필드 | 타입 | 설명 |
|------|------|------|
| took_ms | integer | 검색 소요 시간 (밀리초) |
| model | object | 사용된 모델 정보 |
| collection | string | 검색한 컬렉션 이름 |
| total_candidates | integer | 검색된 전체 후보 수 |
| hits | array | 검색 결과 배열 |
| hits[].id | string/number | 문서 ID |
| hits[].score | float | 유사도 점수 (0.0-1.0) |
| hits[].payload | object | 문서 메타데이터 |

#### 오류 응답

400 Bad Request:

```json
{
  "detail": "Unknown preset_id"
}
```

404 Not Found:

```json
{
  "detail": "Qdrant error: Collection not found"
}
```

500 Internal Server Error:

```json
{
  "detail": "Embedding error: Model loading failed"
}
```

#### 요청 예제

기본 검색:

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

필터 검색:

```bash
curl -X POST http://localhost:5200/search \
  -H "Content-Type: application/json" \
  -d '{
    "text": "파이썬 프로그래밍",
    "top_k": 10,
    "threshold": 0.7,
    "preset_id": "ko-sroberta",
    "qdrant": {
      "url": "http://localhost:6333",
      "collection": "docs_2025",
      "query_filter": {
        "must": [
          {"key": "category", "match": {"value": "programming"}},
          {"key": "language", "match": {"value": "korean"}}
        ]
      }
    }
  }'
```

---

## 4. 데이터 모델

### 4.1 SearchRequest

검색 요청 모델

```typescript
interface SearchRequest {
  text: string;                    // 검색 텍스트 (필수)
  top_k?: number;                  // 최대 결과 수 (1-100)
  threshold?: number;              // 최소 점수 (0.0-1.0)
  with_payload?: boolean;          // 메타데이터 포함
  preset_id?: string;              // 모델 프리셋 ID
  qdrant: QdrantCfg;               // Qdrant 설정
}
```

### 4.2 QdrantCfg

Qdrant 연결 설정

```typescript
interface QdrantCfg {
  url: string;                     // Qdrant URL
  collection: string;              // 컬렉션 이름
  query_filter?: QdrantFilter;     // 필터 조건
}
```

### 4.3 QdrantFilter

Qdrant 필터 조건

```typescript
interface QdrantFilter {
  must?: FilterCondition[];        // AND 조건
  must_not?: FilterCondition[];    // NOT 조건
  should?: FilterCondition[];      // OR 조건
}

interface FilterCondition {
  key: string;                     // 필드 이름
  match?: {value: any};            // 값 일치
  range?: {                        // 범위 조건
    gte?: number;                  // 이상
    gt?: number;                   // 초과
    lte?: number;                  // 이하
    lt?: number;                   // 미만
  };
}
```

### 4.4 SearchResponse

검색 응답 모델

```typescript
interface SearchResponse {
  took_ms: number;                 // 소요 시간 (ms)
  model: object;                   // 사용된 모델
  collection: string;              // 컬렉션 이름
  total_candidates: number;        // 전체 후보 수
  hits: Hit[];                     // 검색 결과
}

interface Hit {
  id: string | number;             // 문서 ID
  score: number;                   // 유사도 점수
  payload?: Record<string, any>;   // 메타데이터
}
```

---

## 5. 오류 코드

### 5.1 HTTP 상태 코드

| 코드 | 이름 | 설명 |
|------|------|------|
| 200 | OK | 요청 성공 |
| 400 | Bad Request | 잘못된 요청 |
| 401 | Unauthorized | 인증 실패 |
| 404 | Not Found | 리소스 없음 |
| 500 | Internal Server Error | 서버 내부 오류 |

### 5.2 오류 응답 형식

```json
{
  "detail": "오류 메시지"
}
```

### 5.3 일반적인 오류 메시지

모델 관련:
- "Unknown preset_id" - 존재하지 않는 preset_id
- "Model not allowed" - 허용되지 않은 모델
- "Embedding error: ..." - 임베딩 생성 실패

Qdrant 관련:
- "Qdrant error: Collection not found" - 컬렉션 없음
- "Qdrant query failed" - 쿼리 실행 실패

인증 관련:
- "Invalid API key" - API 키 불일치

---

## 6. 예제 시나리오

### 6.1 기본 시맨틱 검색

사용자가 "머신러닝"에 관한 문서를 검색

```bash
curl -X POST http://localhost:5200/search \
  -H "Content-Type: application/json" \
  -d '{
    "text": "머신러닝 알고리즘과 응용",
    "top_k": 10,
    "preset_id": "bge-m3",
    "qdrant": {
      "url": "http://localhost:6333",
      "collection": "tech_docs"
    }
  }'
```

### 6.2 카테고리 필터 검색

특정 카테고리의 문서만 검색

```bash
curl -X POST http://localhost:5200/search \
  -H "Content-Type: application/json" \
  -d '{
    "text": "파이썬 웹 개발",
    "top_k": 5,
    "threshold": 0.6,
    "preset_id": "ko-sroberta",
    "qdrant": {
      "url": "http://localhost:6333",
      "collection": "tutorials",
      "query_filter": {
        "must": [
          {"key": "category", "match": {"value": "web_development"}},
          {"key": "language", "match": {"value": "python"}}
        ]
      }
    }
  }'
```

### 6.3 날짜 범위 검색

최근 2년 이내의 문서만 검색

```bash
curl -X POST http://localhost:5200/search \
  -H "Content-Type: application/json" \
  -d '{
    "text": "딥러닝 최신 동향",
    "top_k": 15,
    "preset_id": "mE5-large",
    "qdrant": {
      "url": "http://localhost:6333",
      "collection": "research_papers",
      "query_filter": {
        "must": [
          {"key": "year", "range": {"gte": 2023}}
        ]
      }
    }
  }'
```

### 6.4 복합 조건 검색

여러 조건을 조합한 정밀 검색

```bash
curl -X POST http://localhost:5200/search \
  -H "Content-Type: application/json" \
  -d '{
    "text": "자연어 처리 트랜스포머",
    "top_k": 20,
    "threshold": 0.7,
    "preset_id": "kure-v1",
    "qdrant": {
      "url": "http://localhost:6333",
      "collection": "ai_papers",
      "query_filter": {
        "must": [
          {"key": "topic", "match": {"value": "nlp"}},
          {"key": "year", "range": {"gte": 2020}},
          {"key": "citations", "range": {"gte": 50}}
        ],
        "must_not": [
          {"key": "retracted", "match": {"value": true}}
        ],
        "should": [
          {"key": "venue", "match": {"value": "ACL"}},
          {"key": "venue", "match": {"value": "EMNLP"}}
        ]
      }
    }
  }'
```

### 6.5 유사 문서 찾기

특정 문서와 유사한 다른 문서 검색

```python
import requests

# 기준 문서의 내용
reference_doc = "이 문서는 React 훅의 사용법을 설명합니다..."

# 유사 문서 검색
response = requests.post(
    "http://localhost:5200/search",
    json={
        "text": reference_doc,
        "top_k": 10,
        "threshold": 0.75,
        "preset_id": "bge-m3",
        "qdrant": {
            "url": "http://localhost:6333",
            "collection": "tech_docs",
            "query_filter": {
                "must_not": [
                    {"key": "id", "match": {"value": "original_doc_id"}}
                ]
            }
        }
    }
)

similar_docs = response.json()["hits"]
```

---

## 다음 단계

1. [설정 구성](03_setting_configuration.md) - 환경 변수 및 모델 설정
2. [아키텍처](05_architecture.md) - 시스템 구조 이해
3. [배포 가이드](06_deployment.md) - 프로덕션 배포

---

## 참고 자료

- FastAPI 문서: <https://fastapi.tiangolo.com/>
- Qdrant 필터링: <https://qdrant.tech/documentation/concepts/filtering/>
- OpenAPI 스펙: <https://swagger.io/specification/>
