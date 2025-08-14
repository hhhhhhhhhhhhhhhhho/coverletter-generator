# 🚀 빠른 시작 가이드

이 가이드는 AI 커버레터 생성기를 Docker로 빠르게 실행하는 방법을 설명합니다.

## 📋 사전 요구사항

- Docker 20.10+
- Docker Compose 2.0+
- OpenAI API 키

## ⚡ 5분 만에 실행하기

### 1. 저장소 클론
```bash
git clone https://github.com/hhhhhhhhhhhhhhhhho/coverletter-generator.git
cd coverletter-generator
```

### 2. 환경 변수 설정
```bash
# 환경 변수 파일 복사
cp env.example .env

# .env 파일을 편집하여 OpenAI API 키 설정
# nano .env 또는 원하는 편집기 사용
```

`.env` 파일에서 다음을 설정하세요:
```env
OPENAI_API_KEY=your_actual_openai_api_key_here
```

### 3. Docker로 실행
```bash
# 모든 서비스 빌드 및 실행
docker-compose up -d
```

### 4. 접속
브라우저에서 다음 주소로 접속하세요:
- **애플리케이션**: http://localhost
- **API 문서**: http://localhost:8000/docs

## 🔧 기본 명령어

```bash
# 서비스 상태 확인
docker-compose ps

# 로그 확인
docker-compose logs -f

# 서비스 중지
docker-compose down

# 서비스 재시작
docker-compose restart
```

## 🛠️ Makefile 사용 (선택사항)

Makefile을 사용하면 더 편리하게 관리할 수 있습니다:

```bash
# 도움말 보기
make help

# 빌드 및 실행
make build
make up

# 로그 확인
make logs

# 서비스 중지
make down

# 데이터 백업
make backup
```

## 🔍 문제 해결

### 포트 충돌
포트 80이나 8000이 이미 사용 중인 경우:
```bash
# 사용 중인 포트 확인
lsof -i :80
lsof -i :8000

# 다른 포트로 변경하려면 docker-compose.yml 수정
```

### 메모리 부족
Docker 컨테이너에 메모리 부족 오류가 발생하는 경우:
```bash
# Docker 리소스 증가 (Docker Desktop 설정에서)
# 또는 컨테이너 재시작
docker-compose restart
```

### API 키 오류
OpenAI API 키가 올바르지 않은 경우:
```bash
# 환경 변수 확인
docker-compose exec backend env | grep OPENAI

# 컨테이너 재시작
docker-compose restart backend
```

## 📊 모니터링

### 헬스체크
```bash
# 서비스 상태 확인
curl http://localhost:8000/health
curl http://localhost/health
```

### 리소스 사용량
```bash
# 컨테이너 리소스 사용량 확인
docker stats
```

## 🗂️ 데이터 관리

### 데이터 백업
```bash
# 모든 데이터 백업
make backup
```

### 데이터 복원
```bash
# 백업에서 복원 (필요시)
# backups/YYYYMMDD_HHMMSS/ 디렉토리의 파일들을 사용
```

## 🔒 보안 고려사항

- `.env` 파일에 API 키를 안전하게 보관하세요
- 프로덕션 환경에서는 HTTPS를 사용하세요
- 정기적으로 데이터를 백업하세요

## 📞 지원

문제가 발생하면 다음을 확인하세요:
1. Docker와 Docker Compose가 올바르게 설치되어 있는지
2. OpenAI API 키가 유효한지
3. 포트가 사용 가능한지
4. 충분한 디스크 공간이 있는지

추가 도움이 필요하면 GitHub Issues를 이용해주세요.
