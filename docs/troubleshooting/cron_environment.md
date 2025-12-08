# Docker 크론 환경변수 트러블슈팅

## 📋 목차
1. [문제 정의](#문제-정의)
2. [원인 분석](#원인-분석)
3. [시도한 해결 방법들](#시도한-해결-방법들)
4. [최종 솔루션](#최종-솔루션)
5. [구현 세부사항](#구현-세부사항)
6. [검증 결과](#검증-결과)
7. [솔루션 평가](#솔루션-평가)

---

## 문제 정의

### 상황
TeamMoa 프로젝트에서 Docker 컨테이너 내부 크론(cron)을 통해 Django 관리 명령어를 자동 실행하려 했으나 실패

### 에러 메시지
```
KeyError: 'SECRET_KEY'
django.core.exceptions.ImproperlyConfigured: Set the SECRET_KEY environment variable
```

### 목표
- 매일 새벽 3시에 3일 이상 미인증 계정 자동 삭제
- Django 관리 명령어: `python manage.py delete_unverified_users`

---

## 원인 분석

### 크론의 환경변수 격리

**핵심 문제**: 크론은 최소한의 환경만 가지고 실행됨

```bash
# 일반 쉘 환경 (Docker Compose가 주입한 환경변수 포함)
$ env | wc -l
40

# 크론 실행 환경
$ cron job에서 env | wc -l
8  # PATH, SHELL, HOME 등 기본적인 것만
```

**크론이 상속받지 못하는 것들**:
- Docker Compose `environment` 섹션에서 주입한 환경변수
- Docker `ENV` 명령어로 설정한 환경변수
- 부모 프로세스(PID 1)의 환경변수

### 왜 Django는 환경변수가 필요한가?

TeamMoa 프로젝트는 `django-environ`을 사용:

```python
# TeamMoa/settings/base.py
import environ
env = environ.Env()

SECRET_KEY = env('SECRET_KEY')  # 환경변수에서 읽음
DATABASE_URL = env('DATABASE_URL')
REDIS_URL = env('REDIS_URL')
# ... 등등
```

환경변수가 없으면 Django 설정 로드 자체가 실패합니다.

---

## 시도한 해결 방법들

### ❌ 방법 1: `.env` 파일 로드

**시도**:
```bash
* * * * * appuser bash -c "set -a && source /app/.env && set +a && cd /app && python manage.py ..."
```

**실패 이유**:
- `/app/.env` 파일이 프로덕션 컨테이너에 존재하지 않음
- 프로덕션은 `docker-compose.prod.yml`에서 환경변수를 직접 주입
- 보안상 `.env` 파일을 이미지에 포함하지 않음

---

### ❌ 방법 2: 환경변수 자동 상속 기대

**시도**:
```bash
# Wrapper 스크립트 (/app/cron_run.sh)
#!/bin/bash
cd /app
/opt/venv/bin/python manage.py delete_unverified_users
```

```bash
# 크론 설정
* * * * * appuser /app/cron_run.sh >> /var/log/cron.log 2>&1
```

**테스트**:
```bash
# 직접 실행 시
$ gosu appuser /app/cron_run.sh
✅ 성공! (환경변수 사용 가능)

# 크론에서 실행 시
❌ 실패! (SECRET_KEY 없음)
```

**실패 이유**:
- 크론은 부모 프로세스의 환경변수를 상속받지 못함
- 완전히 새로운 환경에서 실행됨

---

### ⚠️ 방법 3: 크론 파일에 환경변수 직접 선언

**시도**:
```bash
# /etc/cron.d/django-tasks
DJANGO_SETTINGS_MODULE=TeamMoa.settings.prod
SECRET_KEY=12@kzgr_8u3e%0qqvv44*gf5!@&bcs*zo0gap_4be-u&_((^ho
DATABASE_URL=mysql://...
REDIS_URL=redis://...

* * * * * appuser python manage.py delete_unverified_users
```

**문제점**:
1. **확장성 부족**: 환경변수 추가 시마다 크론 파일 수정 필요
2. **DRY 원칙 위반**: `docker-compose.prod.yml`과 중복 관리
3. **보안 위험**: 민감한 정보가 크론 파일에 평문으로 노출
4. **유지보수성 저하**: 환경변수 변경 시 여러 곳 수정 필요

---

### ⚠️ 방법 4: `.env` 파일 볼륨 마운트

**시도**:
```yaml
# docker-compose.prod.yml
services:
  web:
    volumes:
      - .env:/app/.env:ro
```

**문제점**:
1. **배포 복잡도 증가**: 서버에 `.env` 파일 별도 관리 필요
2. **자동화 어려움**: CI/CD 파이프라인에서 `.env` 파일 동기화 필요
3. **보안 관리**: 서버의 `.env` 파일 권한 관리 필요
4. **이미지 포함 불가**: 보안상 `.env`를 이미지에 넣을 수 없음

---

## 최종 솔루션

### ✅ `/proc/1/environ` 활용한 자동 환경 상속

**핵심 아이디어**:
- Docker 컨테이너의 PID 1 프로세스는 컨테이너 시작 시 주입된 **모든 환경변수**를 가지고 있음
- `/proc/1/environ` 파일에서 이를 읽어 현재 쉘에 export

### 아키텍처

```
┌─────────────────────────────────────┐
│   docker-compose.prod.yml           │
│   environment:                      │
│     - SECRET_KEY=${SECRET_KEY}      │
│     - DATABASE_URL=${DATABASE_URL}  │
└──────────────┬──────────────────────┘
               │ Docker 컨테이너 시작
               ▼
┌─────────────────────────────────────┐
│   PID 1 (Daphne)                    │
│   /proc/1/environ                   │
│   (모든 환경변수 저장)               │
└──────────────┬──────────────────────┘
               │ 크론 실행
               ▼
┌─────────────────────────────────────┐
│   Cron Daemon                       │
│   (환경변수 상속 안 됨)              │
└──────────────┬──────────────────────┘
               │ Wrapper 스크립트 실행
               ▼
┌─────────────────────────────────────┐
│   /app/cron_run.sh                  │
│   1. /proc/1/environ 읽기           │
│   2. export 형식으로 변환           │
│   3. source로 환경변수 로드         │
│   4. Django 명령어 실행             │
└─────────────────────────────────────┘
```

---

## 구현 세부사항

### 1. Wrapper 스크립트 작성

**파일**: `/app/cron_run.sh`

```bash
#!/bin/bash

# Docker PID 1 환경변수를 export 형식으로 변환
tr '\0' '\n' < /proc/1/environ | \
  awk -F= 'NF==2 {print "export \""$1"="$2"\""}' > /tmp/container_env.sh

# 환경변수 로드
source /tmp/container_env.sh

# 임시 파일 정리 (보안)
rm -f /tmp/container_env.sh

# Django 관리 명령어 실행
cd /app
/opt/venv/bin/python manage.py delete_unverified_users --dry-run --verbose
```

**상세 설명**:

1. **`/proc/1/environ` 읽기**
   ```bash
   tr '\0' '\n' < /proc/1/environ
   ```
   - PID 1의 환경변수는 NULL(`\0`)로 구분되어 저장됨
   - `tr` 명령어로 줄바꿈(`\n`) 형태로 변환
   - 결과: `KEY=VALUE\nKEY2=VALUE2\n...`

2. **Export 문으로 변환**
   ```bash
   awk -F= 'NF==2 {print "export \""$1"="$2"\""}'
   ```
   - `=`를 구분자로 사용 (`-F=`)
   - 필드가 2개인 경우만 처리 (`NF==2`)
   - `export "KEY=VALUE"` 형식으로 변환
   - 결과: `export "SECRET_KEY=..."\nexport "DATABASE_URL=..."`

3. **환경변수 로드**
   ```bash
   source /tmp/container_env.sh
   ```
   - 임시 파일을 현재 쉘에서 실행
   - 모든 환경변수가 현재 쉘에 설정됨

4. **정리 및 실행**
   ```bash
   rm -f /tmp/container_env.sh
   cd /app
   /opt/venv/bin/python manage.py ...
   ```
   - 보안을 위해 임시 파일 삭제
   - Django 명령어 실행

### 2. 크론 설정

**파일**: `/etc/cron.d/django-tasks`

```bash
# TeamMoa Django Tasks
SHELL=/bin/bash
PATH=/usr/local/bin:/usr/bin:/bin

# 매일 새벽 3시에 3일 이상 미인증 계정 삭제
0 3 * * * appuser /app/cron_run.sh >> /var/log/cron.log 2>&1

```

**주의사항**:
- 파일 끝에 **빈 줄 필수** (크론 요구사항)
- 권한: `chmod 0644`
- 로그 리다이렉션은 `bash -c` 외부에 있어도 됨 (스크립트 파일이므로)

### 3. Dockerfile 설정

```dockerfile
# Install cron
RUN apt-get update && apt-get install -y --no-install-recommends \
    cron \
    && rm -rf /var/lib/apt/lists/*

# Copy wrapper script
COPY deploy/cron_run.sh /app/cron_run.sh
RUN chmod +x /app/cron_run.sh

# Copy crontab file
COPY deploy/crontab /etc/cron.d/django-tasks
RUN chmod 0644 /etc/cron.d/django-tasks

# Create log file
RUN touch /var/log/cron.log && \
    chown appuser:appuser /var/log/cron.log
```

### 4. Entrypoint 설정

**파일**: `deploy/entrypoint.sh`

```bash
#!/bin/bash
set -e

# Start cron daemon
echo "Starting cron daemon..."
service cron start
echo "✅ Cron daemon started"

# ... (다른 초기화 작업)

# Execute the main command as appuser
exec gosu appuser "$@"
```

---

## 검증 결과

### 테스트 환경

**테스트 계정 생성**:
```bash
docker exec teammoa_web_prod gosu appuser bash -c 'cd /app && python manage.py shell << EOF
from accounts.models import User
from django.utils import timezone
from datetime import timedelta

old_date = timezone.now() - timedelta(days=4)
user = User.objects.create_user(
    username="test_unverified_cron",
    email="test_cron@example.com",
    password="testpass123",
    is_active=False
)
user.date_joined = old_date
user.save()
EOF
'
```

### 크론 실행 로그

**로그 파일**: `/var/log/cron.log`

```
Tue Nov 25 20:39:01 UTC 2025

삭제 대상 미인증 계정: 1개
================================================================================

[User ID: 6]
  Username      : test_unverified_cron
  Email         : test_cron@example.com
  Nickname      : (없음)
  Profile       : (없음)
  Date Joined   : 2025-11-22 01:21:48
  Last Login    : (없음)
  Is Active     : False
  Is Deleted    : False
  Deleted At    : (없음)
  Is Staff      : False
  Is Superuser  : False
  경과 일수      : 4일
--------------------------------------------------------------------------------

[DRY-RUN] 실제로 삭제하지 않았습니다. 실제 삭제하려면 --dry-run 옵션을 제거하세요.
```

### 성공 확인

✅ **환경변수 로딩 성공**:
- `SECRET_KEY` 인식
- `DJANGO_SETTINGS_MODULE` 인식
- `DATABASE_URL` 인식

✅ **Django 명령어 정상 실행**:
- 데이터베이스 연결 성공
- 미인증 계정 조회 성공
- 상세 정보 출력 성공

✅ **크론 자동 실행**:
- 매 1분마다 정확히 실행 (테스트 크론)
- 로그 파일에 출력 기록
- 에러 발생 시 stderr도 로그에 기록

---

## 솔루션 평가

### 장점

#### 1. **확장성 (Scalability)**
```bash
# 새로운 환경변수 추가 시
# docker-compose.prod.yml만 수정
environment:
  - NEW_ENV_VAR=value  # 추가

# 크론 파일, 스크립트 수정 불필요! ✅
```

#### 2. **DRY 원칙 (Don't Repeat Yourself)**
- **Single source of truth**: `docker-compose.prod.yml`만 관리
- 환경변수 중복 선언 불필요
- 유지보수 포인트: **3곳 → 1곳** (67% 감소)

#### 3. **보안 (Security)**
- 크론 파일에 민감한 정보 하드코딩 불필요
- 임시 파일 자동 정리 (`rm -f /tmp/container_env.sh`)
- Docker Compose 레벨에서 환경변수 관리

#### 4. **자동화 (Automation)**
- CI/CD 파이프라인에서 추가 작업 불필요
- 재배포 시 크론 설정 수정 불필요
- 개발/스테이징/프로덕션 환경 일관성 보장

#### 5. **재사용성 (Reusability)**
```bash
# 여러 Django 명령어에서 동일한 패턴 사용 가능
0 3 * * * appuser /app/cron_run.sh  # 미인증 계정 삭제
0 2 * * * appuser /app/cron_run_reminders.sh  # 리마인더 전송
0 0 * * 0 appuser /app/cron_run_reports.sh  # 주간 리포트
```

### 단점 및 한계

#### 1. **의존성**
- `/proc/1/environ` 파일 존재 필요 (Linux 전용)
- PID 1 프로세스 권한 이슈 가능성

#### 2. **복잡도**
- 단순 환경변수 전달보다는 복잡한 스크립트
- 새로운 개발자가 이해하는 데 시간 필요

#### 3. **디버깅**
- 환경변수 로딩 실패 시 디버깅 어려움
- 임시 파일이 즉시 삭제되어 검증 불가

### 개선 가능한 점

#### 1. **범용 Wrapper 스크립트**
```bash
#!/bin/bash
# /app/scripts/cron_wrapper.sh - Reusable wrapper

# Load environment
if [ -f /proc/1/environ ]; then
    tr '\0' '\n' < /proc/1/environ | \
    awk -F= 'NF==2 {print "export \""$1"="$2"\""}' > /tmp/env_$$.sh
    source /tmp/env_$$.sh
    rm -f /tmp/env_$$.sh
fi

cd /app

# Execute the command passed as arguments
exec "$@"
```

**사용법**:
```bash
# 크론 파일
0 3 * * * appuser /app/scripts/cron_wrapper.sh python manage.py delete_unverified_users
0 2 * * * appuser /app/scripts/cron_wrapper.sh python manage.py send_reminders
```

#### 2. **에러 핸들링 강화**
```bash
#!/bin/bash
set -euo pipefail  # 에러 발생 시 즉시 종료

# 환경변수 로딩 함수
load_container_env() {
    if [ ! -r /proc/1/environ ]; then
        echo "ERROR: Cannot read /proc/1/environ" >&2
        return 1
    fi

    tr '\0' '\n' < /proc/1/environ | \
    awk -F= 'NF==2 {print "export \""$1"="$2"\""}' > /tmp/env_$$.sh

    source /tmp/env_$$.sh
    rm -f /tmp/env_$$.sh
}

# 환경변수 로딩
if ! load_container_env; then
    echo "ERROR: Failed to load environment variables" >&2
    exit 1
fi

# 필수 환경변수 확인
required_vars=("SECRET_KEY" "DATABASE_URL" "DJANGO_SETTINGS_MODULE")
for var in "${required_vars[@]}"; do
    if [ -z "${!var:-}" ]; then
        echo "ERROR: Required environment variable $var is not set" >&2
        exit 1
    fi
done

cd /app
exec "$@"
```

#### 3. **로깅 개선**
```bash
#!/bin/bash
LOGFILE="/var/log/cron.log"

log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOGFILE"
}

log "INFO: Starting cron job"
log "INFO: Loading environment variables from /proc/1/environ"

# ... 환경변수 로딩 ...

log "INFO: Environment loaded successfully"
log "INFO: Executing command: $*"

cd /app
exec "$@"
```

---

## 비교표: 해결 방법들

| 방법 | 확장성 | 보안 | 자동화 | 복잡도 | 유지보수 | 추천도 |
|------|-------|------|--------|--------|----------|--------|
| `.env` 파일 로드 | ⭐⭐ | ⚠️ | ⭐ | ⭐⭐ | ⭐⭐ | ❌ |
| 크론 파일에 직접 선언 | ⭐ | ❌ | ⭐⭐ | ⭐ | ⭐ | ❌ |
| `.env` 볼륨 마운트 | ⭐⭐ | ⭐ | ⭐ | ⭐⭐ | ⭐ | ⚠️ |
| **`/proc/1/environ` 활용** | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | ✅ |

---

## 관련 파일

### 프로젝트 파일
- **Wrapper 스크립트**: `deploy/cron_run.sh`
- **크론 설정**: `deploy/crontab`
- **Dockerfile**: `Dockerfile`
- **Entrypoint**: `deploy/entrypoint.sh`
- **Django 명령어**: `accounts/management/commands/delete_unverified_users.py`

### 프로덕션 환경
- **스크립트**: `/app/cron_run.sh`
- **크론 파일**: `/etc/cron.d/django-tasks`
- **로그 파일**: `/var/log/cron.log`

---

## 참고 자료

### Linux/Unix
- [cron(8) - Linux man page](https://linux.die.net/man/8/cron)
- [proc(5) - Linux man page](https://linux.die.net/man/5/proc)
- [Environment Variables in Cron Jobs](https://stackoverflow.com/questions/2135478/how-to-simulate-the-environment-cron-executes-a-script-with)

### Docker
- [Docker Environment Variables](https://docs.docker.com/compose/environment-variables/)
- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)

### Django
- [django-environ Documentation](https://django-environ.readthedocs.io/)
- [Django Management Commands](https://docs.djangoproject.com/en/stable/howto/custom-management-commands/)

---

**최종 업데이트**: 2025-11-26
**작성자**: TeamMoa 개발팀
**관련 이슈**: [미인증 계정 자동 삭제 기능](https://github.com/yourusername/TeamMoa/issues/XXX)
