# Vector Search Tester - Docker 배포 가이드

Vector Search API를 위한 웹 테스트 도구의 Docker 배포 가이드입니다.

## 🚀 빠른 시작

### 1. Docker Compose로 실행

```bash
# 프로젝트 빌드 및 실행
docker-compose up -d

# 로그 확인
docker-compose logs -f

# 중지
docker-compose down
```

### 2. Docker로 직접 실행

```bash
# 이미지 빌드
docker build -t vector-search-tester .

# 컨테이너 실행
docker run -d \
  --name vector-search-tester \
  -p 3000:80 \
  vector-search-tester

# 로그 확인
docker logs -f vector-search-tester

# 중지 및 제거
docker stop vector-search-tester
docker rm vector-search-tester
```

## 📋 접속 정보

- **웹 인터페이스**: http://localhost:3000
- **헬스체크**: http://localhost:3000/health

## 🔧 설정

### 환경 변수

| 변수명 | 기본값 | 설명 |
|--------|---------|------|
| `NODE_ENV` | `production` | 실행 환경 |

### 포트 설정

기본적으로 컨테이너는 80포트에서 실행되며, 호스트의 3000포트로 매핑됩니다.

다른 포트를 사용하려면:

```bash
# 8080 포트로 변경
docker-compose up -d -p 8080:80
```

또는 `docker-compose.yml`에서 포트를 수정:

```yaml
ports:
  - "8080:80"  # 호스트:컨테이너
```

## 🏗️ 빌드 과정

1. **빌드 스테이지** (Node.js 18 Alpine)
   - 의존성 설치
   - TypeScript/React 앱 빌드

2. **프로덕션 스테이지** (Nginx Alpine)
   - 빌드된 정적 파일 복사
   - Nginx 설정 적용
   - 80포트로 서비스

## 📊 성능 최적화

### Nginx 설정 특징

- **Gzip 압축**: 텍스트 파일 압축으로 전송량 감소
- **캐싱**: 정적 자원의 브라우저 캐싱 설정
- **SPA 라우팅**: React Router 지원
- **보안 헤더**: XSS, CSRF 방어 헤더 추가

### 이미지 크기 최적화

- **멀티 스테이지 빌드**: 최종 이미지에서 빌드 도구 제외
- **Alpine Linux**: 경량 베이스 이미지 사용
- **.dockerignore**: 불필요한 파일 제외

## 🔍 트러블슈팅

### 컨테이너가 시작되지 않는 경우

```bash
# 로그 확인
docker-compose logs vector-search-tester

# 컨테이너 상태 확인
docker ps -a

# 포트 충돌 확인
netstat -tulpn | grep :3000
```

### 빌드 실패 시

```bash
# 캐시 없이 다시 빌드
docker-compose build --no-cache

# 또는 Docker로 직접
docker build --no-cache -t vector-search-tester .
```

### API 연결 문제

웹 테스트 도구가 API 서버에 연결할 수 없는 경우:

1. **네트워크 확인**: API 서버가 같은 Docker 네트워크에 있는지 확인
2. **호스트 접근**: API 서버가 호스트에서 실행되는 경우 `host.docker.internal` 사용
3. **방화벽**: 컨테이너에서 호스트로의 연결 허용 확인

```bash
# API 서버가 호스트에서 실행되는 경우
# 웹 앱에서 다음 URL 사용
http://host.docker.internal:5200
```

## 🔄 업데이트

새 버전 배포:

```bash
# 코드 변경 후 재빌드
docker-compose build

# 무중단 업데이트
docker-compose up -d
```

## 🐳 Docker Hub 배포

이미지를 Docker Hub에 푸시하려면:

```bash
# 태그 지정
docker tag vector-search-tester username/vector-search-tester:latest

# 푸시
docker push username/vector-search-tester:latest
```

## 📝 추가 설정

### SSL/HTTPS 설정

프로덕션 환경에서 HTTPS를 사용하려면 `docker-compose.yml`의 주석된 nginx-proxy 섹션을 활성화하거나 별도의 리버스 프록시를 설정하세요.

### 모니터링

Prometheus와 Grafana를 추가하여 모니터링 설정이 가능합니다:

```yaml
# docker-compose.yml에 추가
  prometheus:
    image: prom/prometheus
    ports:
      - "9090:9090"
    # 설정 생략...
```

## 🎯 프로덕션 배포

프로덕션 환경에서는:

1. **환경별 설정 파일** 분리
2. **시크릿 관리** (Docker Secrets 또는 외부 시크릿 관리 도구)
3. **로그 관리** (ELK Stack 또는 클라우드 로깅)
4. **모니터링** (Prometheus, Grafana)
5. **백업 전략** 수립
