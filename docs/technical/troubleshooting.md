# 트러블슈팅

> **11건의 핵심 문제 해결 과정**
> 문제 정의 → 원인 분석 → 해결 과정 → 재발 방지

---

## 목차
- [배포 관련](#배포-관련)
- [Django 관련](#django-관련)
- [WebSocket 관련](#websocket-관련)
- [데이터베이스 관련](#데이터베이스-관련)
- [성능 최적화](#성능-최적화)

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

### 3. 🟡 ALB 무중단 배포 중 502 Bad Gateway (Connection Draining)

**중요도**: High | **영향 범위**: 무중단 배포 실패, 배포 중 약 5% 요청 실패

#### 문제 상황

CI/CD 파이프라인을 통한 자동 배포 중 1~2초간 502 Bad Gateway 에러 발생. Multi-AZ (2대 EC2 서버) 환경에서 Rolling Update 방식으로 배포 시 일부 요청이 실패하는 문제.

#### 원인 분석

1. **Target Deregister 직후 즉시 컨테이너 재시작**
   - ALB에서 서버를 제거한 직후 바로 Django 컨테이너 재시작
   - 진행 중인 요청이 강제 종료됨

2. **Connection Draining 설정 누락**
   - ALB Target Group에서 Connection Draining (대기 시간) 미설정
   - 기존 연결이 완전히 종료되기 전에 서버가 내려감

3. **Health Check 전 트래픽 유입**
   - 컨테이너 재시작 후 Health Check 통과 전에 트래픽 라우팅
   - 아직 준비되지 않은 서버로 요청 전달 → 502 에러

#### 해결 과정

**1. ALB Connection Draining 30초 설정**
```bash
# Target Group Deregistration Delay 설정 (5초 → 30초)
aws elbv2 modify-target-group-attributes \
  --target-group-arn $TARGET_GROUP_ARN \
  --attributes Key=deregistration_delay.timeout_seconds,Value=30
```

**2. Rolling Update 배포 순서 조정**
```bash
# GitHub Actions Workflow에서 자동화
1. 서버 1번 Target Deregister
2. 30초 대기 (Connection Draining)
3. 서버 1번 컨테이너 재시작
4. Health Check 통과 확인 (3회, 10초 간격)
5. 서버 1번 Target Register
6. 서버 2번도 동일 순서로 반복
```

**3. 배포 스크립트 자동화**
```yaml
# .github/workflows/deploy.yml
- name: Rolling Update - Server 1
  run: |
    # Deregister
    aws elbv2 deregister-targets --target-group-arn $TG_ARN \
      --targets Id=$EC2_1_ID

    # Wait for Connection Draining
    sleep 300

    # Deploy
    ssh ec2-server-1 "cd ~/TeamMoa && docker compose down && docker compose up -d"

    # Wait for Health Check
    for i in {1..3}; do
      sleep 10
      # Health check logic
    done

    # Register
    aws elbv2 register-targets --target-group-arn $TG_ARN \
      --targets Id=$EC2_1_ID
```

#### 검증 결과

**Locust 부하 테스트 (배포 중)**
- 총 요청: 15,000건
- 502 에러: **0건** (개선 전: 약 750건, 5%)
- 다운타임: **0초**
- 평균 응답 시간: 52ms

**결과**: 완전한 무중단 배포 달성

#### 재발 방지

1. **배포 스크립트 표준화**
   - GitHub Actions Workflow에 Connection Draining 대기 로직 필수화
   - 모든 배포는 자동화된 파이프라인을 통해서만 실행

2. **부하 테스트 통합**
   - 배포 후 자동 부하 테스트 실시 (Locust)
   - 502 에러 0건 확인 후 다음 서버로 진행

3. **모니터링 강화**
   - CloudWatch Alarms: ALB 502 에러 발생 시 즉시 알림
   - Nginx/Django 로그에서 배포 중 에러율 추적

#### 배운 점

- **"무중단 배포"의 정의**: 단순히 서버를 끄지 않는 것이 아니라, **진행 중인 요청까지 안전하게 처리**하는 것
- **인프라 레이어의 세밀함**: Target Deregister, Connection Draining, Health Check 순서의 중요성
- **데이터 기반 검증**: 부하 테스트 없이는 "무중단"을 증명할 수 없음
- **운영과 개발의 차이**: 튜토리얼 수준 구현과 프로덕션 수준 구현의 차이 체감

---

### 4. 🟡 GitHub Actions Dynamic Security Group IP 제거 실패

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

### 6. 🟡 이메일 인증 링크 도메인 불일치 (localhost 링크 발송)

**중요도**: Medium | **영향 범위**: 회원가입 이메일 인증 실패

**문제**:
- 프로덕션 환경에서 회원가입 후 이메일 인증 링크가 `http://localhost:8000/...`로 발송됨
- 사용자가 링크 클릭 시 접속 불가 (localhost는 로컬 머신만 접근 가능)

**원인**:
```bash
# EC2 서버 .env 파일
ALLOWED_HOSTS=localhost,127.0.0.1,teammoa.shop,www.teammoa.shop
# ❌ SITE_DOMAIN 설정 누락!
```

- Django `settings.SITE_DOMAIN`이 환경 변수에 정의되지 않음
- 기본값 `localhost:8000` 사용 ([`TeamMoa/settings/base.py:83`](../../TeamMoa/settings/base.py#L83))
- `django.contrib.sites` 프레임워크가 이메일 링크 생성 시 잘못된 도메인 사용

**해결**:

1. **`.env` 파일에 도메인 설정 추가**:
```bash
# Site Settings (이메일 인증 링크용)
SITE_DOMAIN=teammoa.shop
SITE_NAME=TeamMoa

# CORS도 함께 업데이트
CORS_ALLOWED_ORIGINS=https://teammoa.shop,https://www.teammoa.shop,https://teammoa.duckdns.org
```

2. **컨테이너 재생성** (환경 변수 반영):
```bash
docker compose -f docker-compose.web.yml up -d --force-recreate
```

3. **Django Site 객체 업데이트** (DB 반영):
```bash
docker compose -f docker-compose.web.yml exec web python manage.py migrate
```

4. **설정 확인**:
```bash
docker compose -f docker-compose.web.yml exec web python manage.py shell -c \
  "from django.contrib.sites.models import Site; site = Site.objects.get(id=1); print(f'Domain: {site.domain}, Name: {site.name}')"
# 출력: Domain: teammoa.shop, Name: TeamMoa
```

**설정 파일 위치**:
```python
# TeamMoa/settings/base.py:83-84
SITE_DOMAIN = env('SITE_DOMAIN', default='localhost:8000')  # ⚠️ 기본값 주의!
SITE_NAME = env('SITE_NAME', default='TeamMoa')
```

**작동 원리**:
- `accounts/signals.py`에서 마이그레이션 시 `Site` 객체 자동 업데이트
- Django Allauth가 이메일 템플릿 렌더링 시 `{{ site.domain }}` 사용
- 이메일 인증 링크: `https://{{ site.domain }}/accounts/confirm-email/...`

**재발 방지**:
- `.env.example`에 `SITE_DOMAIN`, `SITE_NAME` 설정 예시 포함 (✅ 완료)
- 도메인 변경 시 체크리스트:
  1. `ALLOWED_HOSTS` 업데이트
  2. `SITE_DOMAIN` 업데이트
  3. `CORS_ALLOWED_ORIGINS` 업데이트
  4. SSL 인증서 갱신 (Let's Encrypt)
  5. OAuth 리디렉션 URI 업데이트 (Google, GitHub)
- 프로덕션 배포 체크리스트에 "Site 도메인 확인" 항목 추가

**관련 이슈**: ALB 구축 후 도메인을 `duckdns.org`에서 `teammoa.shop`으로 변경했으나, `.env` 파일의 `SITE_DOMAIN` 설정을 누락하여 발생

---

## WebSocket 관련

### 7. 🟢 WebSocket 연결 실패 (404 Not Found)

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

### 8. 🟡 Nginx WebSocket 프록시 실패 (502 Bad Gateway)

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

### 9. 🔴 N+1 쿼리 문제 (느린 페이지 로딩)

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

## 성능 최적화

### 10. ✅ 중복 쿼리 문제 (Mixin-View 계층 간 이중 조회)

**중요도**: High | **영향 범위**: 팀 관련 모든 페이지 성능 저하 | **해결 완료**: 2026.01.09

#### 문제 상황

Django Debug Toolbar를 사용해 쿼리를 분석한 결과, 팀 메인 페이지에서 15개 쿼리 중 8개(53%)가 중복 실행되는 문제 발견. 동일한 `Team`, `User` 객체를 Mixin, View, Template 각 계층에서 반복적으로 조회하여 불필요한 DB 부하 발생.

#### 원인 분석

**1. Mixin과 View의 이중 조회**

```python
# common/mixins.py
class TeamMemberRequiredMixin:
    def dispatch(self, request, *args, **kwargs):
        team = get_object_or_404(Team, pk=kwargs['pk'])  # ← 1번째 조회
        # 권한 검증 후 버림
        return super().dispatch(request, *args, **kwargs)

# teams/views.py
class TeamMainPageView(DetailView):
    model = Team  # ← DetailView가 자동으로 2번째 조회

    def get_context_data(self, **kwargs):
        team = self.get_object()  # ← 3번째 접근
```

**2. Django Debug Toolbar 분석 결과**

| 페이지 | 총 쿼리 | 중복 쿼리 | 중복율 | 주요 중복 대상 |
|-------|---------|----------|--------|---------------|
| 팀 메인 | 15개 | 8개 | 53% | `accounts_user` 4번, `teams_team` 4번 |
| 멤버 보드 | 15개 | 8개 | 53% | `accounts_user` 3번, `teams_team` 3번, `members_todo` 4번 |
| 마인드맵 목록 | 10개 | 5개 | 50% | `accounts_user` 3번, `teams_team` 4번 |
| 마인드맵 상세 | 15개 | 8개 | 53% | `teams_team` 3번, `mindmaps_mindmap` 3번, `mindmaps_node` 3번 |

**3. 중복 발생 흐름**

```
HTTP Request
    ↓
1. TeamMemberRequiredMixin.dispatch()
   → SELECT * FROM teams_team WHERE id=1  # 1번째
   → SELECT * FROM accounts_user WHERE id=2  # user 조회
    ↓
2. DetailView.get_object()
   → SELECT * FROM teams_team WHERE id=1  # 2번째 (중복!)
    ↓
3. get_context_data()
   → team.host → SELECT * FROM accounts_user  # 3번째 (중복!)
    ↓
4. Template Rendering
   → {{ team.members.count }} → SELECT COUNT(*)  # 4번째 (중복!)
```

#### 해결 과정

**1. Mixin 캐싱 및 JOIN 최적화** ([`common/mixins.py`](../../common/mixins.py))

```python
class TeamMemberRequiredMixin:
    def dispatch(self, request, *args, **kwargs):
        # Team 객체를 select_related/prefetch_related로 최적화하여 조회
        team = get_object_or_404(
            Team.objects.select_related('host').prefetch_related('members'),
            pk=kwargs['pk']
        )
        if request.user not in team.members.all():
            messages.error(request, "팀원이 아닙니다.")
            return redirect('teams:main_page')

        # View에서 재사용할 수 있도록 캐시에 저장
        self._team_cache = team
        return super().dispatch(request, *args, **kwargs)
```

**2. View에서 캐시 재사용** ([`teams/views.py`](../../teams/views.py))

```python
class TeamMainPageView(TeamMemberRequiredMixin, DetailView):
    def get_object(self, queryset=None):
        """Mixin에서 캐시한 team 객체 재사용 (중복 쿼리 방지)"""
        if hasattr(self, '_team_cache'):
            return self._team_cache
        team = super().get_object(queryset)
        self._team_cache = team
        return team

    def get_context_data(self, **kwargs):
        # get_object()를 먼저 호출하여 self.object 설정
        if not hasattr(self, 'object') or self.object is None:
            self.object = self.get_object()

        context = super().get_context_data(**kwargs)
        team = self.object  # 캐시된 객체 사용

        # TeamUser 조회 시 user 정보를 JOIN으로 가져옴 (N+1 방지)
        context['members'] = TeamUser.objects.filter(team=team).select_related('user')
        # ... (나머지 로직)
```

**3. COUNT 쿼리 제거** ([`members/services.py`](../../members/services.py))

```python
# 미할당 TODO를 한 번에 조회 후 Python에서 분리 (쿼리 1개 절약)
todos_unassigned_all = list(Todo.objects.filter(
    team=team,
    assignee__isnull=True
).select_related('milestone').order_by('order', 'created_at'))

# Python에서 완료 여부로 분리 (추가 쿼리 없음)
todos_unassigned = [todo for todo in todos_unassigned_all if not todo.is_completed]
todos_done = [todo for todo in todos_unassigned_all if todo.is_completed]
```

**4. 마인드맵 상세 페이지 최적화** ([`mindmaps/views.py`](../../mindmaps/views.py), [`mindmaps/services.py`](../../mindmaps/services.py))

```python
# mindmaps/views.py
class MindmapDetailPageView(TeamMemberRequiredMixin, DetailView):
    def get_context_data(self, **kwargs):
        # get_object()를 먼저 호출하여 self.object 설정 (중복 쿼리 방지)
        if not hasattr(self, 'object') or self.object is None:
            self.object = self.get_object()

        context = super().get_context_data(**kwargs)
        team = getattr(self, '_team_cache', None) or get_object_or_404(Team, pk=self.kwargs['pk'])

        # mindmap은 이미 조회했으므로 self.object 전달
        mindmap_data = self.mindmap_service.get_mindmap_with_nodes(
            self.kwargs['mindmap_id'], mindmap=self.object
        )

# mindmaps/services.py
def get_mindmap_with_nodes(self, mindmap_id, mindmap=None):
    # mindmap이 전달되지 않았을 때만 조회
    if mindmap is None:
        mindmap = get_object_or_404(Mindmap, pk=mindmap_id)

    # mindmap_id를 직접 사용하여 불필요한 JOIN 방지
    nodes = Node.objects.filter(mindmap_id=mindmap_id).order_by('id')
    lines = NodeConnection.objects.filter(mindmap_id=mindmap_id).order_by('id')
```

**5. 노드 상세 페이지 최적화** ([`mindmaps/views.py`](../../mindmaps/views.py), [`mindmaps/services.py`](../../mindmaps/services.py))

```python
# mindmaps/views.py
class NodeDetailPageView(TeamMemberRequiredMixin, DetailView):
    def get_context_data(self, **kwargs):
        # get_object()를 먼저 호출하여 self.object 설정
        if not hasattr(self, 'object') or self.object is None:
            self.object = self.get_object()

        context = super().get_context_data(**kwargs)
        team = getattr(self, '_team_cache', None) or get_object_or_404(Team, pk=self.kwargs['pk'])

        # node는 이미 조회했으므로 self.object 전달
        node_data = self.mindmap_service.get_node_with_comments(
            self.kwargs['node_id'], node=self.object
        )

# mindmaps/services.py
def get_node_with_comments(self, node_id, node=None):
    # node가 전달되지 않았을 때만 조회
    if node is None:
        node = get_object_or_404(Node, pk=node_id)

    # node_id를 직접 사용하여 불필요한 JOIN 방지
    comments = Comment.objects.filter(node_id=node_id).select_related('user').order_by('-id')
```

#### 최적화 결과

**측정 환경**: Django Debug Toolbar (로컬 Docker 환경, 2026.01.09)

| 페이지 | 쿼리 수 | 응답 시간 | 개선율 |
|--------|---------|----------|--------|
| **팀 메인** | 13개 → 8개 | 3.7 ms → 2.37 ms | 38% 감소, 39% 단축 ✅ |
| **멤버 보드** | 15개 → 10개 | 4.8 ms → 3.22 ms | 33% 감소, 33% 단축 ✅ |
| **마인드맵 목록** | 10개 → 7개 | 3.23 ms → 1.98 ms | 30% 감소, 39% 단축 ✅ |
| **마인드맵 상세** | 11개 → 9개 | 3.41 ms → 2.39 ms | 18% 감소, 30% 단축 ✅ | 

**핵심 개선 사항**:
- ✅ Mixin-View 계층 간 Team 객체 캐싱으로 중복 조회 완전 제거
- ✅ `select_related('host')` + `prefetch_related('members')` JOIN 최적화
- ✅ `list()` 사용으로 템플릿 COUNT 쿼리 제거
- ✅ Python 필터링으로 조건별 SELECT 쿼리 통합
- ✅ DetailView `self.object` 사전 설정으로 서비스 레이어 중복 조회 방지
- ✅ FK 필드 ID 직접 사용으로 불필요한 JOIN 제거 (예: `mindmap_id=X` vs `mindmap=obj`)

**코드 위치**:
- [`common/mixins.py:6-26`](../../common/mixins.py#L6-L26) - TeamMemberRequiredMixin
- [`teams/views.py:215-256`](../../teams/views.py#L215-L256) - TeamMainPageView
- [`members/services.py:377-385`](../../members/services.py#L377-L385) - get_team_todos_with_stats
- [`mindmaps/views.py:39-67`](../../mindmaps/views.py#L39-L67) - MindmapDetailPageView
- [`mindmaps/views.py:134-161`](../../mindmaps/views.py#L134-L161) - NodeDetailPageView
- [`mindmaps/services.py:87-114`](../../mindmaps/services.py#L87-L114) - get_mindmap_with_nodes
- [`mindmaps/services.py:339-364`](../../mindmaps/services.py#L339-L364) - get_node_with_comments

---

### 11. ✅ 템플릿 태그로 인한 N+1 쿼리 문제

**중요도**: High | **영향 범위**: 공유 게시판, 노드 댓글 목록 성능 저하 | **해결 완료**: 2026.01.10

#### 문제 상황

Django Debug Toolbar 분석 결과, 공유 게시판 목록과 노드 댓글 목록에서 항목 개수에 비례하여 쿼리가 증가하는 N+1 문제 발견.

**공유 게시판 목록**:
- 게시물 0개: 8 쿼리
- 게시물 1개: 10 쿼리
- 게시물 2개: 11 쿼리
- 게시물 3개: 12 쿼리
- **증가율**: 게시물 +1개당 쿼리 +1~2개

**노드 댓글 목록**:
- 댓글 개수에 비례하여 쿼리 증가

#### 원인 분석

**1. 템플릿 태그에서 추가 쿼리 발생**

```django
<!-- shares/templates/shares/post_list.html -->
{% for post in post_list %}
  <span class="post-author">
    {% user_display_name post.teamuser.user team %}  <!-- ← N+1 발생 -->
  </span>
{% endfor %}
```

**2. `user_display_name` 템플릿 태그 내부 로직**

```python
# accounts/templatetags/user_filters.py
@register.simple_tag
def user_display_name(user, team):
    return User.get_display_name_in_team(user, team)

# accounts/models.py
@classmethod
def get_display_name_in_team(cls, user_or_none, team):
    # 3. 팀 탈퇴 체크 - 게시물/댓글마다 실행됨! ⚠️
    if not TeamUser.objects.filter(team=team, user=user_or_none).exists():
        return "탈퇴한 사용자"

    return user_or_none.nickname
```

**3. N+1 쿼리 발생 흐름**

```
게시물 목록 조회 (1개 쿼리)
    ↓
템플릿 렌더링 시작
    ↓
게시물 1: {% user_display_name %} → TeamUser.objects.filter().exists() (쿼리 1)
게시물 2: {% user_display_name %} → TeamUser.objects.filter().exists() (쿼리 2)
게시물 3: {% user_display_name %} → TeamUser.objects.filter().exists() (쿼리 3)
...
```

**4. 서비스 레이어는 이미 최적화되어 있었음**

```python
# shares/services.py
posts_queryset = Post.objects.filter(team=team).select_related('teamuser__user')
```

`select_related('teamuser__user')`로 Post → TeamUser → User를 JOIN으로 가져왔지만, 템플릿 태그에서 추가 검증 쿼리가 발생함.

#### 해결 과정

**해결 방법**: 템플릿에서 직접 `nickname` 접근하여 템플릿 태그 우회

**1. 공유 게시판 목록 템플릿 수정** ([`shares/templates/shares/post_list.html`](../../shares/templates/shares/post_list.html))

```django
<!-- Before: N+1 발생 -->
<span class="post-author">
  {% if post.teamuser %}
    {% user_display_name post.teamuser.user team %}
  {% else %}
    탈퇴한 사용자
  {% endif %}
</span>

<!-- After: 직접 접근 (추가 쿼리 없음) -->
<span class="post-author">
  {% if post.teamuser and post.teamuser.user %}
    {{ post.teamuser.user.nickname }}
  {% else %}
    탈퇴한 사용자
  {% endif %}
</span>
```

**2. 노드 댓글 템플릿 수정** ([`mindmaps/templates/mindmaps/node_detail_page.html`](../../mindmaps/templates/mindmaps/node_detail_page.html))

```django
<!-- Before: N+1 발생 -->
<span class="node-detail-comment-author">
  {% user_display_name comment.user team %}
</span>

<!-- After: 직접 접근 (추가 쿼리 없음) -->
<span class="node-detail-comment-author">
  {% if comment.user %}
    {{ comment.user.nickname }}
  {% else %}
    탈퇴한 사용자
  {% endif %}
</span>
```

**3. 마인드맵 Line N+1 해결** ([`mindmaps/services.py:109`](../../mindmaps/services.py#L109))

```python
# Before: from_node, to_node 접근 시 개별 쿼리
lines = NodeConnection.objects.filter(mindmap_id=mindmap_id).order_by('id')

# After: select_related로 사전 로딩
lines = NodeConnection.objects.filter(mindmap_id=mindmap_id).select_related('from_node', 'to_node').order_by('id')
```

#### 최적화 결과

**공유 게시판 목록**:
- **Before**: 게시물 3개 시 12 쿼리
- **After**: 게시물 3개 시 8 쿼리 (33% 감소)
- 게시물 증가에도 쿼리 수 일정

**노드 댓글 목록**:
- **Before**: 댓글 N개 시 8+N 쿼리
- **After**: 댓글 N개 시 8 쿼리 (N개 쿼리 제거)

**마인드맵 상세 (Line)**:
- **Before**: Line N개 시 9+2N 쿼리
- **After**: Line N개 시 9 쿼리 (2N개 쿼리 제거)

#### 재발 방지

**1. 템플릿 태그 사용 가이드라인**
- 템플릿 태그 내부에서 DB 쿼리 실행 금지 (특히 루프 내부)
- 이미 로드된 관계는 직접 접근 (예: `user.nickname` vs 템플릿 태그)
- 검증 로직은 서비스 레이어에서 처리

**2. Django Debug Toolbar 필수 확인 항목**
- "Similar queries" 섹션: 반복 패턴 확인
- "Duplicates" 섹션: 동일 쿼리 확인
- 목록 페이지는 항목 수에 관계없이 쿼리 수 일정하게 유지

**3. ORM 최적화 체크리스트**
- ✅ 서비스 레이어: `select_related()`, `prefetch_related()` 적용
- ✅ 템플릿: 추가 쿼리 발생 여부 확인
- ✅ 템플릿 태그/필터: DB 쿼리 실행 금지

#### 교훈

- **"서비스 최적화 ≠ 전체 최적화"**: 서비스 레이어에서 JOIN을 적용해도 템플릿 레이어에서 추가 쿼리가 발생할 수 있음
- **템플릿 태그의 숨은 비용**: 편의성을 위한 템플릿 태그가 성능 병목이 될 수 있음
- **계층 간 협업 중요성**: ORM 최적화는 서비스 레이어부터 템플릿까지 전 계층에서 고려해야 함

**코드 위치**:
- [`shares/templates/shares/post_list.html:84-90`](../../shares/templates/shares/post_list.html#L84-L90)
- [`mindmaps/templates/mindmaps/node_detail_page.html:56-62`](../../mindmaps/templates/mindmaps/node_detail_page.html#L56-L62)
- [`mindmaps/services.py:109`](../../mindmaps/services.py#L109)

---

## 회고

### Critical 이슈 해결 성과

**🔴 5건의 Critical 이슈 해결로 서비스 안정화**

1. **HTTPS 리디렉션 루프** (#1)
   - 서비스 중단 → 즉시 복구
   - `SECURE_PROXY_SSL_HEADER` 설정으로 프록시 환경 이해

2. **ALB 무중단 배포 중 502 에러** (#3)
   - 5% 요청 실패 → 완전한 무중단 배포 달성
   - Connection Draining 30초 대기 로직으로 진행 중인 요청 안전 처리
   - Locust 부하 테스트로 "무중단"을 정량적으로 검증

3. **username/email 영구 점유** (#4)
   - 재가입 불가 → 자동 정리 시스템 구축
   - Soft Delete + 조건부 Unique 제약으로 DB 설계 개선

4. **N+1 쿼리** (#8)
   - 11번 쿼리 → 1번 쿼리로 최적화 (10배 쿼리 감소)
   - `select_related()`로 ORM 최적화 학습

5. **Django Debug Toolbar 설정** (#9)
   - 쿼리 분석 도구 부재 → Docker 환경에서도 정상 작동
   - 중복 쿼리 53% 발견 (15개 → 7-8개로 최적화 가능)

### 문제 해결 패턴 분석

**중요도별 분포**
1. 🔴 **Critical** (5건): 서비스 중단, 사용자 경험 직접 영향, 성능 최적화 도구 부재
2. 🟡 **High** (5건): 배포 안정성, 무중단 배포, 핵심 기능 장애, N+1 쿼리
3. 🟢 **Medium** (1건): 데이터 정합성

**기술 영역별 분포**
1. **인프라 계층** (4건): HTTPS, Health Check, Security Group, ALB Connection Draining
2. **데이터 계층** (3건): username/email, 트랜잭션, N+1 쿼리
3. **실시간 통신** (2건): WebSocket 연결, Nginx 프록시
4. **성능 최적화** (2건): Django Debug Toolbar 설정, 템플릿 태그 N+1 쿼리

### 재발 방지 전략

**자동화**
- Health check 엔드포인트 표준화
- CI/CD cleanup 단계 `if: always()` 적용
- Management Command 크론 자동화
- ALB Connection Draining 30초 대기 로직 자동화

**모니터링**
- Django Debug Toolbar로 쿼리 수 실시간 확인
- Docker logs로 컨테이너 상태 추적
- Browser DevTools Network 탭으로 WebSocket 연결 검증
- Locust 부하 테스트로 배포 중 에러율 측정

**문서화**
- 트러블슈팅 10건 문서화로 지식 체계화
- 코드 위치 링크로 추적성 확보

### 기술적 성장

- **프로덕션 환경 이해**: 개발과 배포 환경의 차이 (프록시, HTTPS, Health Check)
- **무중단 배포 설계**: ALB Connection Draining, Rolling Update 순서의 중요성
- **트랜잭션 설계**: 원자성, 일관성, 격리 수준 고려
- **성능 최적화**: N+1 쿼리 해결, ORM 최적화 기법
- **실시간 통신**: ASGI, WebSocket, Nginx 프로토콜 협상
- **데이터 기반 검증**: 부하 테스트로 추상적 목표("무중단")를 구체적 숫자로 증명

---

**작성일**: 2026년 1월 10일
**버전**: 2.5
**총 트러블슈팅 건수**: 11건 (Critical 5건, High 5건, Medium 1건)
