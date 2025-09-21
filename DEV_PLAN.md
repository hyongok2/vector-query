# 0) 목표 & 범위 (MVP)

* **목표**: 로컬 무료 임베딩 모델 기반의 의미 검색 서비스
* **범위**:

  * **A. Search WebAPI**: 입력 텍스트 → 임베딩 → Qdrant 질의 → 결과 반환
  * **B. WebUI**: 사용자가 모델/호스트/컬렉션/쿼리 설정 → API 호출 → 결과 시각화
* **비범위(후속)**: 대량 인덱싱 서비스(파일 업로드/청킹/업서트), 재랭킹, 하이브리드 검색 등

---

# 1) 시스템 구성도(논리)

```
[User] ──(브라우저)──> [WebUI] ──HTTP──> [Search WebAPI] ──> [Embedder(local)]
                                                    └──> [Qdrant(Vector DB)]
```

* WebUI는 **API 클라이언트** 역할만 수행(상태 없음, 결과 표시 전용)
* WebAPI는 **임베딩 + Qdrant 질의**를 담당(단일 책임)

---

# 2) 공통 설계 원칙

* **모델/호스트/컬렉션/TopK/필터**를 모두 **요청에 명시** → 환경 종속 최소화
* **로컬 무료 임베딩 우선**(fastembed/BGE/E5 등), 필요 시 ST 백엔드 옵션
* **버전 호환성**: Qdrant는 `query_points(query=…, query_filter=…)` 형태 기준
* **보안 최소치**: 사내용 API Key 헤더(옵션), CORS 허용 범위 제한
* **관찰성**: 요청-응답 latency(ms), 모델명, 컬렉션, TopK, 결과 개수 로깅

---

# 3) 데이터 모델(요청/응답) – 추상 스키마

## A) `/search` 요청

* **필수**

  * `text`: 검색 질의 문자열
  * `qdrant.url`: Qdrant 호스트 (예: `http://localhost:6333`)
  * `qdrant.collection`: 검색할 컬렉션
* **옵션**

  * `top_k`(기본 5), `threshold`(기본 0.0), `with_payload`(기본 true)
  * `qdrant.query_filter`: Qdrant 필터(예: `source == "xxx.pdf"`)
  * `model`: `backend`(fastembed|st), `name`(예 `BAAI/bge-m3`), `normalize`(bool)

## A) `/search` 응답

* `took_ms`, `model`, `collection`, `hits[]`

  * `hit`: `{ id, score, payload? }`
  * `payload`에는 인덱싱 시 저장한 `text`, `page`, `source`, `tags` 등이 포함

## B) `/models` (옵션)

* 사용 가능 모델 목록(화이트리스트) 반환

## B) `/health`

* 단순 상태 확인

---

# 4) 임베딩 설계

* **기본 백엔드**: `fastembed` (로컬, 가벼움, PyTorch 불필요)

  * **기본 모델 후보**:

    * `BAAI/bge-m3`(다국어/성능 우수),
    * `BAAI/bge-small-en-v1.5`(경량),
    * `intfloat/multilingual-e5-small`(다국어, E5 포맷 필요)
* **프롬프트 규칙**:

  * **BGE**: 쿼리/패시지 구분 없이 입력해도 무난(모델별 권장 프롬프트 문서 추후 반영)
  * **E5**: `query: ...` / `passage: ...` 명시 필요(일관성 위해 API 내부에서 선택적 전처리 플래그)
* **정규화**: 코사인 거리 기준 `normalize_embeddings=True` 유지
* **모델 로딩**: **LRU 캐시**(key=`backend+name`)로 재사용

---

# 5) Qdrant 질의 설계

* **API 호출 전 검증**: 컬렉션 존재 확인(없으면 404 반환)
* **검색 메서드**: `query_points(collection, query=vec, query_filter=…, limit=…, with_payload=…)`
* **필터 설계**: payload 키(`source`, `tags`, `dept` 등)로 must/should 조합
* **스코어 임계치**: `threshold`로 저관련 결과 필터링
* **추후 확장**:

  * 재랭킹(CrossEncoder) 단계 추가(옵션)
  * 다중 컬렉션 라우팅(사이드카)
  * sparse + dense 하이브리드

---

# 6) WebUI 설계 (평가 전용)

* **입력 요소**

  * API URL, API Key(옵션), Qdrant URL, Collection
  * 모델 선택(드롭다운), TopK, Threshold
  * Source 필터(선택), 쿼리 텍스트 입력
* **출력 요소**

  * took(ms), 모델/컬렉션 정보
  * 결과 테이블: `score`, `page`, `source`, `text(앞부분)`
  * 하이라이트(간단 토큰 매칭) 옵션
* **행동**

  * “Search” 버튼 → `/search` POST 호출 → 테이블 갱신
  * 오류 시 상태코드·메시지 표시

---

# 7) 설정 & 배포

* **환경변수(.env)**

  * `QDRANT_URL`, `DEFAULT_COLLECTION`, `DEFAULT_MODEL`, `ALLOW_MODELS`, `API_KEY`, `CORS_ALLOW_ORIGINS`
* **프로세스 구성**

  * WebAPI: Uvicorn 단독(초기 1 worker), CPU 기준
  * WebUI: Streamlit/단일 프로세스
* **Docker Compose(권장)**

  * `qdrant` 서비스 + `api` + `ui` (동일 네트워크)
  * API는 `qdrant:6333`에 붙고, UI는 `api:8080`에 호출
* **운영 체크**

  * 로그: 요청/응답 시간, 예외, 모형명, 요청 파라미터
  * 헬스체크: `/health`

---

# 8) 테스트 전략

* **기능 테스트**: 샘플 PDF 2\~3개 인덱싱 → 동일 쿼리에서 기대 문단 상위 노출 확인
* **부하/성능**: 1\~10QPS에서 p50/p95 latency 바운드 측정(임베딩/네트워크/Qdrant 분리 측정)
* **호환성**: 모델별(BGE/E5) 프롬프트 차이로 정확도 변화 확인
* **에러 케이스**: 컬렉션 없음/모델 미허용/필수 필드 누락/필터 오류/타임아웃

---

# 9) 보안 & 권한 (사내 전제)

* **API Key 헤더(X-API-Key)**: 사내망 한정이라도 최소 적용 권장
* **CORS 제한**: UI 도메인만 허용(또는 내부망)
* **데이터 민감도**: payload에 PII 저장 금지(필요 시 마스킹/익명화)

---

# 10) 로드맵(우선순위)

1. **MVP**: `/search` + WebUI 연결(단일 컬렉션, fastembed 기본)
2. **모델 옵션화**: ST 백엔드 선택 지원(토치 설치 환경에서만 노출)
3. **재랭킹**: CrossEncoder로 Top-20→Top-5 재정렬(정확도↑)
4. **하이라이트 고도화**: 문장 단위 스니펫/키워드 강조
5. **인덱싱 서비스 분리**: 파일 업로드→청킹→업서트 API/워커
6. **하이브리드 검색**: Sparse + Dense 결합 랭킹
7. **멀티테넌시/ACL**: 팀별 컬렉션/태그 기반 접근 제어

---

# 11) 위험 요소 & 대응

* **모델 성능 편차**: 문서/언어별 적합 모델 사전 검증 → 기본 모델 가이드 제공
* **버전 호환(Qdrant/클라이언트)**: API 래퍼로 인터페이스 고정, 호환성 테스트
* **임베딩 지연**: 캐시/사전 워밍업, 경량 모델 기본값 제공, 필요 시 GPU 옵션
* **필터 오사용**: UI에서 필터 빌더 제공(키/연산자/값 검증)
