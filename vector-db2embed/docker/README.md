배포 시 docker compose 파일과 같은 경로에

config 폴더 그리고 내부에 models_config.yaml 파일이 필요합니다.
models 폴더도 필요하고, 위 config에 기입된 embedding model 파일들이 있어야 합니다.

## 실행 방법
```bash
docker-compose up -d
```

## 접속
- **애플리케이션**: http://localhost:5260
- **Qdrant**: http://localhost:6333 (별도 실행 필요)