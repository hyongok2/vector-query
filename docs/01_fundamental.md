# Vector Database 기초

이 문서는 Vector Database와 임베딩 모델에 대한 기본 개념과 학습 자료를 제공합니다.

## 목차

1. [Vector란 무엇인가?](#1-vector란-무엇인가)
2. [임베딩의 이해](#2-임베딩의-이해)
3. [Vector Database 소개](#3-vector-database-소개)
4. [임베딩 모델](#4-임베딩-모델)
5. [실제 활용 사례](#5-실제-활용-사례)
6. [학습 자료](#6-학습-자료)

---

## 1. Vector란 무엇인가?

### 1.1 기본 개념

**Vector(벡터)** 는 수학적으로 크기와 방향을 가진 값들의 배열입니다. AI/ML 맥락에서는 데이터를 숫자 배열로 표현한 것을 의미합니다.

```python
# 예시: 3차원 벡터
vector = [0.2, 0.5, 0.8]

# 실제 임베딩: 768차원 벡터 (BERT 모델 예시)
embedding = [0.023, -0.145, 0.892, ..., 0.234]  # 768개의 실수값
```

### 1.2 왜 Vector가 필요한가?

컴퓨터는 텍스트, 이미지, 음성을 직접 이해하지 못합니다. 이들을 숫자로 변환해야 비교, 검색, 분석이 가능합니다.

**전통적 방식 vs Vector 방식:**

| 비교 대상 | 전통적 키워드 검색 | Vector 검색 |
|----------|-----------------|------------|
| 검색어 | "강아지" | [0.2, 0.5, 0.8, ...] |
| 결과 | 정확히 "강아지" 포함 문서만 | "애완견", "반려동물", "puppy" 등 의미적으로 유사한 문서 |
| 장점 | 빠르고 정확함 | 의미 기반 검색 가능 |
| 단점 | 동의어/유의어 검색 불가 | 계산 비용이 높음 |

### 1.3 Vector 유사도 측정

두 벡터가 얼마나 비슷한지 측정하는 방법:

#### Cosine Similarity (코사인 유사도)

가장 널리 사용되는 방식으로, 두 벡터 사이의 각도를 측정합니다.

```python
import numpy as np

def cosine_similarity(vec1, vec2):
    """
    코사인 유사도: -1 ~ 1 사이 값
    1에 가까울수록 유사함
    """
    dot_product = np.dot(vec1, vec2)
    norm_a = np.linalg.norm(vec1)
    norm_b = np.linalg.norm(vec2)
    return dot_product / (norm_a * norm_b)

# 예시
vec_dog = [0.8, 0.2, 0.1]
vec_puppy = [0.7, 0.3, 0.1]  # 유사함
vec_car = [0.1, 0.2, 0.9]    # 다름

print(cosine_similarity(vec_dog, vec_puppy))  # 0.96 (매우 유사)
print(cosine_similarity(vec_dog, vec_car))    # 0.23 (다름)
```

#### Euclidean Distance (유클리드 거리)

두 점 사이의 직선 거리를 측정합니다.

```python
def euclidean_distance(vec1, vec2):
    """
    유클리드 거리: 0 이상의 값
    0에 가까울수록 유사함
    """
    return np.linalg.norm(np.array(vec1) - np.array(vec2))
```

#### Dot Product (내적)

두 벡터의 내적 값을 사용합니다.

```python
def dot_product(vec1, vec2):
    """
    내적: 클수록 유사함
    """
    return np.dot(vec1, vec2)
```

---

## 2. 임베딩의 이해

### 2.1 임베딩이란?

**임베딩(Embedding)** 은 텍스트, 이미지 등의 비정형 데이터를 고정된 크기의 벡터로 변환하는 과정입니다.

```text
텍스트: "안녕하세요"
    ↓ (임베딩 모델)
Vector: [0.234, -0.145, 0.892, ..., 0.456]  # 768차원
```

### 2.2 좋은 임베딩의 조건

1. **의미적 유사성 보존**: 비슷한 의미를 가진 텍스트는 벡터 공간에서도 가까이 위치
2. **차원의 적절성**: 너무 낮으면 정보 손실, 너무 높으면 계산 비용 증가
3. **도메인 적합성**: 사용할 분야에 맞는 학습 데이터로 훈련됨

### 2.3 임베딩의 특성

**벡터 공간에서의 관계:**

```text
King - Man + Woman ≈ Queen
Paris - France + Korea ≈ Seoul
```

이러한 관계성을 통해 의미적 연산이 가능합니다.

---

## 3. Vector Database 소개

### 3.1 Vector Database란?

**Vector Database** 는 고차원 벡터를 효율적으로 저장하고 검색하기 위해 최적화된 데이터베이스입니다.

### 3.2 전통적 DB vs Vector DB

| 특징 | 전통적 RDB | Vector DB |
|------|-----------|-----------|
| | (MySQL, PostgreSQL) | (Qdrant, Pinecone, Weaviate) |
| 데이터 타입 | 구조화된 데이터 (테이블, 행, 열) | 고차원 벡터 + 메타데이터 |
| 검색 방식 | 정확한 일치 (WHERE 조건) | 유사도 검색 (Similarity Search) |
| 인덱싱 | B-Tree, Hash | HNSW, IVF, Product Quantization |
| 주요 용도 | 트랜잭션, CRUD 작업 | 의미 검색, 추천 시스템, RAG |
| 확장성 | 수직 확장 위주 | 수평 확장 용이 |

### 3.3 Vector DB가 필요한 이유

1. **대규모 벡터 검색 최적화**: 수백만~수억 개의 벡터에서 빠른 검색
2. **메타데이터 필터링**: 벡터 검색 + 조건 필터링 동시 지원
3. **확장성**: 분산 환경에서의 효율적 운영
4. **실시간 업데이트**: 동적 데이터 추가/삭제

### 3.4 주요 Vector Database 비교

#### Qdrant (본 프로젝트 사용)

**선정 이유**: [Qdrant 선정 배경 문서](https://github.com/your-repo/docs/qdrant-selection.md) 참고

**특징:**

- Rust로 작성되어 고성능
- 풍부한 필터링 기능
- 완전한 오픈소스
- Docker 배포 용이
- gRPC/REST API 지원

**장점:**

```yaml
성능: 10M+ 벡터에서 <100ms 응답
필터링: 복잡한 메타데이터 조건 지원
배포: Docker/K8s 친화적
비용: 오픈소스, 자체 호스팅 가능
```

#### 타 Vector DB 비교

| DB | 장점 | 단점 | 적합한 사용 사례 |
|----|------|------|-----------------|
| **Pinecone** | 관리형 서비스, 사용 쉬움 | 비용 높음, 클라우드 전용 | 빠른 프로토타입, 관리 부담 최소화 |
| **Weaviate** | GraphQL 지원, 모듈화 | 복잡한 설정 | 지식 그래프 + 벡터 검색 |
| **Milvus** | 초대규모 확장성 | 운영 복잡도 높음 | 엔터프라이즈급 대규모 시스템 |
| **Chroma** | 경량, 간단함 | 프로덕션 기능 제한적 | 개발/테스트 환경 |
| **pgvector** | PostgreSQL 익스텐션 | 성능 제한적 | 기존 PostgreSQL 환경 활용 |

---

## 4. 임베딩 모델

### 4.1 임베딩 모델이란?

텍스트를 벡터로 변환하는 딥러닝 모델입니다.

### 4.2 주요 임베딩 모델

#### OpenAI Embeddings

```python
# text-embedding-3-small
# 차원: 1536
# 장점: 높은 품질, 다국어 지원
# 단점: API 비용, 인터넷 필요
# 용도: 프로덕션 RAG 시스템
```

#### Sentence Transformers (Hugging Face)

```python
# paraphrase-multilingual-mpnet-base-v2
# 차원: 768
# 장점: 무료, 오프라인 가능, 한국어 지원
# 단점: GPU 필요 (CPU 가능하나 느림)
# 용도: 자체 호스팅, 비용 절감
```

#### 한국어 특화 모델

| 모델 | 차원 | 특징 | 용도 |
|------|------|------|------|
| **jhgan/ko-sroberta-multitask** | 768 | 한국어 최적화 | 한국어 문서 검색 |
| **BM-K/KoSimCSE-roberta** | 768 | 한국어 문장 유사도 | 한국어 의미 검색 |
| **intfloat/multilingual-e5-large** | 1024 | 다국어 + 한국어 우수 | 다국어 환경 |

### 4.3 모델 선택 기준

```yaml
품질 우선:
  - OpenAI text-embedding-3-large (3072차원)
  - Cohere embed-multilingual-v3.0 (1024차원)

비용 절감:
  - Sentence Transformers (오픈소스)
  - Hugging Face 무료 모델

한국어 특화:
  - jhgan/ko-sroberta-multitask
  - BM-K/KoSimCSE-roberta

속도 중요:
  - text-embedding-3-small (1536차원)
  - all-MiniLM-L6-v2 (384차원, 빠름)
```

### 4.4 임베딩 모델 성능 비교

**MTEB 리더보드** (Massive Text Embedding Benchmark):

- <https://huggingface.co/spaces/mteb/leaderboard>

**한국어 벤치마크**:

- KLUE (Korean Language Understanding Evaluation)
- KorNLI (Korean Natural Language Inference)

---

## 5. 실제 활용 사례

### 5.1 RAG (Retrieval-Augmented Generation)

**LLM의 한계 극복:**

```text
문제: ChatGPT는 학습 데이터 이후 정보를 모름
해결: Vector DB에서 관련 문서 검색 → LLM에게 제공 → 답변 생성

[사용자 질문]
     ↓
[임베딩 모델] → 질문을 벡터로 변환
     ↓
[Vector DB] → 유사한 문서 검색
     ↓
[LLM] → 검색된 문서 + 질문 → 답변 생성
```

**예시:**

```python
# 질문: "2024년 회사 매출은?"
question_vector = embed("2024년 회사 매출은?")

# Vector DB에서 유사 문서 검색
results = qdrant.search(
    collection_name="company_docs",
    query_vector=question_vector,
    limit=5
)

# LLM에게 컨텍스트 제공
context = "\n".join([doc.text for doc in results])
prompt = f"다음 문서를 참고하여 답변하세요:\n{context}\n\n질문: 2024년 회사 매출은?"

answer = llm.generate(prompt)
```

### 5.2 시맨틱 검색 (Semantic Search)

**키워드 검색의 한계:**

```text
검색어: "저렴한 노트북"
전통적 검색: "저렴한", "노트북" 단어 포함 문서만
시맨틱 검색: "가성비 좋은 랩탑", "예산형 컴퓨터" 등도 검색
```

### 5.3 추천 시스템

```python
# 사용자가 좋아한 영화의 벡터
liked_movie_vector = embed("인셉션: 꿈속의 꿈, SF, 크리스토퍼 놀란")

# 유사한 영화 검색
recommendations = vector_db.search(
    query_vector=liked_movie_vector,
    filter={"genre": "SF"},  # 메타데이터 필터
    limit=10
)
```

### 5.4 중복 탐지

```python
# 새 문서 임베딩
new_doc_vector = embed(new_document)

# 유사도 높은 기존 문서 검색
similar_docs = vector_db.search(
    query_vector=new_doc_vector,
    limit=1
)

if similar_docs[0].score > 0.95:
    print("중복 문서 발견!")
```

### 5.5 다국어 검색

```python
# 한국어 질문
query_kr = embed("강아지 훈련 방법")

# 영어 문서도 검색 가능 (다국어 임베딩 모델 사용 시)
results = vector_db.search(query_kr)
# 결과: "How to train a puppy", "Dog training tips" 등
```

---

## 6. 학습 자료

### 6.1 공식 문서

**Qdrant:**

- [공식 문서](https://qdrant.tech/documentation/)
- [Python 클라이언트](https://github.com/qdrant/qdrant-client)
- [필터링 가이드](https://qdrant.tech/documentation/concepts/filtering/)

**임베딩 모델:**

- [Sentence Transformers](https://www.sbert.net/)
- [Hugging Face Hub](https://huggingface.co/models?pipeline_tag=sentence-similarity)
- [OpenAI Embeddings](https://platform.openai.com/docs/guides/embeddings)

### 6.2 튜토리얼

**초급:**

1. [Vector Database 시작하기](https://qdrant.tech/documentation/quick-start/)
2. [첫 번째 RAG 시스템 만들기](https://python.langchain.com/docs/use_cases/question_answering/)

**중급:**

1. [임베딩 모델 파인튜닝](https://www.sbert.net/docs/training/overview.html)
2. [Qdrant 필터링 마스터하기](https://qdrant.tech/documentation/concepts/filtering/)

**고급:**

1. [대규모 Vector DB 최적화](https://qdrant.tech/documentation/guides/optimize/)
2. [프로덕션 RAG 시스템 구축](https://www.pinecone.io/learn/series/rag/)

### 6.3 추천 강의

- [Deeplearning.AI - Vector Databases](https://www.deeplearning.ai/short-courses/vector-databases-embeddings-applications/)
- [Hugging Face - NLP Course](https://huggingface.co/learn/nlp-course/)

### 6.4 커뮤니티

- [Qdrant Discord](https://qdrant.to/discord)
- [Hugging Face Forums](https://discuss.huggingface.co/)
- [r/MachineLearning](https://www.reddit.com/r/MachineLearning/)

### 6.5 논문 및 기술 자료

**핵심 논문:**

- "Attention Is All You Need" (Transformer 원리)
- "BERT: Pre-training of Deep Bidirectional Transformers"
- "Sentence-BERT: Sentence Embeddings using Siamese BERT-Networks"

**벤치마크:**

- [MTEB Leaderboard](https://huggingface.co/spaces/mteb/leaderboard)
- [BEIR Benchmark](https://github.com/beir-cellar/beir)

---

## 다음 단계

이 문서를 읽었다면:

1. [사용 방법](02_how_to_use.md) - 실제 코드 예시와 사용법
2. [설정 방법](03_setting_configuration.md) - 실제 코드 예시와 사용법
3. [API 상세](04_api_detail.md) - API 엔드포인트 레퍼런스
4. [아키텍처](05_architecture.md) - 시스템 구조 이해
5. [배포 가이드](06_deployment.md) - 프로덕션 배포 방법
6. [도구 소개](07_about_tools.md) - 관련 도구 및 유틸리티

---

## 참고 자료

- [Qdrant 선정 배경](../why-qdrant.md)
- [프로젝트 버전 히스토리](../version_history.md)
- [릴리즈 노트](../release_notes/)
