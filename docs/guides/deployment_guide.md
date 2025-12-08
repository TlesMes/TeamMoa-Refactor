# TeamMoa 배포 가이드

TeamMoa 프로젝트의 Docker 기반 배포 가이드입니다.

## 📋 목차

1. [사전 요구사항](#사전-요구사항)
2. [개발 환경 배포](#개발-환경-배포)
3. [프로덕션 환경 배포](#프로덕션-환경-배포)
4. [환경 변수 설정](#환경-변수-설정)
5. [데이터베이스 마이그레이션](#데이터베이스-마이그레이션)
6. [정적 파일 관리](#정적-파일-관리)
7. [트러블슈팅](#트러블슈팅)

---

## 🔧 사전 요구사항

배포 전 다음 소프트웨어가 설치되어 있어야 합니다:

- **Docker** (>= 20.10)
- **Docker Compose** (>= 2.0)
- **Git**

### Docker 설치 확인

```bash
docker --version
docker-compose --version
```

---

## 🚀 개발 환경 배포

로컬 개발 환경에서 Docker를 사용한 배포 방법입니다.

### 1단계: 저장소 클론

```bash
git clone https://github.com/yourusername/TeamMoa.git
cd TeamMoa
```

### 2단계: 환경 변수 설정

`.env.example` 파일을 복사하여 `.env` 파일 생성:

```bash
cp .env.example .env
```

**Docker 개발 환경**을 사용하는 경우, `.env` 파일에서 다음 항목만 수정:

```env
# DB_HOST를 'db'로 변경 (Docker 컨테이너 이름)
DB_HOST=db

# (선택) 개발용 비밀번호 설정
DB_PASSWORD=dev_password
DB_ROOT_PASSWORD=dev_root_password
```

**로컬 개발 환경**(venv 사용)인 경우, 기본값(`DB_HOST=localhost`) 그대로 사용하면 됩니다.

### 3단계: Docker Compose 실행

```bash
# 백그라운드에서 실행
docker-compose up -d

# 또는 로그 확인하면서 실행
docker-compose up
```

### 4단계: 초기 설정

컨테이너가 시작된 후 다음 명령어로 초기 설정:

```bash
# 데이터베이스 마이그레이션
docker-compose exec web python manage.py migrate

# 정적 파일 수집
docker-compose exec web python manage.py collectstatic --noinput

# 슈퍼유저 생성
docker-compose exec web python manage.py createsuperuser
```

### 5단계: 접속 확인

브라우저에서 다음 URL로 접속:

- **메인 페이지**: http://localhost:8000
- **관리자 페이지**: http://localhost:8000/admin/
- **API 문서**: http://localhost:8000/api/schema/swagger-ui/
- **Health Check**: http://localhost:8000/health/

### 개발 환경 중지

```bash
# 컨테이너 중지
docker-compose stop

# 컨테이너 중지 및 삭제
docker-compose down

# 컨테이너 + 볼륨 삭제 (데이터베이스 초기화)
docker-compose down -v
```

---

## 🏭 프로덕션 환경 배포

프로덕션 환경 배포 시 주의사항 및 절차입니다.

### 1단계: 프로덕션 환경 변수 설정

`.env.example` 파일을 복사하여 `.env.production` 파일 생성:

```bash
cp .env.example .env.production
```

`.env.production` 파일을 열어서 **프로덕션 섹션의 주석을 해제**하고 값을 변경:

```env
# ================================================================
# 개발 환경 설정 주석 처리
# ================================================================
# DEBUG=True
# ALLOWED_HOSTS=localhost,127.0.0.1
# DB_HOST=localhost

# ================================================================
# 프로덕션 환경 설정 주석 해제
# ================================================================
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
DB_HOST=db
DB_ROOT_PASSWORD=strong_root_password
DB_CONN_MAX_AGE=600

# Redis Settings
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=strong_redis_password

# Security Settings
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
```

**필수 변경 사항**:
1. **SECRET_KEY**: 새로 생성 (보안)
   ```bash
   python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
   ```
2. **ALLOWED_HOSTS**: 실제 도메인
3. **DB_PASSWORD, DB_ROOT_PASSWORD**: 강력한 비밀번호
4. **REDIS_PASSWORD**: 강력한 비밀번호
5. **OAuth 설정**: 프로덕션용 Client ID/Secret

### 2단계: SSL 인증서 설정 (선택사항)

HTTPS를 사용하려면 SSL 인증서를 준비:

```bash
mkdir -p deploy/ssl
# SSL 인증서 파일을 deploy/ssl/ 디렉토리에 배치
# - cert.pem
# - key.pem
```

### 3단계: 프로덕션 컨테이너 실행

```bash
docker-compose -f docker-compose.prod.yml up -d
```

### 4단계: 초기 설정

```bash
# 마이그레이션 및 정적 파일 수집은 entrypoint.sh에서 자동 실행됨

# 슈퍼유저 생성
docker-compose -f docker-compose.prod.yml exec web python manage.py createsuperuser
```

### 5단계: 로그 확인

```bash
# 전체 로그 확인
docker-compose -f docker-compose.prod.yml logs -f

# 특정 서비스 로그 확인
docker-compose -f docker-compose.prod.yml logs -f web
docker-compose -f docker-compose.prod.yml logs -f nginx
```

### 프로덕션 환경 업데이트

코드 업데이트 시:

```bash
# 최신 코드 가져오기
git pull origin main

# 컨테이너 재빌드 및 재시작
docker-compose -f docker-compose.prod.yml up -d --build

# 마이그레이션 (필요시)
docker-compose -f docker-compose.prod.yml exec web python manage.py migrate
```

---

## ⚙️ 환경 변수 설정

### 필수 환경 변수

| 변수명 | 설명 | 예시 |
|--------|------|------|
| `SECRET_KEY` | Django 시크릿 키 | `django-insecure-...` |
| `DEBUG` | 디버그 모드 | `False` (프로덕션) |
| `ALLOWED_HOSTS` | 허용 호스트 | `yourdomain.com` |
| `DB_NAME` | 데이터베이스 이름 | `teammoa_db` |
| `DB_USER` | 데이터베이스 유저 | `teammoa_user` |
| `DB_PASSWORD` | 데이터베이스 비밀번호 | `strong_password` |
| `EMAIL_HOST_USER` | 이메일 발신 주소 | `yourapp@gmail.com` |
| `EMAIL_HOST_PASSWORD` | 이메일 앱 비밀번호 | `app_password` |

### 선택적 환경 변수

| 변수명 | 설명 | 기본값 |
|--------|------|--------|
| `REDIS_PASSWORD` | Redis 비밀번호 | (없음) |
| `SECURE_SSL_REDIRECT` | SSL 리다이렉트 | `True` |
| `GUNICORN_WORKERS` | Gunicorn 워커 수 | CPU * 2 + 1 |

---

## 🗄️ 데이터베이스 마이그레이션

### 마이그레이션 생성

```bash
docker-compose exec web python manage.py makemigrations
```

### 마이그레이션 적용

```bash
docker-compose exec web python manage.py migrate
```

### 마이그레이션 상태 확인

```bash
docker-compose exec web python manage.py showmigrations
```

### 데이터베이스 백업

```bash
# MySQL 백업
docker-compose exec db mysqldump -u root -p teammoa_db > backup_$(date +%Y%m%d).sql
```

### 데이터베이스 복원

```bash
# MySQL 복원
docker-compose exec -T db mysql -u root -p teammoa_db < backup_20250101.sql
```

---

## 📁 정적 파일 관리

### 정적 파일 수집

```bash
docker-compose exec web python manage.py collectstatic --noinput
```

### 정적 파일 경로

- **개발 환경**: Django가 직접 서빙 (`STATICFILES_DIRS`)
- **프로덕션**: Nginx가 서빙 (`/app/staticfiles/`)

### 미디어 파일 관리

사용자 업로드 파일은 `media/` 디렉토리에 저장됨:

```bash
# 미디어 파일 볼륨 확인
docker volume inspect teammoa_media_prod
```

---

## 🔍 트러블슈팅

### 1. 컨테이너가 시작되지 않음

```bash
# 로그 확인
docker-compose logs web

# 컨테이너 상태 확인
docker-compose ps
```

**일반적인 원인**:
- 환경 변수 누락 또는 잘못된 설정
- 포트 충돌 (8000, 3306, 6379)
- 데이터베이스 연결 실패

### 2. 데이터베이스 연결 오류

```bash
# 데이터베이스 컨테이너 확인
docker-compose exec db mysql -u root -p

# 데이터베이스 로그 확인
docker-compose logs db
```

### 3. 정적 파일이 로드되지 않음

```bash
# collectstatic 재실행
docker-compose exec web python manage.py collectstatic --noinput --clear

# Nginx 설정 확인
docker-compose exec nginx nginx -t
```

### 4. WebSocket 연결 실패 (Mindmaps)

**원인**: Redis 연결 문제 또는 Nginx WebSocket 설정

```bash
# Redis 연결 확인
docker-compose exec redis redis-cli ping

# Nginx 설정에서 WebSocket 헤더 확인
# deploy/nginx-site.conf의 Upgrade, Connection 헤더 확인
```

### 5. 메모리 부족

```bash
# Docker 리소스 정리
docker system prune -a --volumes

# 사용하지 않는 이미지 삭제
docker image prune -a
```

---

## 📊 모니터링

### Health Check 엔드포인트

```bash
curl http://localhost:8000/health/
```

**응답 예시**:
```json
{
  "status": "healthy",
  "service": "TeamMoa"
}
```

### 컨테이너 리소스 모니터링

```bash
# 실시간 리소스 사용량 확인
docker stats

# 특정 컨테이너 상세 정보
docker inspect teammoa_web_prod
```

### 로그 수집

프로덕션 환경의 로그는 다음 위치에 저장됩니다:
- **Django 로그**: `logs/django.log`
- **Nginx 액세스 로그**: Nginx 컨테이너 내부
- **Nginx 에러 로그**: Nginx 컨테이너 내부

```bash
# Django 로그 확인
docker-compose exec web cat logs/django.log

# Nginx 로그 확인
docker-compose -f docker-compose.prod.yml logs nginx
```

---

## 🚨 보안 체크리스트

프로덕션 배포 전 확인사항:

- [ ] `DEBUG=False` 설정
- [ ] 강력한 `SECRET_KEY` 생성
- [ ] `ALLOWED_HOSTS` 정확히 설정
- [ ] 데이터베이스 비밀번호 변경
- [ ] Redis 비밀번호 설정
- [ ] OAuth 프로덕션 키 사용
- [ ] SSL/TLS 인증서 설정
- [ ] 방화벽 설정 (필요한 포트만 오픈)
- [ ] 정기 백업 설정
- [ ] 모니터링 시스템 연동

---

## 📞 지원

문제 발생 시:
1. [GitHub Issues](https://github.com/yourusername/TeamMoa/issues) 등록
2. 로그 파일 첨부
3. 환경 정보 제공 (OS, Docker 버전 등)

---

**최종 업데이트**: 2025.10.23
