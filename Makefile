# Docker Compose 명령어들
.PHONY: help build up down logs clean restart status

# 기본 명령어
help: ## 사용 가능한 명령어들을 보여줍니다
	@echo "사용 가능한 명령어들:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# 빌드 및 실행
build: ## Docker 이미지들을 빌드합니다
	docker-compose build

up: ## 애플리케이션을 시작합니다
	docker-compose up -d

down: ## 애플리케이션을 중지합니다
	docker-compose down

restart: ## 애플리케이션을 재시작합니다
	docker-compose restart

# 로그 및 상태
logs: ## 모든 서비스의 로그를 보여줍니다
	docker-compose logs -f

logs-backend: ## 백엔드 로그만 보여줍니다
	docker-compose logs -f backend

logs-frontend: ## 프론트엔드 로그만 보여줍니다
	docker-compose logs -f frontend

status: ## 컨테이너 상태를 확인합니다
	docker-compose ps

# 개발용 명령어
dev: ## 개발 모드로 실행 (로그 표시)
	docker-compose up

dev-build: ## 개발 모드로 빌드 후 실행
	docker-compose up --build

# 정리
clean: ## 모든 컨테이너, 이미지, 볼륨을 정리합니다
	docker-compose down -v --rmi all --remove-orphans

clean-volumes: ## 볼륨만 정리합니다
	docker-compose down -v

# 개별 서비스 관리
build-backend: ## 백엔드만 빌드합니다
	docker-compose build backend

build-frontend: ## 프론트엔드만 빌드합니다
	docker-compose build frontend

up-backend: ## 백엔드만 시작합니다
	docker-compose up -d backend

up-frontend: ## 프론트엔드만 시작합니다
	docker-compose up -d frontend

# 헬스체크
health: ## 서비스 헬스체크를 확인합니다
	@echo "백엔드 헬스체크:"
	@curl -f http://localhost:8000/health || echo "백엔드가 응답하지 않습니다"
	@echo "프론트엔드 헬스체크:"
	@curl -f http://localhost/health || echo "프론트엔드가 응답하지 않습니다"

# 환경 설정
setup: ## 초기 설정을 수행합니다
	@echo "환경 변수 파일을 설정해주세요:"
	@echo "cp env.example .env"
	@echo "그리고 .env 파일에서 OPENAI_API_KEY를 설정해주세요"

# 프로덕션 배포
prod: ## 프로덕션 모드로 실행
	docker-compose -f docker-compose.yml up -d

# 백업 및 복원
backup: ## 데이터 백업
	@echo "데이터 백업을 시작합니다..."
	@mkdir -p backups/$(shell date +%Y%m%d_%H%M%S)
	@docker run --rm -v coverletter-generator_uploads_data:/data -v $(PWD)/backups/$(shell date +%Y%m%d_%H%M%S):/backup alpine tar czf /backup/uploads.tar.gz -C /data .
	@docker run --rm -v coverletter-generator_job_postings_data:/data -v $(PWD)/backups/$(shell date +%Y%m%d_%H%M%S):/backup alpine tar czf /backup/job_postings.tar.gz -C /data .
	@docker run --rm -v coverletter-generator_cover_letters_data:/data -v $(PWD)/backups/$(shell date +%Y%m%d_%H%M%S):/backup alpine tar czf /backup/cover_letters.tar.gz -C /data .
	@docker run --rm -v coverletter-generator_chroma_db_data:/data -v $(PWD)/backups/$(shell date +%Y%m%d_%H%M%S):/backup alpine tar czf /backup/chroma_db.tar.gz -C /data .
	@echo "백업이 완료되었습니다: backups/$(shell date +%Y%m%d_%H%M%S)/"
