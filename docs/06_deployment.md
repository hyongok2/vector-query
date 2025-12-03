# Vector Search API 배포 가이드

이 문서는 Vector Search API를 프로덕션 환경에 배포하는 방법을 설명합니다.

## 목차

1. [배포 전 체크리스트](#1-배포-전-체크리스트)
2. [로컬 개발 환경](#2-로컬-개발-환경)
3. [Docker 배포](#3-docker-배포)
4. [프로덕션 배포](#4-프로덕션-배포)
5. [모니터링 및 로깅](#5-모니터링-및-로깅)
6. [성능 최적화](#6-성능-최적화)
7. [보안 강화](#7-보안-강화)
8. [트러블슈팅](#8-트러블슈팅)

---

## 1. 배포 전 체크리스트

### 1.1 필수 확인 사항

#### 환경 요구사항

- [ ] Python 3.9 이상 설치
- [ ] Docker 20.10 이상 설치 (컨테이너 배포 시)
- [ ] Qdrant 서버 실행 중
- [ ] 충분한 디스크 공간 (모델 저장용 20GB+)
- [ ] 충분한 메모리 (최소 8GB, 권장 16GB+)

#### 설정 파일

- [ ] `.env` 파일 생성 및 설정
- [ ] `config/models_config.yaml` 검토
- [ ] API 키 설정 (프로덕션 필수)
- [ ] CORS 도메인 설정

#### 모델 준비

- [ ] 필요한 임베딩 모델 다운로드
- [ ] 모델 파일 경로 확인
- [ ] 모델 로드 테스트

#### 보안

- [ ] API 키 생성 및 안전한 저장
- [ ] HTTPS 인증서 준비 (프로덕션)
- [ ] 방화벽 규칙 설정
- [ ] 민감 정보 로그 제외 확인

### 1.2 성능 테스트

```bash
# Health check
curl http://localhost:5200/health

# 모델 로드 테스트
curl http://localhost:5200/models

# 검색 테스트
curl -X POST http://localhost:5200/search \
  -H "Content-Type: application/json" \
  -d '{
    "text": "테스트 쿼리",
    "preset_id": "bge-m3",
    "qdrant": {
      "url": "http://localhost:6333",
      "collection": "test_collection"
    }
  }'
```

---

## 2. 로컬 개발 환경

### 2.1 가상환경 설정

```bash
# 가상환경 생성
python -m venv venv

# 활성화 (Windows)
venv\Scripts\activate

# 활성화 (Linux/Mac)
source venv/bin/activate

# 의존성 설치
pip install -r requirements.txt
```

### 2.2 환경 변수 설정

`.env` 파일 생성:

```bash
# 기본 설정
QDRANT_URL=http://localhost:6333
DEFAULT_COLLECTION=docs_2025
ALLOW_MODELS=all

# 개발 모드 설정
API_KEY=
CORS_ALLOW_ORIGINS=*
DEVICE=auto
TORCH_NUM_THREADS=4

# 로깅
LOG_LEVEL=INFO
```

### 2.3 로컬 실행

```bash
# 개발 서버 실행
python main.py

# 또는 Uvicorn 직접 실행 (리로드 기능)
uvicorn app.api:app --host 0.0.0.0 --port 5200 --reload
```

### 2.4 개발 도구

#### API 문서 확인

- Swagger UI: http://localhost:5200/docs
- ReDoc: http://localhost:5200/redoc
- OpenAPI JSON: http://localhost:5200/openapi.json

#### 디버깅

```python
# main.py에 디버그 모드 추가
import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "app.api:app",
        host="0.0.0.0",
        port=5200,
        reload=True,  # 코드 변경 시 자동 재시작
        log_level="debug"  # 상세 로그
    )
```

---

## 3. Docker 배포

### 3.1 Docker 이미지 빌드

#### Dockerfile 확인

```dockerfile
# vector-search-api/Dockerfile
FROM python:3.11-slim

WORKDIR /app

# 의존성 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 코드 복사
COPY . .

# 포트 노출
EXPOSE 5200

# 실행
CMD ["python", "main.py"]
```

#### 이미지 빌드

```bash
cd vector-search-api

# 이미지 빌드
docker build -t vector-search-api:v1.0.2 .

# 빌드 확인
docker images | grep vector-search-api
```

### 3.2 Docker Compose 배포

#### docker-compose.yml

```yaml
version: '3.8'

services:
  vector-api:
    image: vector-search-api:v1.0.2
    container_name: vector-search-api
    ports:
      - "5200:5200"
    environment:
      - QDRANT_URL=http://qdrant:6333
      - DEFAULT_COLLECTION=docs_2025
      - ALLOW_MODELS=all
      - API_KEY=${API_KEY}
      - CORS_ALLOW_ORIGINS=*
      - DEVICE=auto
      - TORCH_NUM_THREADS=4
    volumes:
      - ./models:/app/models:ro
      - ./config:/app/config:ro
      - ./logs:/app/logs
    restart: unless-stopped
    depends_on:
      - qdrant
    networks:
      - vector-network

  qdrant:
    image: qdrant/qdrant:v1.7.4
    container_name: qdrant
    ports:
      - "6333:6333"
      - "6334:6334"
    volumes:
      - qdrant_storage:/qdrant/storage
    restart: unless-stopped
    networks:
      - vector-network

volumes:
  qdrant_storage:
    driver: local

networks:
  vector-network:
    driver: bridge
```

#### 실행

```bash
# 환경 변수 파일 생성
echo "API_KEY=your-secret-key-here" > .env

# 컨테이너 시작
docker-compose up -d

# 로그 확인
docker-compose logs -f vector-api

# 상태 확인
docker-compose ps

# 중지
docker-compose down
```

### 3.3 Docker 최적화

#### 멀티스테이지 빌드

```dockerfile
# 빌드 스테이지
FROM python:3.11-slim AS builder

WORKDIR /app

COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# 실행 스테이지
FROM python:3.11-slim

WORKDIR /app

# 빌드 스테이지에서 설치한 패키지 복사
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

COPY . .

EXPOSE 5200

CMD ["python", "main.py"]
```

#### 이미지 크기 최적화

```bash
# 불필요한 파일 제외 (.dockerignore)
cat > .dockerignore << EOF
__pycache__
*.pyc
*.pyo
*.pyd
.git
.gitignore
.env
.venv
venv/
.pytest_cache
.coverage
*.log
EOF

# 이미지 크기 확인
docker images vector-search-api:v1.0.2
```

---

## 4. 프로덕션 배포

### 4.1 AWS 배포 (ECS Fargate)

#### ECR에 이미지 푸시

```bash
# ECR 로그인
aws ecr get-login-password --region ap-northeast-2 | \
  docker login --username AWS --password-stdin \
  123456789012.dkr.ecr.ap-northeast-2.amazonaws.com

# 이미지 태깅
docker tag vector-search-api:v1.0.2 \
  123456789012.dkr.ecr.ap-northeast-2.amazonaws.com/vector-search-api:v1.0.2

# 이미지 푸시
docker push \
  123456789012.dkr.ecr.ap-northeast-2.amazonaws.com/vector-search-api:v1.0.2
```

#### ECS 태스크 정의 (JSON)

```json
{
  "family": "vector-search-api",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "2048",
  "memory": "4096",
  "containerDefinitions": [
    {
      "name": "vector-api",
      "image": "123456789012.dkr.ecr.ap-northeast-2.amazonaws.com/vector-search-api:v1.0.2",
      "portMappings": [
        {
          "containerPort": 5200,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "QDRANT_URL",
          "value": "http://qdrant.internal:6333"
        },
        {
          "name": "DEFAULT_COLLECTION",
          "value": "docs_2025"
        }
      ],
      "secrets": [
        {
          "name": "API_KEY",
          "valueFrom": "arn:aws:secretsmanager:ap-northeast-2:123456789012:secret:vector-api-key"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/vector-search-api",
          "awslogs-region": "ap-northeast-2",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

#### ALB 설정

```bash
# 타겟 그룹 생성
aws elbv2 create-target-group \
  --name vector-api-tg \
  --protocol HTTP \
  --port 5200 \
  --vpc-id vpc-xxxxxx \
  --target-type ip \
  --health-check-path /health

# 리스너 규칙 추가
aws elbv2 create-rule \
  --listener-arn arn:aws:elasticloadbalancing:... \
  --priority 100 \
  --conditions Field=path-pattern,Values='/search*' \
  --actions Type=forward,TargetGroupArn=arn:aws:elasticloadbalancing:...
```

### 4.2 GCP 배포 (Cloud Run)

#### 이미지 빌드 및 푸시

```bash
# GCP 프로젝트 설정
gcloud config set project your-project-id

# Artifact Registry에 이미지 푸시
gcloud builds submit --tag gcr.io/your-project-id/vector-search-api:v1.0.2

# 또는 Docker로 직접 푸시
docker tag vector-search-api:v1.0.2 gcr.io/your-project-id/vector-search-api:v1.0.2
docker push gcr.io/your-project-id/vector-search-api:v1.0.2
```

#### Cloud Run 배포

```bash
gcloud run deploy vector-search-api \
  --image gcr.io/your-project-id/vector-search-api:v1.0.2 \
  --platform managed \
  --region asia-northeast1 \
  --port 5200 \
  --memory 4Gi \
  --cpu 2 \
  --min-instances 1 \
  --max-instances 10 \
  --set-env-vars QDRANT_URL=http://qdrant:6333,DEFAULT_COLLECTION=docs_2025 \
  --set-secrets API_KEY=vector-api-key:latest \
  --allow-unauthenticated
```

### 4.3 Kubernetes 배포

#### Deployment YAML

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: vector-search-api
  namespace: production
spec:
  replicas: 3
  selector:
    matchLabels:
      app: vector-search-api
  template:
    metadata:
      labels:
        app: vector-search-api
    spec:
      containers:
      - name: vector-api
        image: vector-search-api:v1.0.2
        ports:
        - containerPort: 5200
        env:
        - name: QDRANT_URL
          value: "http://qdrant-service:6333"
        - name: DEFAULT_COLLECTION
          value: "docs_2025"
        - name: API_KEY
          valueFrom:
            secretKeyRef:
              name: vector-api-secret
              key: api-key
        resources:
          requests:
            memory: "4Gi"
            cpu: "2000m"
          limits:
            memory: "8Gi"
            cpu: "4000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 5200
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 5200
          initialDelaySeconds: 10
          periodSeconds: 5
        volumeMounts:
        - name: models
          mountPath: /app/models
          readOnly: true
      volumes:
      - name: models
        persistentVolumeClaim:
          claimName: models-pvc
---
apiVersion: v1
kind: Service
metadata:
  name: vector-search-api
  namespace: production
spec:
  selector:
    app: vector-search-api
  ports:
  - port: 80
    targetPort: 5200
  type: LoadBalancer
```

#### 배포

```bash
# Secret 생성
kubectl create secret generic vector-api-secret \
  --from-literal=api-key=your-secret-key \
  -n production

# 배포
kubectl apply -f deployment.yaml

# 상태 확인
kubectl get pods -n production
kubectl get svc -n production

# 로그 확인
kubectl logs -f deployment/vector-search-api -n production
```

---

## 5. 모니터링 및 로깅

### 5.1 로깅 설정

#### 구조화된 로깅

```python
# app/logging_config.py
import logging
import json
from datetime import datetime

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }

        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data)

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('/app/logs/app.log')
    ]
)

for handler in logging.root.handlers:
    handler.setFormatter(JSONFormatter())
```

#### API 요청 로깅

```python
# app/middleware.py
import time
import logging
from fastapi import Request

logger = logging.getLogger(__name__)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()

    response = await call_next(request)

    duration = time.time() - start_time

    logger.info(
        "API Request",
        extra={
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "duration_ms": duration * 1000,
            "client_ip": request.client.host
        }
    )

    return response
```

### 5.2 메트릭 수집

#### Prometheus 메트릭

```python
# requirements.txt에 추가
# prometheus-client==0.19.0

# app/metrics.py
from prometheus_client import Counter, Histogram, Gauge, generate_latest
from fastapi import Response

# 메트릭 정의
request_count = Counter(
    'api_requests_total',
    'Total API requests',
    ['method', 'endpoint', 'status']
)

request_duration = Histogram(
    'api_request_duration_seconds',
    'API request duration',
    ['method', 'endpoint']
)

model_load_time = Histogram(
    'model_load_duration_seconds',
    'Model loading duration',
    ['model_name']
)

active_requests = Gauge(
    'api_active_requests',
    'Number of active requests'
)

# 메트릭 엔드포인트
@app.get("/metrics")
async def metrics():
    return Response(
        content=generate_latest(),
        media_type="text/plain"
    )
```

#### 메트릭 수집 미들웨어

```python
@app.middleware("http")
async def prometheus_middleware(request: Request, call_next):
    active_requests.inc()

    start_time = time.time()

    response = await call_next(request)

    duration = time.time() - start_time

    request_count.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code
    ).inc()

    request_duration.labels(
        method=request.method,
        endpoint=request.url.path
    ).observe(duration)

    active_requests.dec()

    return response
```

### 5.3 모니터링 대시보드

#### Prometheus 설정 (prometheus.yml)

```yaml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'vector-search-api'
    static_configs:
      - targets: ['vector-api:5200']
    metrics_path: '/metrics'
```

#### Grafana 대시보드

주요 메트릭:
- 요청 수 (QPS)
- 응답 시간 (P50, P95, P99)
- 에러 비율
- 모델 로드 시간
- 메모리 사용량
- CPU 사용량

---

## 6. 성능 최적화

### 6.1 모델 최적화

#### GPU 사용

```bash
# .env 설정
DEVICE=cuda
TORCH_NUM_THREADS=8

# Docker에서 GPU 사용
docker run --gpus all \
  -e DEVICE=cuda \
  vector-search-api:v1.0.2
```

#### 모델 캐싱

```yaml
# config/models_config.yaml
settings:
  cache_models: true
  max_cached_models: 3
  preload_models:
    - bge-m3
    - ko-sroberta
```

### 6.2 리소스 최적화

#### 메모리 제한

```yaml
# docker-compose.yml
services:
  vector-api:
    deploy:
      resources:
        limits:
          memory: 8G
        reservations:
          memory: 4G
```

#### CPU 최적화

```bash
# 스레드 수 조정
TORCH_NUM_THREADS=4
OMP_NUM_THREADS=4
```

### 6.3 캐싱 전략

#### Redis 결과 캐싱

```python
# app/cache.py
import redis
import hashlib
import json

redis_client = redis.Redis(
    host='localhost',
    port=6379,
    decode_responses=True
)

def cache_key(text: str, preset_id: str) -> str:
    data = f"{text}:{preset_id}"
    return hashlib.md5(data.encode()).hexdigest()

def get_cached_result(text: str, preset_id: str):
    key = cache_key(text, preset_id)
    result = redis_client.get(key)
    return json.loads(result) if result else None

def set_cached_result(text: str, preset_id: str, result, ttl=3600):
    key = cache_key(text, preset_id)
    redis_client.setex(key, ttl, json.dumps(result))
```

---

## 7. 보안 강화

### 7.1 HTTPS 설정

#### Nginx 리버스 프록시

```nginx
# nginx.conf
server {
    listen 443 ssl http2;
    server_name api.example.com;

    ssl_certificate /etc/ssl/certs/cert.pem;
    ssl_certificate_key /etc/ssl/private/key.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    location / {
        proxy_pass http://vector-api:5200;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 7.2 Rate Limiting

```python
# requirements.txt에 추가
# slowapi==0.1.9

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.post("/search")
@limiter.limit("100/minute")
async def search_vectors(request: Request, req: SearchRequest):
    # ...
```

### 7.3 API 키 관리

#### AWS Secrets Manager

```python
import boto3
import json

def get_api_key():
    client = boto3.client('secretsmanager', region_name='ap-northeast-2')

    response = client.get_secret_value(SecretId='vector-api-key')
    secret = json.loads(response['SecretString'])

    return secret['api_key']

API_KEY = get_api_key()
```

---

## 8. 트러블슈팅

### 8.1 일반적인 문제

#### 메모리 부족

증상:
```
RuntimeError: CUDA out of memory
```

해결:
```bash
# 작은 모델 사용
PRESET_ID=mE5-small

# 배치 크기 줄이기
BATCH_SIZE=32

# 캐시 모델 수 제한
MAX_CACHED_MODELS=1
```

#### Qdrant 연결 실패

증상:
```
Qdrant connection failed: Connection refused
```

해결:
```bash
# Qdrant 상태 확인
curl http://localhost:6333/health

# Docker 네트워크 확인
docker network inspect vector-network

# Qdrant 재시작
docker-compose restart qdrant
```

#### 모델 로드 느림

증상:
- 첫 요청 응답 시간 > 30초

해결:
```yaml
# config/models_config.yaml
settings:
  preload_models:
    - bge-m3  # 시작 시 미리 로드
  cache_models: true
```

### 8.2 성능 문제

#### 응답 시간 느림

진단:
```bash
# 프로파일링
python -m cProfile -o profile.stats main.py

# 결과 분석
python -c "import pstats; p = pstats.Stats('profile.stats'); p.sort_stats('cumulative').print_stats(20)"
```

최적화:
- GPU 사용
- 배치 처리
- 결과 캐싱
- 모델 사전 로드

### 8.3 로그 분석

```bash
# 에러 로그 확인
docker-compose logs vector-api | grep ERROR

# 응답 시간 분석
cat logs/app.log | jq 'select(.duration_ms > 1000)'

# 에러 집계
cat logs/app.log | jq -r 'select(.level == "ERROR") | .message' | sort | uniq -c
```

---

## 다음 단계

1. [사용 가이드](02_how_to_use.md) - API 사용 방법
2. [설정 구성](03_setting_configuration.md) - 환경 변수 및 모델 설정
3. [아키텍처](05_architecture.md) - 시스템 구조 이해

---

## 참고 자료

- Docker Best Practices: <https://docs.docker.com/develop/dev-best-practices/>
- Kubernetes Deployment: <https://kubernetes.io/docs/concepts/workloads/controllers/deployment/>
- AWS ECS: <https://docs.aws.amazon.com/ecs/>
- GCP Cloud Run: <https://cloud.google.com/run/docs>
- Prometheus: <https://prometheus.io/docs/>
- Grafana: <https://grafana.com/docs/>
