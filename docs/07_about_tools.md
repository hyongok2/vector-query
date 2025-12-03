# Vector Search 유틸리티 도구

이 문서는 Vector Search 프로젝트와 함께 제공되는 3가지 유틸리티 도구의 기능과 사용법을 설명합니다.

## 목차

1. [도구 개요](#1-도구-개요)
2. [vector-collection-test](#2-vector-collection-test)
3. [vector-db2embed](#3-vector-db2embed)
4. [web-test-tool](#4-web-test-tool)

---

## 1. 도구 개요

### 1.1 도구 목록

| 도구명 | 타입 | 목적 | 주요 기술 |
|--------|------|------|-----------|
| vector-collection-test | Python Script | 벡터 검색 품질 검증 | Python, OracleDB, Requests |
| vector-db2embed | Streamlit App | DB → Vector 임베딩 생성 | Streamlit, SQLAlchemy, Qdrant |
| web-test-tool | React Web App | Vector 검색 API 테스트 | React, TypeScript, Vite |

### 1.2 디렉토리 구조

```
tools/
├── vector-collection-test/     # 벡터 검색 품질 검증 스크립트
│   ├── equipment_vector_validation.py
│   └── equipment_vector_validation_csv.py
├── vector-db2embed/            # DB → Vector 임베딩 도구
│   ├── streamlit_app.py
│   ├── requirements.txt
│   ├── config/
│   ├── src/
│   └── docker/
└── web-test-tool/              # Vector 검색 웹 테스트 도구
    ├── src/
    ├── package.json
    ├── Dockerfile
    └── docker-compose.yml
```

---

## 2. vector-collection-test

### 2.1 개요

**목적**: 벡터 검색 품질 검증 도구

벡터 컬렉션에 저장된 데이터의 품질을 검증하는 스크립트입니다. 각 설비에 대해 벡터 검색을 수행하여 자기 자신이 1등으로 검색되는지 확인하고, 그렇지 않은 경우를 리포트로 출력합니다.

### 2.2 주요 기능

- **자동 검증**: 전체 설비를 대상으로 벡터 검색 수행
- **품질 평가**: 자기 자신이 Top-1인지 확인
- **리포트 생성**: 검증 실패 항목 리포트 출력
- **CSV 지원**: CSV 파일 기반 검증 지원

### 2.3 구성 파일

#### equipment_vector_validation.py

Oracle DB 연동 버전

```python
# 주요 설정
DB_CONFIG = {
    'host': '123.123.123.123',
    'port': 1522,
    'service_name': 'EESDB',
    'user': 'your_username',
    'password': 'your_password'
}

VECTOR_API_CONFIG = {
    'url': 'http://localhost:5200/search',
    'preset_id': 'ko-sbert',
    'top_k': 10,
    'threshold': 0.0,
    'qdrant': {
        'url': 'http://localhost:6333',
        'collection': 'your_collection_name'
    }
}
```

#### equipment_vector_validation_csv.py

CSV 파일 기반 버전 - DB 연결 없이 CSV 파일로 검증 가능

### 2.4 사용 방법

#### 단계 1: 설정 수정

스크립트 상단의 설정을 실제 환경에 맞게 수정합니다:

```python
# DB 연결 정보
DB_CONFIG = {
    'host': 'your_host',
    'port': 1521,
    'service_name': 'your_service',
    'user': 'your_user',
    'password': 'your_password'
}

# Vector API 설정
VECTOR_API_CONFIG = {
    'url': 'http://your-api:5200/search',
    'preset_id': 'your-model',  # bge-m3, ko-sbert 등
    'qdrant': {
        'url': 'http://your-qdrant:6333',
        'collection': 'your_collection'
    }
}
```

#### 단계 2: 실행

```bash
# Oracle DB 버전
python equipment_vector_validation.py

# CSV 버전
python equipment_vector_validation_csv.py
```

### 2.5 출력 예제

```
============================================================
설비 벡터 검색 검증 시작
============================================================

총 826개 설비 검증 시작...

[1/826] 검증 중: 설비A (ID: 001)
  ✅ 자기 자신이 1등 (score: 0.9876)

[2/826] 검증 중: 설비B (ID: 002)
  ❌ 자기 자신이 3등 (score: 0.8234)
  Top-1: 설비C (score: 0.9012)

...

============================================================
검증 완료
============================================================
총 검증: 826개
성공: 810개 (98.1%)
실패: 16개 (1.9%)

실패 목록:
1. 설비B (ID: 002) - 3등 (score: 0.8234)
2. 설비D (ID: 004) - 2등 (score: 0.8567)
...
```

### 2.6 활용 사례

- **품질 모니터링**: 벡터 임베딩 품질 확인
- **모델 비교**: 다른 임베딩 모델 성능 비교
- **데이터 검증**: 컬렉션 데이터 무결성 확인
- **정기 점검**: 주기적 품질 검증 자동화

---

## 3. vector-db2embed

### 3.1 개요

**목적**: Database → Text → Embedding → Qdrant 파이프라인

데이터베이스에서 데이터를 추출하여 텍스트로 변환하고, 임베딩 벡터를 생성한 후 Qdrant에 저장하는 올인원 Streamlit 애플리케이션입니다.

### 3.2 주요 기능

- **다중 DB 지원**: Oracle, MySQL, PostgreSQL, SQL Server
- **유연한 텍스트 변환**: Jinja2 템플릿 기반 텍스트 생성
- **임베딩 모델 선택**: 11가지 사전 설정 모델 지원
- **Qdrant 통합**: 자동 컬렉션 생성 및 벡터 업로드
- **배치 처리**: 대용량 데이터 효율적 처리
- **진행률 표시**: 실시간 처리 상태 모니터링
- **컬렉션 관리**: 컬렉션 생성, 삭제, 조회

### 3.3 시스템 구조

```
vector-db2embed/
├── streamlit_app.py          # 메인 애플리케이션
├── requirements.txt          # 의존성 패키지
├── config/
│   └── models_config.yaml    # 모델 설정
├── src/
│   ├── model_management/     # 임베딩 모델 관리
│   ├── services/             # 핵심 서비스
│   │   ├── database_service.py     # DB 연결
│   │   ├── qdrant_service.py       # Qdrant 통합
│   │   └── text_processor.py       # 텍스트 변환
│   ├── utils/                # 유틸리티
│   └── components/           # UI 컴포넌트
└── docker/                   # Docker 설정
```

### 3.4 설치 및 실행

#### 로컬 실행

```bash
cd tools/vector-db2embed

# 가상환경 생성 및 활성화
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt

# Streamlit 실행
streamlit run streamlit_app.py
```

#### Docker 실행

```bash
cd tools/vector-db2embed/docker

# Docker Compose로 실행
docker-compose up -d

# 로그 확인
docker-compose logs -f

# 중지
docker-compose down
```

애플리케이션 접속: http://localhost:8501

### 3.5 사용 방법

#### 단계 1: 데이터베이스 연결

1. **데이터베이스 타입 선택**: Oracle, MySQL, PostgreSQL, SQL Server
2. **연결 정보 입력**:
   - Host/Port
   - Database/Service Name
   - Username/Password
3. **연결 테스트**: "Test Connection" 버튼 클릭

#### 단계 2: 데이터 조회

```sql
-- SQL 쿼리 입력 예제
SELECT
    equipment_id,
    equipment_name,
    description,
    category
FROM equipment
WHERE status = 'ACTIVE'
```

- **쿼리 실행**: "Execute Query" 클릭
- **결과 확인**: 데이터 프리뷰 표시

#### 단계 3: 텍스트 변환 설정

Jinja2 템플릿으로 텍스트 생성:

```jinja2
{{ equipment_name }}
카테고리: {{ category }}
설명: {{ description }}
```

- **ID 컬럼**: 고유 식별자 컬럼 선택
- **템플릿 테스트**: 변환 결과 미리보기

#### 단계 4: 임베딩 모델 선택

```yaml
models:
  - preset_id: bge-m3
    backend: st
    name: ./models/bge-m3
    normalize: true

  - preset_id: ko-sroberta
    backend: st
    name: ./models/ko-sroberta
    normalize: true
```

사전 설정된 11개 모델 중 선택:
- **다국어**: bge-m3, mE5-small/base/large
- **한국어**: ko-sroberta, ko-simcse, kure-v1

#### 단계 5: Qdrant 설정

1. **Qdrant URL**: http://localhost:6333
2. **컬렉션 이름**: 새로운 또는 기존 컬렉션
3. **벡터 차원**: 모델에 따라 자동 설정

#### 단계 6: 처리 옵션

- **배치 크기**: 100-1000 (기본값: 100)
- **처리 방식**: 전체 처리 또는 샘플 테스트

#### 단계 7: 실행

"Start Processing" 버튼 클릭 후 진행률 모니터링:

```
Processing Progress:
████████████████████ 100% (826/826)

Statistics:
- Total records: 826
- Successfully processed: 826
- Failed: 0
- Processing time: 2m 34s
- Average time per record: 0.19s
```

### 3.6 지원 데이터베이스

| DB 타입 | 드라이버 | 연결 문자열 예제 |
|---------|---------|-----------------|
| Oracle | oracledb | oracle+oracledb://user:pass@host:1521/service |
| MySQL | pymysql | mysql+pymysql://user:pass@host:3306/db |
| PostgreSQL | psycopg2 | postgresql://user:pass@host:5432/db |
| SQL Server | pyodbc | mssql+pyodbc://user:pass@host/db?driver=... |

### 3.7 임베딩 모델 정보

| 모델 ID | 차원 | 언어 | 특징 |
|---------|------|------|------|
| bge-m3 | 1024 | 다국어 | 범용 고성능 |
| mE5-small | 384 | 다국어 | 경량 빠른 처리 |
| mE5-base | 768 | 다국어 | 균형잡힌 성능 |
| mE5-large | 1024 | 다국어 | 높은 정확도 |
| ko-sroberta | 768 | 한국어 | 한국어 특화 |
| ko-simcse | 768 | 한국어 | 대조 학습 |
| kure-v1 | 1024 | 한국어 | 한국어 SOTA |

### 3.8 활용 사례

- **신규 컬렉션 생성**: 처음으로 벡터 검색 시스템 구축
- **데이터 업데이트**: 기존 데이터 갱신 및 추가
- **모델 마이그레이션**: 다른 임베딩 모델로 재생성
- **A/B 테스트**: 여러 모델 성능 비교

---

## 4. web-test-tool

### 4.1 개요

**목적**: Vector Search API 웹 기반 테스트 도구

React + TypeScript로 구현된 Vector Search API의 모든 기능을 테스트할 수 있는 인터랙티브 웹 애플리케이션입니다.

### 4.2 주요 기능

- **API 엔드포인트 테스트**: /health, /models, /search
- **동적 API URL 설정**: 다양한 환경 지원
- **모델 선택**: 사전 설정 모델 또는 커스텀 모델
- **검색 파라미터 조정**: top_k, threshold, with_payload
- **Qdrant 필터링**: 복잡한 필터 조건 테스트
- **실시간 결과 표시**: 검색 결과 및 성능 메트릭
- **에러 처리**: 상세한 오류 메시지 표시

### 4.3 기술 스택

```json
{
  "프레임워크": "React 19.1.1",
  "언어": "TypeScript 5.8.3",
  "빌드도구": "Vite 7.1.6",
  "스타일링": "CSS",
  "배포": "Docker + Nginx"
}
```

### 4.4 설치 및 실행

#### 로컬 개발 모드

```bash
cd tools/web-test-tool

# 의존성 설치
npm install

# 개발 서버 실행
npm run dev

# 접속
# http://localhost:5173
```

#### 프로덕션 빌드

```bash
# 빌드
npm run build

# 빌드 결과 미리보기
npm run preview
```

#### Docker 실행

```bash
cd tools/web-test-tool

# Docker 이미지 빌드
docker build -t web-test-tool .

# 컨테이너 실행
docker run -p 8080:80 web-test-tool

# 또는 Docker Compose
docker-compose up -d
```

애플리케이션 접속: http://localhost:8080

### 4.5 사용 방법

#### 단계 1: API URL 설정

```
API Base URL: http://localhost:5200
```

- **기본값**: http://localhost:5200
- **커스텀 URL**: 원격 서버 주소 입력 가능

#### 단계 2: Health Check

"Check Health" 버튼 클릭:

```json
{
  "ok": true,
  "qdrant_url": "http://localhost:6333"
}
```

#### 단계 3: 모델 조회

"Load Models" 버튼 클릭하여 사용 가능한 모델 목록 표시:

```
Available Models:
- bge-m3 (backend: st, normalize: true)
- ko-sroberta (backend: st, normalize: true)
- mE5-large (backend: st, normalize: true)
```

#### 단계 4: 검색 파라미터 설정

**기본 파라미터**:
- **Query Text**: 검색할 텍스트 입력
- **Preset Model**: 모델 선택 (드롭다운)
- **Top K**: 결과 개수 (1-100)
- **Threshold**: 최소 점수 (0.0-1.0)

**Qdrant 설정**:
- **URL**: http://localhost:6333
- **Collection**: 컬렉션 이름

**고급 필터** (옵션):

```json
{
  "must": [
    {"key": "category", "match": {"value": "technology"}}
  ]
}
```

#### 단계 5: 검색 실행

"Search" 버튼 클릭 후 결과 확인:

```json
{
  "took_ms": 245,
  "model": {
    "backend": "st",
    "name": "./models/bge-m3"
  },
  "collection": "docs_2025",
  "total_candidates": 10,
  "hits": [
    {
      "id": "doc_001",
      "score": 0.8934,
      "payload": {
        "title": "인공지능 기술 동향",
        "content": "최신 AI 기술의 발전..."
      }
    }
  ]
}
```

### 4.6 UI 구성

```
┌────────────────────────────────────────────┐
│  Vector Search API Test Tool               │
├────────────────────────────────────────────┤
│  API Configuration                         │
│  ┌──────────────────────────────────────┐ │
│  │ Base URL: [http://localhost:5200  ] │ │
│  │ [Check Health]  [Load Models]       │ │
│  └──────────────────────────────────────┘ │
├────────────────────────────────────────────┤
│  Search Parameters                         │
│  ┌──────────────────────────────────────┐ │
│  │ Query: [인공지능 기술          ]    │ │
│  │ Model: [bge-m3 ▼]                   │ │
│  │ Top K: [5    ]  Threshold: [0.0   ] │ │
│  │                                      │ │
│  │ Qdrant URL: [http://localhost:6333] │ │
│  │ Collection: [docs_2025            ] │ │
│  │                                      │ │
│  │ Filter (JSON):                       │ │
│  │ ┌──────────────────────────────────┐ │ │
│  │ │ {                                │ │ │
│  │ │   "must": [...]                  │ │ │
│  │ │ }                                │ │ │
│  │ └──────────────────────────────────┘ │ │
│  │                                      │ │
│  │ [Search]                             │ │
│  └──────────────────────────────────────┘ │
├────────────────────────────────────────────┤
│  Results                                   │
│  ┌──────────────────────────────────────┐ │
│  │ Took: 245ms                          │ │
│  │ Total: 10 results                    │ │
│  │                                      │ │
│  │ 1. [0.893] 인공지능 기술 동향       │ │
│  │    최신 AI 기술의 발전...           │ │
│  │                                      │ │
│  │ 2. [0.867] 머신러닝 알고리즘        │ │
│  │    다양한 ML 기법 소개...           │ │
│  └──────────────────────────────────────┘ │
└────────────────────────────────────────────┘
```

### 4.7 Docker 배포

#### Dockerfile

```dockerfile
FROM node:18-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/nginx.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

#### docker-compose.yml

```yaml
version: '3.8'

services:
  web-test-tool:
    build: .
    ports:
      - "8080:80"
    environment:
      - NODE_ENV=production
    restart: unless-stopped
```

### 4.8 활용 사례

- **API 기능 테스트**: 개발 중 API 동작 확인
- **모델 성능 비교**: 여러 모델의 검색 품질 비교
- **필터 조건 실험**: 복잡한 필터 쿼리 테스트
- **데모 및 프레젠테이션**: 비기술적 이해관계자 대상 시연
- **통합 테스트**: 전체 시스템 엔드투엔드 테스트

---

## 다음 단계

도구 사용 중 문제가 발생하면 다음 문서를 참고하세요:

1. [Vector Search API 사용 가이드](02_how_to_use.md)
2. [설정 및 구성](03_setting_configuration.md)
3. [API 상세 레퍼런스](04_api_detail.md)
4. [문제 해결](02_how_to_use.md#6-문제-해결)

---

## 참고 자료

- **vector-collection-test**: Python Requests, OracleDB
- **vector-db2embed**: Streamlit Documentation, SQLAlchemy
- **web-test-tool**: React Documentation, Vite Guide
- Vector Search API: [GitHub Repository]
