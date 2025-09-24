# Vector Search API

벡터 검색 API 서버 - FastAPI 기반의 임베딩 및 벡터 검색 서비스

## 주요 기능

- 다양한 임베딩 모델 지원 (한국어 특화 모델 포함)
- Qdrant 벡터 데이터베이스 통합
- RESTful API 제공
- Docker 컨테이너 지원
- 볼륨 마운트 기반 모델 관리

## 시작하기

### 1. 환경 설정

```bash
# 환경 변수 파일 생성
cp .env.example .env

# Python 가상 환경 생성 및 활성화
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt
```

### 2. 모델 다운로드

```bash
# 모델 다운로드 스크립트 실행
cd download
python download_models.py
```

### 3. 실행

#### 로컬 실행
```bash
python main.py
```

#### Docker Compose 실행
```bash
docker-compose up -d
```

## 새 모델 추가 가이드

새로운 임베딩 모델을 추가하려면 다음 단계를 따르세요:

### 1. 모델 다운로드

config - models_config.yaml 파일 추가 반영
```yaml
  ko-e5:
    backend: st
    path: ./models/ko-e5
    normalize: true
    e5_mode: auto
    description: "Korean E5 model, requires query/passage prefixes"
    dimension: 1024
```

다운로드 실행:
```bash
cd download
python download_models.py
```

### 2. 검증

서버 재시작 후 새 모델 확인:

```bash
# 사용 가능한 모델 목록 확인
curl http://localhost:5200/models


## API 엔드포인트

### 모델 관련

- `GET /models` - 사용 가능한 모델 목록 조회

### 벡터 검색

- `POST /search` - 벡터 검색 수행

### 상태 확인

- `GET /health` - 서버 상태 확인

## Docker 볼륨 구조

```
./models/           # 로컬 모델 디렉토리 (읽기 전용 마운트)
├── bge-m3/
├── mE5-base/
├── ko-sbert/
└── ...

/app/models/        # 컨테이너 내부 경로
```

## 주의사항

1. **모델 크기**: 각 모델은 수백 MB ~ 수 GB의 용량을 차지합니다
2. **메모리 사용**: 여러 모델 동시 로드 시 메모리 사용량이 증가합니다
3. **초기 로딩**: 첫 요청 시 모델 로딩으로 지연이 발생할 수 있습니다
4. **볼륨 권한**: Docker 사용 시 모델 디렉토리 읽기 권한 확인

