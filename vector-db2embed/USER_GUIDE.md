# DB to Embedding to Qdrant 사용자 가이드

## 📌 개요
이 애플리케이션은 데이터베이스의 데이터를 텍스트로 변환하고, 임베딩 벡터로 변환한 후 Qdrant 벡터 DB에 저장하는 도구입니다.

## 🚀 빠른 시작

### 1. DB 연결 설정
```
DB URI 예시:
- Oracle: oracle+oracledb://username:password@localhost:1521/?service_name=XEPDB1
- MySQL: mysql+pymysql://username:password@localhost:3306/database
- PostgreSQL: postgresql://username:password@localhost:5432/database
- SQLite: sqlite:///path/to/database.db
```

### 2. 기본 워크플로우
1. DB URI 입력
2. SQL 쿼리 작성
3. 텍스트 템플릿 설정
4. 임베딩 모델 선택
5. Qdrant 연결 정보 입력
6. "✨ 임베딩 & 업서트 실행" 클릭

## 📝 SQL 쿼리 작성 가이드

### 기본 쿼리
```sql
-- 모든 데이터 가져오기
SELECT * FROM table_name

-- 특정 컬럼만 선택
SELECT id, title, description FROM table_name
```

### 조건 필터링 (WHERE 절)
```sql
-- 단일 조건
SELECT * FROM products WHERE status = 'active'

-- 여러 조건 (AND)
SELECT * FROM products
WHERE status = 'active'
  AND price >= 1000

-- 여러 조건 (OR)
SELECT * FROM products
WHERE category = 'A'
   OR category = 'B'

-- 복합 조건
SELECT * FROM products
WHERE status = 'active'
  AND (category = 'A' OR category = 'B')
  AND price BETWEEN 1000 AND 5000
```

### 유용한 필터 패턴
```sql
-- 텍스트 검색 (LIKE)
SELECT * FROM articles WHERE title LIKE '%AI%'
SELECT * FROM articles WHERE content LIKE '%machine learning%'

-- NULL 값 처리
SELECT * FROM users WHERE email IS NOT NULL
SELECT * FROM users WHERE deleted_at IS NULL

-- 날짜 범위
SELECT * FROM orders WHERE created_at >= '2024-01-01'
SELECT * FROM orders WHERE created_at BETWEEN '2024-01-01' AND '2024-12-31'

-- IN 연산자 (여러 값 중 하나)
SELECT * FROM products WHERE category IN ('A', 'B', 'C')
SELECT * FROM orders WHERE status IN ('pending', 'processing')

-- 정렬과 제한
SELECT * FROM products ORDER BY created_at DESC LIMIT 100
SELECT TOP 100 * FROM products ORDER BY price DESC  -- SQL Server
```

## 🎨 텍스트 템플릿 (Jinja2)

### 기본 사용법
템플릿은 DB의 컬럼명을 `{{컬럼명}}` 형식으로 참조합니다.

```jinja2
{{title}} - {{description}}
```

### 고급 템플릿 예시

#### 1. 단순 조합
```jinja2
{{id}}: {{title}} - {{description}}
```

#### 2. 조건부 텍스트
```jinja2
{{title}}{% if category %} [{{category}}]{% endif %} - {{description}}
```

#### 3. 여러 필드 조합
```jinja2
제품명: {{product_name}}
카테고리: {{category}}
가격: {{price}}원
설명: {{description}}
```

#### 4. 날짜 포맷팅
```jinja2
{{title}} (작성일: {{created_at}})
{{content}}
```

#### 5. NULL 값 처리
```jinja2
{{title|default('제목 없음')}} - {{description|default('설명 없음')}}
```

#### 6. 문자열 조작
```jinja2
{{title|upper}} - {{description|truncate(100)}}
```

### 템플릿 필터 (자주 사용)
- `|upper` - 대문자 변환
- `|lower` - 소문자 변환
- `|title` - 제목 형식 (각 단어 첫글자 대문자)
- `|truncate(100)` - 100자로 자르기
- `|default('기본값')` - NULL일 때 기본값
- `|trim` - 앞뒤 공백 제거

## ⚙️ 설정 옵션

### 미리보기 행 수
- 화면에 표시할 데이터 개수
- 10~1000 사이 설정 가능
- 기본값: 50

### 처리 최대 행 수
- 실제로 임베딩할 데이터 개수 제한
- 0 = 제한 없음 (전체 처리)
- 대용량 데이터 테스트 시 유용

### 원본 PK 컬럼명
- 데이터 업데이트 시 기준이 되는 고유 식별자
- 예: `id`, `product_id`, `article_no`
- 같은 PK의 데이터가 변경되면 자동으로 벡터 업데이트

### 청킹 최대 문자 수
- 긴 텍스트를 여러 조각으로 나누는 기준
- 200~3000자 설정 가능
- 임베딩 모델의 최대 입력 길이 고려

### 배치 크기
- 한 번에 처리할 텍스트 개수
- 메모리와 성능의 균형 고려
- 기본값: 64

## 💾 설정 저장
- 💾 버튼 클릭으로 현재 설정 저장
- F5 새로고침해도 설정 유지
- 사용자별로 개별 저장 (IP 기반)

## 🔄 데이터 업데이트
PK 컬럼을 설정하면 같은 PK의 데이터가 변경될 때 자동으로 업데이트됩니다.

예시:
1. 첫 실행: `id=1, title="원본 제목"` → 벡터 생성
2. 재실행: `id=1, title="수정된 제목"` → 기존 벡터 덮어쓰기

## 📊 임베딩 모델
각 모델은 고정된 벡터 차원을 가집니다:
- **bge-m3**: 1024차원 (다국어)
- **mE5-base**: 768차원 (다국어)
- **mE5-small**: 384차원 (다국어, 빠름)
- **paraphrase-ml**: 384차원 (다국어)
- 한국어 특화 모델들도 지원

## 🎯 활용 예시

### 1. 제품 검색 시스템
```sql
SELECT product_id, name, category, description, price
FROM products
WHERE status = 'active' AND stock > 0
```
템플릿:
```jinja2
{{name}} ({{category}}) - {{description}} 가격: {{price}}원
```

### 2. FAQ 시스템
```sql
SELECT id, question, answer, category
FROM faq
WHERE published = true
```
템플릿:
```jinja2
Q: {{question}}
A: {{answer}}
카테고리: {{category}}
```

### 3. 문서 검색
```sql
SELECT doc_id, title, content, author, created_at
FROM documents
WHERE deleted_at IS NULL
ORDER BY created_at DESC
```
템플릿:
```jinja2
{{title}} by {{author}}
{{content}}
```

## ❗ 주의사항
1. 대용량 데이터는 "처리 최대 행 수"로 제한하여 테스트
2. 민감한 정보가 포함된 컬럼은 SELECT에서 제외
3. 텍스트가 너무 길면 청킹 크기 조정
4. DB 연결 정보는 보안 주의

## 🔧 문제 해결
- **연결 실패**: DB URI 형식과 네트워크 확인
- **임베딩 실패**: 텍스트가 비어있는지 확인
- **Qdrant 오류**: 호스트/포트 확인, 컬렉션 이름 확인
- **메모리 부족**: 배치 크기 줄이기