# Qdrant 필터링 완벽 가이드

Qdrant 벡터 검색에서 페이로드 기반 필터링을 활용한 정교한 검색 방법

## 📋 목차

- [개요](#개요)
- [필터 연산자](#필터-연산자)
  - [must (AND)](#must-and)
  - [should (OR)](#should-or)
  - [must_not (NOT)](#must_not-not)
- [필터 조건 종류](#필터-조건-종류)
- [Nested 필터](#nested-필터)
- [실전 활용 예시](#실전-활용-예시)
- [API 사용 방법](#api-사용-방법)

---

## 🎯 개요

Qdrant의 필터링 기능은 벡터 검색 전에 페이로드(metadata) 조건으로 데이터를 **사전 필터링**합니다.
이를 통해 "특정 카테고리의 문서만" 또는 "특정 날짜 이후의 데이터만" 검색하는 등 비즈니스 요구사항에 맞는 정교한 검색이 가능합니다.

### 필터링 작동 원리

```
1. 페이로드 필터 적용 (사전 필터링)
   ↓
2. 필터를 통과한 벡터들만 대상으로 유사도 검색
   ↓
3. 상위 K개 결과 반환
```

### 현재 프로젝트 구현 상태

✅ **백엔드**: 완전히 구현됨 (`vector-search-api/app/qdrant_wrapper.py`)
⚠️ **프론트엔드**: UI 입력 기능 미구현 (`web-test-tool`)

---

## 🔧 필터 연산자

필터 조건들을 논리 연산으로 결합할 수 있습니다.

### must (AND)

모든 조건이 **동시에** 만족되어야 합니다.

```json
{
  "must": [
    { "key": "category", "match": { "value": "기술문서" } },
    { "key": "year", "range": { "gte": 2023 } }
  ]
}
```

**결과**: 2023년 이후 작성된 기술문서만 검색

### should (OR)

**최소 하나** 이상의 조건이 만족되면 됩니다.

```json
{
  "should": [
    { "key": "author", "match": { "value": "홍길동" } },
    { "key": "author", "match": { "value": "김철수" } }
  ]
}
```

**결과**: 홍길동 또는 김철수가 작성한 문서

### must_not (NOT)

지정된 조건을 **모두 제외**합니다.

```json
{
  "must_not": [
    { "key": "status", "match": { "value": "draft" } }
  ]
}
```

**결과**: 초안(draft) 상태가 아닌 문서들만

### 조합 사용

```json
{
  "must": [
    { "key": "category", "match": { "value": "AI" } },
    { "key": "year", "range": { "gte": 2024 } }
  ],
  "must_not": [
    { "key": "status", "match": { "value": "archived" } }
  ]
}
```

**결과**: 2024년 이후 작성된 AI 카테고리 문서 중 보관되지 않은 것들

---

## 🛠️ 필터 조건 종류

### 1. match - 정확한 값 매칭

keyword, integer, boolean 타입에 사용

```json
{ "key": "status", "match": { "value": "published" } }
{ "key": "likes", "match": { "value": 100 } }
{ "key": "is_public", "match": { "value": true } }
```

### 2. match any - IN 연산자

여러 값 중 **하나라도 일치**하면 매칭

```json
{
  "key": "tags",
  "match": { "any": ["AI", "머신러닝", "딥러닝"] }
}
```

**예시**: tags가 "AI", "머신러닝", "딥러닝" 중 하나라도 포함된 문서

### 3. match except - NOT IN 연산자

지정된 값들을 **모두 제외**

```json
{
  "key": "language",
  "match": { "except": ["en", "ja"] }
}
```

**예시**: 영어, 일본어를 제외한 다른 언어 문서

### 4. range - 범위 조건

숫자값에 대한 비교 연산 (`gt`, `gte`, `lt`, `lte`)

```json
{
  "key": "price",
  "range": {
    "gte": 10000,
    "lte": 50000
  }
}
```

**예시**: 가격이 10,000원 이상 50,000원 이하인 상품

### 5. range (날짜) - 시간 범위

RFC 3339 형식 (ISO 8601) 지원

```json
{
  "key": "created_at",
  "range": {
    "gte": "2024-01-01T00:00:00Z",
    "lt": "2025-01-01T00:00:00Z"
  }
}
```

**예시**: 2024년에 작성된 문서

### 6. match text - 전문 검색

텍스트에서 **모든 단어**가 포함되어야 함 (순서 무관)

```json
{
  "key": "description",
  "match": { "text": "빠른 성능" }
}
```

**예시**: "빠른"과 "성능" 단어가 모두 포함된 설명

### 7. match phrase - 구문 검색

**정확한 순서**대로 일치해야 함

```json
{
  "key": "title",
  "match": { "phrase": "인공지능 기술" }
}
```

**예시**: "인공지능 기술"이 정확히 이 순서로 제목에 포함

### 8. geo_radius - 원형 지역 검색

중심점과 반경(미터)으로 원형 영역 지정

```json
{
  "key": "location",
  "geo_radius": {
    "center": {
      "lon": 126.978,
      "lat": 37.566
    },
    "radius": 5000
  }
}
```

**예시**: 서울 중심부 반경 5km 이내 위치

### 9. geo_bounding_box - 직사각형 영역

좌상단과 우하단 좌표로 직사각형 영역 지정

```json
{
  "key": "location",
  "geo_bounding_box": {
    "top_left": {
      "lon": 126.5,
      "lat": 37.7
    },
    "bottom_right": {
      "lon": 127.2,
      "lat": 37.4
    }
  }
}
```

**예시**: 서울 특정 구역 내 위치

### 10. geo_polygon - 다각형 영역

복잡한 경계선을 다각형으로 정의

```json
{
  "key": "location",
  "geo_polygon": {
    "exterior": {
      "points": [
        { "lon": 126.5, "lat": 37.5 },
        { "lon": 127.0, "lat": 37.6 },
        { "lon": 127.0, "lat": 37.4 }
      ]
    }
  }
}
```

**예시**: 불규칙한 행정구역 경계 내 위치

### 11. values_count - 배열 길이 조건

배열 필드의 요소 개수로 필터링

```json
{
  "key": "tags",
  "values_count": { "gte": 3 }
}
```

**예시**: 태그가 3개 이상인 문서

### 12. is_empty / is_null

필드가 비어있거나 null인 경우

```json
{ "is_empty": { "key": "comments" } }
{ "is_null": { "key": "deleted_at" } }
```

**예시**: 댓글이 없거나, 삭제되지 않은 문서

### 13. has_id - ID 기반 필터

특정 ID 목록만 검색

```json
{ "has_id": [1, 5, 10, 23, 47] }
```

**예시**: 지정된 ID의 문서만 검색

---

## 🎯 Nested 필터

배열 내 **같은 객체**에서 여러 조건을 동시에 만족해야 할 때 사용합니다.

### 문제 상황

다음과 같은 데이터가 있을 때:

```json
{
  "id": 1,
  "title": "공룡 백과사전",
  "diet": [
    { "food": "고기", "likes": true },
    { "food": "풀", "likes": false }
  ]
}
```

### ❌ 잘못된 방식 (Nested 없이)

```json
{
  "must": [
    { "key": "diet[].food", "match": { "value": "고기" } },
    { "key": "diet[].likes", "match": { "value": true } }
  ]
}
```

**문제점**: 서로 다른 배열 요소에서 조건이 만족되어도 통과됨
- `diet[0].food = "고기"` (만족)
- `diet[1].likes = false` (다른 요소에서 likes 확인)

### ✅ 올바른 방식 (Nested 사용)

```json
{
  "nested": {
    "key": "diet",
    "filter": {
      "must": [
        { "key": "food", "match": { "value": "고기" } },
        { "key": "likes", "match": { "value": true } }
      ]
    }
  }
}
```

**효과**: **같은 배열 요소** 내에서 두 조건이 모두 만족되어야 함

### 실전 예시: 상품 옵션 필터링

```json
{
  "nested": {
    "key": "options",
    "filter": {
      "must": [
        { "key": "color", "match": { "value": "black" } },
        { "key": "size", "match": { "value": "L" } },
        { "key": "stock", "range": { "gt": 0 } }
      ]
    }
  }
}
```

**결과**: 같은 옵션에서 "검정색 + L사이즈 + 재고있음"을 모두 만족하는 상품

---

## 💡 실전 활용 예시

### 예시 1: 기술 블로그 검색

"최근 AI 관련 게시물 중 초안 제외"

```json
{
  "must": [
    { "key": "category", "match": { "value": "기술" } },
    { "key": "published_date", "range": { "gte": "2024-01-01T00:00:00Z" } },
    { "key": "content", "match": { "text": "AI 머신러닝" } }
  ],
  "must_not": [
    { "key": "status", "match": { "value": "draft" } }
  ]
}
```

### 예시 2: 지역 맛집 검색

"강남역 반경 3km, 평점 4.0 이상, 한식/일식"

```json
{
  "must": [
    {
      "key": "location",
      "geo_radius": {
        "center": { "lon": 127.0276, "lat": 37.4979 },
        "radius": 3000
      }
    },
    { "key": "rating", "range": { "gte": 4.0 } },
    { "key": "cuisine", "match": { "any": ["한식", "일식"] } }
  ]
}
```

### 예시 3: 이커머스 상품 검색

"Samsung 브랜드, 검정색 재고 있는 상품"

```json
{
  "must": [
    { "key": "brand", "match": { "value": "Samsung" } },
    {
      "nested": {
        "key": "options",
        "filter": {
          "must": [
            { "key": "color", "match": { "value": "black" } },
            { "key": "stock", "range": { "gt": 0 } }
          ]
        }
      }
    }
  ]
}
```

### 예시 4: 부동산 매물 검색

"서울 특정 구역, 가격대, 방 2개 이상, 최근 1년 이내 등록"

```json
{
  "must": [
    {
      "key": "location",
      "geo_bounding_box": {
        "top_left": { "lon": 126.9, "lat": 37.6 },
        "bottom_right": { "lon": 127.1, "lat": 37.4 }
      }
    },
    { "key": "price", "range": { "gte": 300000000, "lte": 500000000 } },
    { "key": "rooms", "range": { "gte": 2 } },
    { "key": "registered_date", "range": { "gte": "2024-01-01T00:00:00Z" } }
  ],
  "must_not": [
    { "key": "status", "match": { "value": "sold" } }
  ]
}
```

### 예시 5: 채용 공고 검색

"서울 소재 IT 회사, 연봉 5천만원 이상, Python 기술스택 포함"

```json
{
  "must": [
    { "key": "location.city", "match": { "value": "서울" } },
    { "key": "industry", "match": { "value": "IT" } },
    { "key": "salary", "range": { "gte": 50000000 } },
    { "key": "tech_stack", "match": { "any": ["Python", "Django", "FastAPI"] } }
  ],
  "should": [
    { "key": "benefits", "match": { "text": "재택근무" } },
    { "key": "benefits", "match": { "text": "유연근무" } }
  ]
}
```

**참고**: `should` 사용 시 하나라도 만족하면 우선순위 상승

---

## 🔌 API 사용 방법

### Python Client 예시

```python
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue, Range

client = QdrantClient(url="http://localhost:6333")

# 필터 정의
search_filter = Filter(
    must=[
        FieldCondition(
            key="category",
            match=MatchValue(value="기술")
        ),
        FieldCondition(
            key="year",
            range=Range(gte=2024)
        )
    ]
)

# 검색 실행
results = client.query_points(
    collection_name="documents",
    query=[0.1, 0.2, ...],  # 쿼리 벡터
    query_filter=search_filter,
    limit=10
)
```

### REST API 예시 (현재 프로젝트)

**엔드포인트**: `POST http://localhost:5200/search`

**요청 본문**:

```json
{
  "text": "인공지능 최신 동향",
  "preset_id": "bge-m3",
  "top_k": 10,
  "threshold": 0.7,
  "with_payload": true,
  "qdrant": {
    "url": "http://localhost:6333",
    "collection": "tech_documents",
    "query_filter": {
      "must": [
        { "key": "category", "match": { "value": "AI" } },
        { "key": "year", "range": { "gte": 2024 } }
      ],
      "must_not": [
        { "key": "status", "match": { "value": "draft" } }
      ]
    }
  }
}
```

### cURL 예시

```bash
curl -X POST http://localhost:5200/search \
  -H "Content-Type: application/json" \
  -d '{
    "text": "벡터 검색 최적화",
    "preset_id": "bge-m3",
    "top_k": 5,
    "qdrant": {
      "url": "http://localhost:6333",
      "collection": "documents",
      "query_filter": {
        "must": [
          { "key": "category", "match": { "value": "기술" } }
        ]
      }
    }
  }'
```

---

## 📚 추가 자료

- [Qdrant 공식 문서 - Filtering](https://qdrant.tech/documentation/concepts/filtering/)
- [Qdrant Python Client](https://python-client.qdrant.tech/)
- [프로젝트 API 문서](./API_DOCUMENTATION.md)
- [Qdrant 선정 배경](./why_qdrant.md)

---

## 🎓 핵심 요약

1. **필터 연산자**: `must` (AND), `should` (OR), `must_not` (NOT)
2. **조건 종류**: match, range, geo, text, nested 등 13가지
3. **Nested 필터**: 배열 내 같은 객체에서 여러 조건 동시 만족
4. **현재 상태**: 백엔드 완전 구현, 웹 UI 입력 기능만 추가 필요
5. **활용 가치**: 비즈니스 요구사항에 맞는 정교한 벡터 검색 가능

---

**작성일**: 2025-11-13
**작성자**: 문형옥(by claude code)
**버전**: 1.0.0
