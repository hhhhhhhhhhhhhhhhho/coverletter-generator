# 🐳 Docker 컨테이너화 가이드

이 문서는 AI 커버레터 생성기의 Docker 컨테이너화 구조와 구현 방법을 상세히 설명합니다.

## 📋 목차

1. [전체 아키텍처](#전체-아키텍처)
2. [컨테이너 구조](#컨테이너-구조)
3. [네트워크 구성](#네트워크-구성)
4. [볼륨 관리](#볼륨-관리)
5. [환경 변수](#환경-변수)
6. [빌드 프로세스](#빌드-프로세스)
7. [배포 전략](#배포-전략)
8. [모니터링 및 로깅](#모니터링-및-로깅)
9. [보안 고려사항](#보안-고려사항)
10. [성능 최적화](#성능-최적화)

## 🏗️ 전체 아키텍처

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           Docker Architecture                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌────────────────────────────────────────────────────────────────────┐     │
│  │                    Frontend Container                              │     │
│  │  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐             │     │
│  │  │   React     │    │   Nginx     │    │   Static    │             │     │
│  │  │   Build     │───▶│   Server    │───▶│   Files     │             │     │
│  │  │             │    │   (Port 80) │    │             │             │     │
│  │  └─────────────┘    └─────────────┘    └─────────────┘             │     │
│  └────────────────────────────────────────────────────────────────────┘     │
│                                    │                                        │
│                                    │ HTTP/API Requests                      │
│                                    ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                    Backend Container                                │    │
│  │  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐              │    │
│  │  │   FastAPI   │    │   Python    │    │   AI/ML     │              │    │
│  │  │   Server    │───▶│   Runtime   │───▶│   Pipeline  │              │    │
│  │  │ (Port 8000) │    │             │    │             │              │    │
│  │  └─────────────┘    └─────────────┘    └─────────────┘              │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                    │                                        │
│                                    │ Data Persistence                       │
│                                    ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                    Docker Volumes                                   │    │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐ │    │
│  │  │   uploads   │  │job_postings │  │cover_letters│  │ chroma_db   │ │    │
│  │  │   _data     │  │   _data     │  │   _data     │  │   _data     │ │    │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘ │    │
│  └─────────────────────────────────────────────────────────────────────┘    │ 
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## 📦 컨테이너 구조

### Frontend Container (`coverletter-frontend`)

#### 멀티스테이지 빌드 구조
```dockerfile
# Stage 1: Build Stage
FROM node:18-alpine as build
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
RUN npm run build

# Stage 2: Production Stage
FROM nginx:alpine
COPY nginx.conf /etc/nginx/nginx.conf
COPY --from=build /app/build /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

#### 특징
- **Node.js 18 Alpine**: 가벼운 Node.js 런타임
- **Nginx**: 고성능 웹 서버 및 리버스 프록시
- **정적 파일 서빙**: React 빌드 결과물을 효율적으로 서빙
- **API 프록시**: `/api/*` 요청을 백엔드로 전달

#### Nginx 설정
```nginx
# API 요청을 백엔드로 프록시
location /api/ {
    proxy_pass http://backend:8000/api/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}

# SPA 라우팅 지원
location / {
    try_files $uri $uri/ /index.html;
}
```

### Backend Container (`coverletter-backend`)

#### 단일 스테이지 빌드
```dockerfile
FROM python:3.11-slim
WORKDIR /app

# 시스템 패키지 설치
RUN apt-get update && apt-get install -y \
    gcc g++ && rm -rf /var/lib/apt/lists/*

# Python 의존성 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 코드 복사
COPY . .

# 필요한 디렉토리 생성
RUN mkdir -p uploads job_postings cover_letters

EXPOSE 8000
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### 특징
- **Python 3.11 Slim**: 최적화된 Python 런타임
- **FastAPI**: 고성능 웹 프레임워크
- **Uvicorn**: ASGI 서버
- **의존성 관리**: requirements.txt 기반 패키지 설치

## 🌐 네트워크 구성

### Docker Network
```yaml
networks:
  coverletter-network:
    driver: bridge
```

#### 네트워크 토폴로지
```
┌─────────────────────────────────────────────────────────────┐
│                    coverletter-network                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐                    ┌─────────────┐         │
│  │  Frontend   │◄──────────────────►│   Backend   │         │
│  │  10.0.0.2   │     HTTP/API       │  10.0.0.3   │         │
│  │   Port 80   │                    │  Port 8000  │         │
│  └─────────────┘                    └─────────────┘         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

#### 통신 흐름
1. **외부 요청** → Frontend Container (Port 80)
2. **API 요청** → Frontend Nginx → Backend Container (Port 8000)
3. **정적 파일** → Frontend Nginx → Static Files
4. **헬스체크** → 각 컨테이너의 헬스체크 엔드포인트

## 💾 볼륨 관리

### 볼륨 구조
```yaml
volumes:
  uploads_data:
    driver: local
  job_postings_data:
    driver: local
  cover_letters_data:
    driver: local
  chroma_db_data:
    driver: local
```

### 볼륨 마운트
```yaml
volumes:
  - uploads_data:/app/uploads
  - job_postings_data:/app/job_postings
  - cover_letters_data:/app/cover_letters
  - chroma_db_data:/app/chroma_db
```

### 데이터 영속성 전략
```
┌─────────────────────────────────────────────────────────────┐
│                    Data Persistence                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │
│  │   uploads   │  │job_postings │  │cover_letters│          │
│  │   _data     │  │   _data     │  │   _data     │          │
│  │             │  │             │  │             │          │
│  │ PDF Files   │  │ Job Data    │  │ Cover       │          │
│  │ Temp Files  │  │ Metadata    │  │ Letters     │          │
│  └─────────────┘  └─────────────┘  └─────────────┘          │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐    │
│  │              chroma_db_data                         │    │
│  │                                                     │    │
│  │ Vector Embeddings                                   │    │
│  │ Document Indexes                                    │    │
│  │ Metadata Storage                                    │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 백업 전략
```bash
# 자동 백업 스크립트
make backup
# → backups/YYYYMMDD_HHMMSS/ 디렉토리에 압축 파일 생성
```

## 🔧 환경 변수

### 환경 변수 구조
```yaml
environment:
  - OPENAI_API_KEY=${OPENAI_API_KEY}
  - PYTHONPATH=/app
  - PYTHONUNBUFFERED=1
```

### 환경 변수 파일 (.env)
```env
# OpenAI API 설정
OPENAI_API_KEY=your_openai_api_key_here

# 애플리케이션 설정
APP_ENV=production
DEBUG=false

# 포트 설정
BACKEND_PORT=8000
FRONTEND_PORT=80

# 로깅 설정
LOG_LEVEL=INFO
```

### 환경 변수 관리 전략
- **개발 환경**: `.env` 파일 사용
- **프로덕션 환경**: Docker Secrets 또는 환경 변수 주입
- **보안**: API 키는 환경 변수로 분리

## 🔨 빌드 프로세스

### Frontend 빌드 프로세스
```
1. Node.js Alpine 이미지 다운로드
2. package.json 복사 및 의존성 설치
3. 소스 코드 복사
4. npm run build 실행
5. Nginx Alpine 이미지로 전환
6. 빌드 결과물을 Nginx로 복사
7. Nginx 설정 파일 복사
8. 최종 이미지 생성
```

### Backend 빌드 프로세스
```
1. Python 3.11 Slim 이미지 다운로드
2. 시스템 패키지 업데이트 및 설치
3. requirements.txt 복사 및 Python 패키지 설치
4. 애플리케이션 코드 복사
5. 필요한 디렉토리 생성
6. 환경 변수 설정
7. 최종 이미지 생성
```

### .dockerignore 최적화
```
# 제외되는 파일들
- Git 관련 파일들
- 캐시 디렉토리들
- 가상환경
- IDE 설정 파일들
- 로그 파일들
- 임시 파일들
- AI 도구 관련 파일들
- 개인 파일들
```

## 🚀 배포 전략

### 개발 환경
```bash
# 개발 모드 실행
make dev

# 로그 실시간 확인
make logs
```

### 프로덕션 환경
```bash
# 프로덕션 모드 실행
make prod

# 백그라운드 실행
docker-compose up -d
```

### 스케일링 전략
```yaml
# docker-compose.override.yml (개발용)
services:
  backend:
    deploy:
      replicas: 1
  frontend:
    deploy:
      replicas: 1

# docker-compose.prod.yml (프로덕션용)
services:
  backend:
    deploy:
      replicas: 3
      resources:
        limits:
          memory: 2G
        reservations:
          memory: 1G
  frontend:
    deploy:
      replicas: 2
```

## 📊 모니터링 및 로깅

### 헬스체크
```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 40s
```

### 로깅 전략
```yaml
# Nginx 로그
access_log /var/log/nginx/access.log main;
error_log /var/log/nginx/error.log;

# Python 로그
logging:
  level: INFO
  format: '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
```

### 모니터링 명령어
```bash
# 컨테이너 상태 확인
docker-compose ps

# 리소스 사용량 확인
docker stats

# 로그 확인
docker-compose logs -f

# 헬스체크 확인
curl http://localhost:8000/health
curl http://localhost/health
```

## 🔒 보안 고려사항

### 컨테이너 보안
```dockerfile
# 비루트 사용자 실행
RUN addgroup -g 1001 -S nodejs
RUN adduser -S nextjs -u 1001
USER nextjs

# 최소 권한 원칙
RUN chmod 755 /app
RUN chown -R nextjs:nodejs /app
```

### 네트워크 보안
```yaml
# 네트워크 격리
networks:
  coverletter-network:
    driver: bridge
    internal: true  # 외부 접근 제한
```

### 환경 변수 보안
```bash
# 민감한 정보는 환경 변수로 관리
export OPENAI_API_KEY="your-secret-key"
docker-compose up -d
```

### 이미지 보안
```bash
# 베이스 이미지 정기 업데이트
docker pull python:3.11-slim
docker pull node:18-alpine
docker pull nginx:alpine

# 취약점 스캔
docker scan coverletter-backend
docker scan coverletter-frontend
```

## ⚡ 성능 최적화

### 이미지 크기 최적화
```dockerfile
# 멀티스테이지 빌드로 최종 이미지 크기 감소
# 불필요한 파일 제거
# 레이어 캐싱 최적화
```

### 빌드 캐싱
```yaml
# Docker BuildKit 사용
DOCKER_BUILDKIT=1 docker-compose build

# 캐시 활용
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
```

### 리소스 제한
```yaml
services:
  backend:
    deploy:
      resources:
        limits:
          memory: 2G
          cpus: '1.0'
        reservations:
          memory: 1G
          cpus: '0.5'
```

### Nginx 최적화
```nginx
# Gzip 압축
gzip on;
gzip_vary on;
gzip_min_length 1024;
gzip_comp_level 6;

# 캐시 설정
location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
    expires 1y;
    add_header Cache-Control "public, immutable";
}
```

## 🔧 문제 해결

### 일반적인 문제들

#### 포트 충돌
```bash
# 사용 중인 포트 확인
lsof -i :80
lsof -i :8000

# 포트 변경
docker-compose up -p 8080:80 -p 8081:8000
```

#### 메모리 부족
```bash
# Docker 리소스 증가
# Docker Desktop → Settings → Resources → Memory

# 컨테이너 재시작
docker-compose restart
```

#### 권한 문제
```bash
# 볼륨 권한 수정
sudo chown -R $USER:$USER ./uploads
sudo chown -R $USER:$USER ./job_postings
```

#### 네트워크 문제
```bash
# 네트워크 재생성
docker-compose down
docker network prune
docker-compose up
```

## 📈 확장성 고려사항

### 수평 확장
```yaml
# 백엔드 서비스 확장
docker-compose up --scale backend=3

# 로드 밸런서 추가
services:
  nginx-lb:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx-lb.conf:/etc/nginx/nginx.conf
```

### 수직 확장
```yaml
# 리소스 증가
services:
  backend:
    deploy:
      resources:
        limits:
          memory: 4G
          cpus: '2.0'
```

### 데이터베이스 분리
```yaml
# 외부 데이터베이스 연결
services:
  backend:
    environment:
      - DATABASE_URL=postgresql://user:pass@host:5432/db
```

이 문서는 Docker 컨테이너화의 모든 측면을 다루며, 개발자들이 시스템을 이해하고 유지보수할 수 있도록 도와줍니다.
