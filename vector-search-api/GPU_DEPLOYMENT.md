# GPU 배포 전략 가이드

GPU 가속을 위한 배포 옵션과 전략

## 🎯 핵심 전략

### 1. Requirements 분기 전략

**현재 (CPU)**: `requirements.txt`
**GPU용**: `requirements-gpu.txt` 생성

```bash
# requirements-gpu.txt
torch==2.8.0+cu121  # CUDA 12.1 버전
torchvision==0.18.0+cu121
# ... 나머지 패키지들은 동일
```

### 2. Dockerfile 멀티 스테이지

```dockerfile
# === GPU 버전 ===
FROM nvidia/cuda:12.1-runtime-ubuntu22.04 as gpu-base
# GPU 의존성 설치
COPY requirements-gpu.txt .
RUN pip install -r requirements-gpu.txt

# === CPU 버전 ===
FROM python:3.11-slim as cpu-base
COPY requirements.txt .
RUN pip install -r requirements.txt

# === 최종 스테이지 ===
FROM ${BASE_IMAGE:-cpu-base} as final
# 공통 설정들...
```

### 3. Docker Compose 환경별 분리

**CPU 배포**: `docker-compose.yml` (현재)
**GPU 배포**: `docker-compose.gpu.yml`

```yaml
# docker-compose.gpu.yml
services:
  vector-api:
    build:
      context: .
      dockerfile: Dockerfile
      args:
        BASE_IMAGE: gpu-base
    runtime: nvidia  # NVIDIA Container Runtime
    environment:
      - NVIDIA_VISIBLE_DEVICES=all
      - DEVICE=cuda
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
```

## 🚀 배포 옵션

### Option 1: 빌드 타임 선택
```bash
# CPU 빌드 (기본)
docker-compose up -d

# GPU 빌드
docker-compose -f docker-compose.gpu.yml up -d
```

### Option 2: 런타임 환경변수
```bash
# 단일 Dockerfile, 환경변수로 제어
ENV DEVICE=auto  # auto|cpu|cuda|mps
```

### Option 3: 별도 이미지 태그
```bash
# CPU 이미지
docker build -t vector-api:cpu .

# GPU 이미지
docker build -t vector-api:gpu -f Dockerfile.gpu .
```

## 🛠️ 구현 우선순위

### 1단계: Requirements 분리
- [x] `requirements.txt` (CPU, 현재)
- [ ] `requirements-gpu.txt` 생성

### 2단계: Docker 설정
- [ ] `Dockerfile.gpu` 또는 멀티스테이지 추가
- [ ] `docker-compose.gpu.yml` 생성

### 3단계: 환경 감지
```python
# app/config.py 수정
def get_device():
    if device_config == "auto":
        return "cuda" if torch.cuda.is_available() else "cpu"
    return device_config
```

### 4단계: 문서화
- [ ] README.md에 GPU 배포 섹션 추가
- [ ] 성능 벤치마크 추가

## 📋 체크리스트

### 인프라 준비
- [ ] NVIDIA Docker Runtime 설치
- [ ] CUDA 12.1+ 드라이버 확인
- [ ] GPU 메모리 용량 확인 (모델당 2-8GB)

### 코드 수정
- [ ] `requirements-gpu.txt` 생성
- [ ] `Dockerfile.gpu` 생성
- [ ] `docker-compose.gpu.yml` 생성
- [ ] 환경변수 `DEVICE=cuda` 설정

### 테스트
- [ ] GPU 감지 확인: `torch.cuda.is_available()`
- [ ] 메모리 사용량 모니터링
- [ ] 성능 벤치마크 (CPU vs GPU)

## 🎁 추가 최적화

### 모델 최적화
```python
# 더 큰 배치 사이즈 활용
BATCH_SIZE = 32 if device == "cuda" else 8

# 혼합 정밀도 (FP16)
model.half() if device == "cuda" else model.float()
```

### 메모리 관리
```python
# GPU 메모리 정리
if device == "cuda":
    torch.cuda.empty_cache()
```

## 💡 권장사항

1. **점진적 전환**: CPU → GPU 환경 단계적 마이그레이션
2. **환경 분리**: 개발(CPU), 운영(GPU) 환경 구분
3. **모니터링**: GPU 메모리/사용률 대시보드 구축
4. **비용 최적화**: 필요 시에만 GPU 인스턴스 활성화

**결론**: 현재 CPU 버전을 유지하면서 GPU 옵션을 추가하는 하이브리드 전략 권장