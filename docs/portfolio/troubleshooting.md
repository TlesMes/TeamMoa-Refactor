# 트러블슈팅

> **8건의 핵심 문제 해결 과정**
> 문제 정의 → 원인 분석 → 해결 과정 → 재발 방지

---

## 목차
- [배포 관련](#배포-관련)
- [Django 관련](#django-관련)
- [WebSocket 관련](#websocket-관련)
- [데이터베이스 관련](#데이터베이스-관련)

---

## 배포 관련

### 1. 🔴 HTTPS 리디렉션 루프 (무한 리디렉션)

**중요도**: Critical | **영향 범위**: 프로덕션 전체 서비스 중단

**문제**:
```
ERR_TOO_MANY_REDIRECTS
https://teammoa.duckdns.org → 무한 리디렉션
```

**원인**:
- Django `SECURE_SSL_REDIRECT=True` 설정으로 모든 HTTP 요청을 HTTPS로 리디렉션
- Nginx에서 HTTPS 종료 후 Django에 HTTP로 프록시
- Django는 X-Forwarded-Proto 헤더 없이 스키마 판단 불가능 → 무한 리디렉션

**해결**:
```python
# TeamMoa/settings/prod.py
SECURE_SSL_REDIRECT = True

# Nginx가 HTTPS로 받았음을 Django에 알림
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
```

```nginx
# deploy/nginx-site.conf
location / {
    proxy_pass http://web:8000;
    proxy_set_header X-Forwarded-Proto $scheme;  # https 전달
}
```

**재발 방지**:
- 프록시 환경 배포 시 `X-Forwarded-Proto` 헤더 설정 체크리스트 추가
- Nginx 설정 템플릿에 `proxy_set_header X-Forwarded-Proto $scheme` 기본 포함
- 배포 전 HTTPS 리디렉션 테스트 자동화

**참고**: [Django 문서 - SECURE_PROXY_SSL_HEADER](https://docs.djangoproject.com/en/5.0/ref/settings/#secure-proxy-ssl-header)

---

### 2. 🟡 Docker Health Check 실패 (502 Bad Gateway)

**중요도**: High | **영향 범위**: 컨테이너 오케스트레이션 실패, 무중단 배포 불가

**문제**:
```bash
$ docker ps
NAME                STATUS
teammoa_web_prod    Up (unhealthy)
```

**원인**:
- Health check 엔드포인트 `/health/` 미구현
- Django `ALLOWED_HOSTS`에 컨테이너 내부 호출용 `127.0.0.1` 미등록

**해결**:
```python
# TeamMoa/urls.py
from django.http import JsonResponse

def health_check(request):
    return JsonResponse({'status': 'ok'})

urlpatterns = [
    path('health/', health_check, name='health_check'),
    # ...
]
```

```python
# TeamMoa/settings/prod.py
ALLOWED_HOSTS = [
    '3.34.102.12',
    'teammoa.duckdns.org',
    '127.0.0.1',  # Health check용
    'web'         # Docker 내부 네트워크용
]
```

```dockerfile
# Dockerfile
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://127.0.0.1:8000/health/ || exit 1
```

**재발 방지**:
- Health check 엔드포인트를 프로젝트 초기 설정에 포함
- Nginx health check와 Django health check 분리 (`/nginx-health`, `/health/`)
- `ALLOWED_HOSTS`에 컨테이너 내부 주소(`127.0.0.1`, `web`) 기본 등록
- Dockerfile에 HEALTHCHECK 명령 템플릿화

---

### 3. 🟡 GitHub Actions Dynamic Security Group IP 제거 실패

**중요도**: High | **영향 범위**: CI/CD 파이프라인 중단, 배포 불가

**문제**:
- 배포 실패 시 GitHub Actions Runner IP가 AWS Security Group에 잔류
- 다음 배포 시 중복 IP 등록 시도로 워크플로우 실패

**원인**:
- 배포 스크립트 실패 시 cleanup 단계 미실행 (조건부 실행 미설정)

**해결**:
```yaml
# .github/workflows/ci-cd.yml
- name: Remove IP from security group
  if: always()  # 성공/실패 상관없이 항상 실행
  run: |
    aws ec2 revoke-security-group-ingress \
        --group-id ${{ secrets.AWS_SECURITY_GROUP_ID }} \
        --protocol tcp \
        --port 22 \
        --cidr ${{ steps.ip.outputs.ipv4 }}/32
  continue-on-error: true  # 제거 실패해도 워크플로우는 계속
```

**재발 방지**:
- 모든 CI/CD 워크플로우에 cleanup 단계 `if: always()` 적용
- Dynamic Security Group 사용 시 IP 제거 단계 필수화
- 워크플로우 실패 시 수동 IP 제거 스크립트 문서화

---

## Django 관련

### 4. 🔴 username/email 영구 점유 문제

**중요도**: Critical | **영향 범위**: 사용자 경험 저하, DB 리소스 낭비

**문제**:
- 회원가입 시 이메일 주소 오타 입력
- 이메일 인증 실패로 계정 미활성화 (`is_active=False`)
- username/email은 DB unique 제약으로 재사용 불가

**원인**:
- Django `unique=True` 제약조건이 soft-deleted 레코드에도 적용
- 미인증 계정 자동 정리 로직 부재

**해결 (Soft Delete + 자동 정리)**:
```python
# accounts/models.py
class User(AbstractUser):
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['username'],
                condition=Q(is_deleted=False),
                name='unique_active_username'
            ),
            models.UniqueConstraint(
                fields=['email'],
                condition=Q(is_deleted=False),
                name='unique_active_email'
            )
        ]
```

```python
# accounts/management/commands/delete_unverified_users.py
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from accounts.models import User

class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('--days', type=int, default=3)

    def handle(self, *args, **options):
        days = options['days']
        cutoff = timezone.now() - timedelta(days=days)

        # 3일 이상 미인증 계정 삭제
        users = User.objects.filter(
            is_active=False,
            is_deleted=False,
            date_joined__lt=cutoff
        )

        count = users.count()
        users.delete()

        self.stdout.write(f'✅ {count}개 미인증 계정 삭제')
```

**자동 실행 (crontab)**:
```bash
# 매일 새벽 3시에 3일 이상 미인증 계정 삭제
0 3 * * * cd ~/TeamMoa && docker exec teammoa_web_prod python manage.py delete_unverified_users
```

**성과**:
- 미인증 계정 자동 정리로 username/email 재사용 가능
- DB 리소스 최적화

**재발 방지**:
- 조건부 Unique 제약(`UniqueConstraint` + `condition`)을 모델 설계 표준으로 적용
- Management Command 크론 작업 자동 등록 스크립트 작성
- 미인증 계정 정리 로그 주간 모니터링

**코드 위치**: [`accounts/management/commands/delete_unverified_users.py`](../../accounts/management/commands/delete_unverified_users.py)

---

### 5. 🟢 트랜잭션 원자성 위반 (회원가입 + 이메일 발송)

**중요도**: Medium | **영향 범위**: 데이터 일관성 문제, 더미 계정 생성

**문제**:
- 회원가입 성공 후 DB 커밋
- 이메일 발송 실패 시 계정만 생성되고 인증 메일 미전송

**원인**:
- 회원가입과 이메일 발송이 별도 트랜잭션으로 분리
- 이메일 발송 실패 시 롤백 메커니즘 부재

**해결**:
```python
# accounts/services.py
from django.db import transaction

class AuthService:
    @transaction.atomic
    def register_user(self, form, current_site):
        """
        회원가입 + 이메일 발송을 원자적으로 처리
        이메일 발송 실패 시 회원가입도 롤백
        """
        with transaction.atomic():
            # 1. 유저 생성 (DB 저장)
            user = form.save()

            # 2. 이메일 발송 (실패 시 예외 발생 → 롤백)
            self.send_activation_email(user, current_site)

        # 예외 없이 성공하면 최종 커밋
        return user
```

**재발 방지**:
- 서비스 레이어 메서드에 `@transaction.atomic` 데코레이터 기본 적용
- 외부 API 호출(이메일, SMS) 포함 시 트랜잭션 설계 검토 필수
- 회원가입/결제 등 중요 비즈니스 로직에 트랜잭션 테스트 추가

**코드 위치**: [`accounts/services.py:18-36`](../../accounts/services.py#L18-L36)

---

## WebSocket 관련

### 6. 🟢 WebSocket 연결 실패 (404 Not Found)

**중요도**: Medium | **영향 범위**: 실시간 마인드맵 기능 전체 불가

**문제**:
```javascript
WebSocket connection to 'ws://localhost:8000/ws/mindmap/1/1/' failed: 404
```

**원인**:
- `python manage.py runserver`는 WSGI 프로토콜만 지원 (WebSocket 미지원)
- Django Channels 라우팅 설정되었으나 ASGI 서버 미사용

**해결**:
```bash
# 개발 환경
python -m daphne -b 0.0.0.0 -p 8000 TeamMoa.asgi:application

# 프로덕션 환경 (Docker)
CMD ["daphne", "-b", "0.0.0.0", "-p", "8000", "TeamMoa.asgi:application"]
```

**재발 방지**:
- 개발 환경 설정 가이드에 Daphne 사용 명시
- `README.md`에 WebSocket 기능 개발 시 ASGI 서버 필수 안내
- Docker Compose에서 Daphne로 통일하여 개발/운영 환경 일치

---

### 7. 🟡 Nginx WebSocket 프록시 실패 (502 Bad Gateway)

**중요도**: High | **영향 범위**: 프로덕션 실시간 협업 기능 중단

**문제**:
```
WebSocket connection to 'wss://teammoa.duckdns.org/ws/mindmap/1/1/' failed
```

**원인**:
- Nginx 기본 설정은 HTTP/1.0 프록시 (WebSocket Upgrade 헤더 미전달)
- WebSocket 프로토콜 협상 실패로 연결 거부

**해결**:
```nginx
# deploy/nginx-site.conf
location /ws/ {
    proxy_pass http://web:8000;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
}
```

**재발 방지**:
- Nginx 설정 템플릿에 WebSocket 프록시 설정 기본 포함
- `/ws/` 경로는 자동으로 WebSocket 설정 적용되도록 표준화
- Nginx 설정 변경 시 WebSocket 연결 테스트 자동화

**참고**: [Nginx 문서 - WebSocket proxying](http://nginx.org/en/docs/http/websocket.html)

---

## 데이터베이스 관련

### 8. 🔴 N+1 쿼리 문제 (느린 페이지 로딩)

**중요도**: Critical | **영향 범위**: 팀 목록 페이지 성능 저하

**문제**:
- 팀 목록 페이지 로딩 시간 과다 소요
- 10개 팀 조회 시 11번 DB 쿼리 발생 (1 + N)

**원인**:
- ORM lazy loading으로 인한 N+1 쿼리 발생
- 외래키 참조마다 개별 SELECT 쿼리 실행

```python
# Before
teams = Team.objects.all()  # 1번 쿼리
for team in teams:
    print(team.host.username)  # 팀마다 추가 쿼리 (N번)
```

**해결**:
```python
# After
teams = Team.objects.select_related('host').all()  # 1번 JOIN 쿼리
for team in teams:
    print(team.host.username)  # 쿼리 없음 (이미 로드됨)
```

**재발 방지**:
- 서비스 레이어 QuerySet에 `select_related()`/`prefetch_related()` 기본 적용
- Django Debug Toolbar를 개발 환경에 필수 설치
- 목록 페이지 개발 시 쿼리 수 10개 이하 유지 원칙
- 코드 리뷰 시 N+1 쿼리 체크리스트 항목 추가

---

## 회고

### Critical 이슈 해결 성과

**🔴 3건의 Critical 이슈 해결로 서비스 안정화**

1. **HTTPS 리디렉션 루프** (#1)
   - 서비스 중단 → 즉시 복구
   - `SECURE_PROXY_SSL_HEADER` 설정으로 프록시 환경 이해

2. **username/email 영구 점유** (#4)
   - 재가입 불가 → 자동 정리 시스템 구축
   - Soft Delete + 조건부 Unique 제약으로 DB 설계 개선

3. **N+1 쿼리** (#8)
   - 11번 쿼리 → 1번 쿼리로 최적화 (10배 쿼리 감소)
   - `select_related()`로 ORM 최적화 학습

### 문제 해결 패턴 분석

**중요도별 분포**
1. 🔴 **Critical** (3건): 서비스 중단, 사용자 경험 직접 영향
2. 🟡 **High** (3건): 배포 안정성, 핵심 기능 장애
3. 🟢 **Medium** (2건): 데이터 정합성, 개발 환경

**기술 영역별 분포**
1. **인프라 계층** (3건): HTTPS, Health Check, Security Group
2. **데이터 계층** (3건): username/email, 트랜잭션, N+1 쿼리
3. **실시간 통신** (2건): WebSocket 연결, Nginx 프록시

### 재발 방지 전략

**자동화**
- Health check 엔드포인트 표준화
- CI/CD cleanup 단계 `if: always()` 적용
- Management Command 크론 자동화

**모니터링**
- Django Debug Toolbar로 쿼리 수 실시간 확인
- Docker logs로 컨테이너 상태 추적
- Browser DevTools Network 탭으로 WebSocket 연결 검증

**문서화**
- 트러블슈팅 8건 문서화로 지식 체계화
- 코드 위치 링크로 추적성 확보

### 기술적 성장

- **프로덕션 환경 이해**: 개발과 배포 환경의 차이 (프록시, HTTPS, Health Check)
- **트랜잭션 설계**: 원자성, 일관성, 격리 수준 고려
- **성능 최적화**: N+1 쿼리 해결, ORM 최적화 기법
- **실시간 통신**: ASGI, WebSocket, Nginx 프로토콜 협상

---

**작성일**: 2025년 12월 7일
**버전**: 2.0
**총 트러블슈팅 건수**: 8건
