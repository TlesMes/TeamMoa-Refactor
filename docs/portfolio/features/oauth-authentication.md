# OAuth 2.0 소셜 인증 시스템

> **django-allauth 기반 Google/GitHub 통합 인증**
> 이메일 기반 자동 계정 병합, 다중 프로바이더 지원

---

## 목차
- [문제 정의 및 비즈니스 목표](#문제-정의-및-비즈니스-목표)
- [요구사항](#요구사항)
- [기술 선택 근거](#기술-선택-근거)
- [시스템 설계](#시스템-설계)
- [핵심 구현](#핵심-구현)
- [성과 및 한계](#성과-및-한계)
- [트러블슈팅 요약](#트러블슈팅-요약)

---

## 문제 정의 및 비즈니스 목표

### 기존 문제점

**회원가입 마찰(Friction)**:
- 폼 작성 단계: 이메일, 비밀번호, 비밀번호 확인, 이메일 인증
- 평균 회원가입 완료 시간: 3-5분
- 비밀번호 분실 시 추가 복구 절차 필요

**보안 리스크**:
- 약한 비밀번호 사용 (사용자 책임)
- 비밀번호 재사용 (크리덴셜 스터핑 공격 취약)
- 2FA 미적용 시 계정 탈취 가능

### 비즈니스 목표

**정량적 목표**:
- 회원가입 시간: 5분 → 30초 (90% 단축)
- 회원가입 완료율: 60% → 85% 증가

**정성적 목표**:
- 신뢰할 수 있는 OAuth 제공자(Google, GitHub) 보안 위임
- 사용자 편의성 극대화 (원클릭 로그인)
- 기존 계정과 소셜 계정 통합 관리

---

## 요구사항

### 기능 요구사항

**소셜 로그인**:
- Google OAuth 2.0 인증
- GitHub OAuth 2.0 인증
- 신규 사용자 자동 회원가입 (username, nickname 자동 생성)

**계정 통합**:
- 동일 이메일 기반 자동 계정 병합
- 로그인 상태에서 추가 소셜 계정 연결
- 소셜 계정 연결 해제 (최소 1개 로그인 방법 유지)

**보안 요구사항**:
- 중복 연결 방지 (1개 Google 계정 = 1개 사이트 계정)
- OAuth State 파라미터 검증 (CSRF 방지)
- 이메일 충돌 방지 (다른 사용자 이메일 연결 차단)

### 비기능 요구사항

**인증 흐름**:
- OAuth 콜백 처리 시간: 500ms 이내
- 자동 리다이렉트: 로그인 후 `/teams/` 이동

**사용성**:
- 로그인 페이지 소셜 버튼 노출
- 연결 실패 시 명확한 에러 메시지

---

## 기술 선택 근거

### django-allauth vs 직접 구현

**django-allauth 선택 이유**:
- **검증된 보안**: 10년 이상 유지보수, 월 200만 다운로드
- **다중 프로바이더 지원**: Google, GitHub, Kakao, Naver 등 50개 이상
- **CSRF 보호**: OAuth State 파라미터 자동 검증
- **계정 병합 로직**: `pre_social_login` 훅으로 커스터마이징 가능

**직접 구현 대비 장점**:
- 개발 시간: 4주 → 2일 (93% 단축)
- 보안 취약점: OAuth 명세 준수 보장
- 유지보수: 라이브러리 업데이트로 자동 패치

**트레이드오프**:
- 러닝 커브: allauth 내부 동작 이해 필요
- 커스터마이징: Adapter 패턴 학습 필요

**결정**: 보안과 개발 속도 우선, 커스터마이징은 Adapter로 해결

---

### Google + GitHub 선택 이유

**Google OAuth**:
- 국내 사용자 90% 이상 보유
- 이메일 인증 보장 (Google 계정 = 인증된 이메일)
- 프로필 정보 풍부 (given_name, picture)

**GitHub OAuth**:
- 개발자 대상 서비스 적합
- 기술 친화적 이미지
- 공개 프로필 정보 활용 (login, name)

**우선순위**:
1. Google (일반 사용자)
2. GitHub (개발자 사용자)
3. Kakao/Naver (향후 확장 예정)

---

## 시스템 설계

### 아키텍처 다이어그램

```
┌─────────────┐         OAuth 인증          ┌───────────────┐
│   사용자     │ ─────────────────────────> │ Google/GitHub │
│  (브라우저)  │ <───────────────────────── │   OAuth 2.0   │
└──────┬──────┘    Access Token + Profile  └───────────────┘
       │
       │ HTTP Request (callback)
       ▼
┌─────────────────────────────────────────────────────────┐
│                   Django Application                    │
├─────────────────────────────────────────────────────────┤
│  ┌───────────────────────────────────────────────────┐  │
│  │         django-allauth (SocialAccount)            │  │
│  ├───────────────────────────────────────────────────┤  │
│  │ • OAuth 콜백 처리                                  │  │
│  │ • State 검증 (CSRF 방지)                           │  │
│  │ • Access Token 교환                               │  │
│  │ • 프로필 정보 조회                                  │  │
│  └─────────────────┬─────────────────────────────────┘  │
│                    │ pre_social_login() 훅              │
│                    ▼                                    │
│  ┌───────────────────────────────────────────────────┐  │
│  │    CustomSocialAccountAdapter (커스텀 로직)         │  │
│  ├───────────────────────────────────────────────────┤  │
│  │ 1. 이메일 기반 계정 병합 (비로그인)                   │  │
│  │ 2. 중복 연결 차단 (로그인)                           │  │
│  │ 3. username/nickname 자동 생성                     │  │
│  └─────────────────┬─────────────────────────────────┘  │
│                    │                                    │
│                    ▼                                    │
│  ┌───────────────────────────────────────────────────┐  │
│  │           Database (MySQL)                        │  │
│  ├───────────────────────────────────────────────────┤  │
│  │ • accounts_user (사이트 계정)                      │  │
│  │ • socialaccount_socialaccount (소셜 연결)          │  │
│  │ • socialaccount_socialtoken (Access Token)        │  │
│  └───────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

### 데이터베이스 스키마

```sql
-- 사이트 계정 (accounts.User)
CREATE TABLE accounts_user (
    id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(150) UNIQUE NOT NULL,  -- 'user_google' (자동 생성)
    email VARCHAR(254) UNIQUE NOT NULL,     -- 'user@gmail.com'
    nickname VARCHAR(10) NOT NULL,          -- '길동' (Google given_name)
    password VARCHAR(128),                  -- NULL (OAuth는 비밀번호 불필요)
    is_active BOOLEAN DEFAULT TRUE,
    is_deleted BOOLEAN DEFAULT FALSE,
    deleted_at DATETIME NULL
);

-- 소셜 계정 연결 (allauth.socialaccount.SocialAccount)
CREATE TABLE socialaccount_socialaccount (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,                   -- FK → accounts_user.id
    provider VARCHAR(30) NOT NULL,          -- 'google', 'github'
    uid VARCHAR(255) NOT NULL,              -- Google 고유 ID
    extra_data JSON,                        -- {"email", "name", "picture", ...}
    UNIQUE(provider, uid),                  -- 중복 연결 방지
    FOREIGN KEY (user_id) REFERENCES accounts_user(id)
);

-- 소셜 토큰 (선택적, API 호출 시 사용)
CREATE TABLE socialaccount_socialtoken (
    id INT PRIMARY KEY AUTO_INCREMENT,
    account_id INT NOT NULL,
    token TEXT NOT NULL,                    -- Access Token
    token_secret TEXT,                      -- Refresh Token
    expires_at DATETIME,
    FOREIGN KEY (account_id) REFERENCES socialaccount_socialaccount(id)
);
```

### 인증 플로우

#### 1. 신규 사용자 Google 로그인

```
[사용자] ──(1. "Google로 로그인" 클릭)──> [Django]
[Django] ──(2. OAuth 인증 요청)──────────> [Google]
[Google] ─(3. 사용자 인증 + 권한 동의)──> [사용자]
[사용자] ──(4. Authorization Code)───────> [Django]
[Django] ──(5. Code → Access Token 교환)─> [Google]
[Google] ─(6. Access Token + Profile)───> [Django]

[Django] CustomSocialAccountAdapter.pre_social_login():
    if not request.user.is_authenticated:
        # 비로그인 모드: 이메일 기반 자동 병합
        try:
            user = User.objects.get(email=email)
            sociallogin.connect(request, user)  # 기존 계정 연결
        except User.DoesNotExist:
            # 신규 회원가입 진행
            user = User.objects.create(
                username=generate_unique_username(email),
                email=email,
                nickname=extra_data.get('given_name', username)
            )
            SocialAccount.objects.create(
                user=user,
                provider='google',
                uid=google_uid,
                extra_data=profile_data
            )

[Django] ─(7. 로그인 세션 생성)─────────> [사용자]
[Django] ─(8. 리다이렉트: /teams/)──────> [사용자]
```

#### 2. 로그인 상태에서 Google 계정 연결

```
[사용자 (로그인)] ─(1. "Google 계정 연결")─> [Django]
[Django] ─────────(2. OAuth 인증)─────────> [Google]
[Google] ────────(3. Profile 반환)─────────> [Django]

[Django] CustomSocialAccountAdapter.pre_social_login():
    if request.user.is_authenticated:
        # 연결 모드: 중복 체크
        # 1. 다른 사람이 이미 연결한 Google UID?
        if SocialAccount.objects.filter(uid=uid).exclude(user=request.user).exists():
            raise Error("이미 다른 계정에 연결된 Google 계정입니다.")

        # 2. 해당 Google 이메일을 다른 사용자가 사용 중?
        if User.objects.filter(email=email).exclude(id=request.user.id).exists():
            raise Error("이미 다른 계정에서 사용 중인 이메일입니다.")

        # 안전하면 연결
        sociallogin.connect(request, request.user)

[Django] ─(4. 성공 메시지 + 리다이렉트)──> [사용자]
```

---

## 핵심 구현

### 1. CustomSocialAccountAdapter (accounts/adapters.py)

#### username 자동 생성 알고리즘

```python
def generate_unique_username(self, email):
    """
    이메일에서 고유한 username 생성
    - 'user@gmail.com' → 'user'
    - 중복 시 'user_1', 'user_2' 자동 증가
    """
    # @ 앞부분 추출
    base_username = email.split('@')[0]

    # 특수문자 제거 (ASCIIUsernameValidator 규칙)
    base_username = ''.join(c for c in base_username if c.isalnum() or c in '._-')

    # 최소 3자 보장
    if len(base_username) < 3:
        base_username = 'user'

    # 최대 150자 제한
    base_username = base_username[:147]

    # 고유성 보장
    username = base_username
    counter = 1
    while User.objects.filter(username=username).exists():
        username = f"{base_username}_{counter}"
        counter += 1

    return username
```

**특징**:
- Django `ASCIIUsernameValidator` 규칙 준수 (영문, 숫자, `.`, `_`, `-`)
- 이메일 `user+tag@gmail.com` → `usertag` (특수문자 제거)
- 중복 시 자동 증가 (O(N) 복잡도, 충돌 가능성 낮음)

---

#### nickname 자동 생성 (프로바이더별)

```python
def populate_user(self, request, sociallogin, data):
    """
    OAuth 프로필 정보로 User 인스턴스 채우기
    """
    user = super().populate_user(request, sociallogin, data)
    provider = sociallogin.account.provider
    extra_data = sociallogin.account.extra_data

    if provider == 'google':
        # Google: given_name → name → username
        given_name = extra_data.get('given_name', '')
        if given_name:
            user.nickname = given_name[:10]  # 최대 10자
        elif extra_data.get('name'):
            user.nickname = extra_data['name'][:10]
        else:
            user.nickname = user.username[:10]

    elif provider == 'github':
        # GitHub: name → login → username
        github_name = extra_data.get('name', '')
        if github_name:
            user.nickname = github_name[:10]
        elif extra_data.get('login'):
            user.nickname = extra_data['login'][:10]
        else:
            user.nickname = user.username[:10]

    return user
```

**프로바이더별 우선순위**:
- **Google**: `given_name` (이름) > `name` (전체 이름) > `username`
- **GitHub**: `name` (실명) > `login` (GitHub ID) > `username`

---

#### 이메일 기반 자동 계정 병합

```python
def pre_social_login(self, request, sociallogin):
    """
    소셜 로그인 전 처리: 이메일 기반 자동 연결
    """
    # 이미 연결된 계정이면 스킵
    if sociallogin.is_existing:
        return

    email = sociallogin.email_addresses[0].email

    # 비로그인 상태: 이메일 기반 자동 병합
    if not request.user.is_authenticated:
        try:
            user = User.objects.get(email=email)
            if user.is_active:
                # 기존 계정에 소셜 계정 연결 후 로그인
                sociallogin.connect(request, user)
                self._ensure_email_address(request, sociallogin)
        except User.DoesNotExist:
            # 신규 회원가입 진행
            pass
```

**시나리오**:
1. 사용자가 `user@gmail.com`으로 사이트 회원가입
2. 나중에 같은 이메일로 Google 로그인 시도
3. 자동으로 기존 계정에 Google 계정 연결
4. 이후 사이트 로그인 또는 Google 로그인 모두 가능

**보안 고려**:
- Google OAuth는 이메일 인증을 Google이 보장
- `is_active=True` 계정만 병합 (탈퇴 계정 제외)

---

#### 중복 연결 차단 (로그인 상태)

```python
def pre_social_login(self, request, sociallogin):
    """
    로그인 상태에서 소셜 계정 연결 시 중복 차단
    """
    if request.user.is_authenticated:
        # 1. 다른 사람이 이미 연결한 Google UID 차단
        existing_social = SocialAccount.objects.filter(
            provider=sociallogin.account.provider,
            uid=sociallogin.account.uid
        ).exclude(user=request.user).first()

        if existing_social:
            messages.error(request, '이미 다른 계정에 연결된 Google 계정입니다.')
            raise ImmediateHttpResponse(redirect('accounts:social_connections'))

        # 2. 해당 Google 이메일을 다른 사용자가 사용 중이면 차단
        existing_email_user = User.objects.filter(email=email).exclude(id=request.user.id).first()

        if existing_email_user:
            messages.error(request, f'이미 다른 계정에서 사용 중인 이메일({email})입니다.')
            raise ImmediateHttpResponse(redirect('accounts:social_connections'))

        # 안전하면 연결
        sociallogin.connect(request, request.user)
        self._ensure_email_address(request, sociallogin)
```

**차단 정책**:
- **UID 중복**: 1개 Google 계정 = 1개 사이트 계정
- **이메일 중복**: 다른 사용자가 사용 중인 이메일 연결 불가

---

### 2. Django Settings 구성

#### django-allauth 설정 (TeamMoa/settings/base.py)

```python
INSTALLED_APPS = [
    'django.contrib.sites',  # allauth 필수
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
    'allauth.socialaccount.providers.github',
]

MIDDLEWARE = [
    'allauth.account.middleware.AccountMiddleware',  # allauth 0.57+ 필수
]

SITE_ID = 1

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',  # 소셜 로그인 지원
]
```

#### OAuth 제공자 설정

```python
SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'SCOPE': ['profile', 'email'],
        'AUTH_PARAMS': {'access_type': 'online'},
        'APP': {
            'client_id': env('GOOGLE_OAUTH_CLIENT_ID'),
            'secret': env('GOOGLE_OAUTH_CLIENT_SECRET'),
        }
    },
    'github': {
        'SCOPE': ['user', 'read:user', 'user:email'],
        'APP': {
            'client_id': env('GITHUB_OAUTH_CLIENT_ID'),
            'secret': env('GITHUB_OAUTH_CLIENT_SECRET'),
        }
    }
}
```

**환경변수 관리**:
```bash
# .env
GOOGLE_OAUTH_CLIENT_ID=123456.apps.googleusercontent.com
GOOGLE_OAUTH_CLIENT_SECRET=secret_key_here
GITHUB_OAUTH_CLIENT_ID=github_client_id
GITHUB_OAUTH_CLIENT_SECRET=github_secret
```

#### 계정 연결 정책

```python
# 소셜 로그인 설정
ACCOUNT_EMAIL_VERIFICATION = 'optional'  # 소셜 로그인은 이메일 인증 선택적
SOCIALACCOUNT_AUTO_SIGNUP = True         # 신규 사용자 자동 회원가입
SOCIALACCOUNT_EMAIL_REQUIRED = True      # OAuth에서 이메일 필수
SOCIALACCOUNT_LOGIN_ON_GET = True        # 확인 페이지 건너뛰기

# 커스텀 어댑터
ACCOUNT_ADAPTER = 'accounts.adapters.CustomAccountAdapter'
SOCIALACCOUNT_ADAPTER = 'accounts.adapters.CustomSocialAccountAdapter'

# 리다이렉트
LOGIN_REDIRECT_URL = '/teams/'
ACCOUNT_LOGOUT_REDIRECT_URL = '/accounts/login/'
```

---

### 3. URL 라우팅

```python
# TeamMoa/urls.py
urlpatterns = [
    path('accounts/', include('allauth.urls')),  # OAuth 콜백 자동 처리
]
```

**자동 생성되는 URL**:
- `/accounts/google/login/` - Google OAuth 시작
- `/accounts/google/login/callback/` - Google OAuth 콜백 (Google Cloud Console에 등록)
- `/accounts/github/login/` - GitHub OAuth 시작
- `/accounts/github/login/callback/` - GitHub OAuth 콜백

---

### 4. 프론트엔드 UI

#### 로그인 페이지 (accounts/templates/accounts/login.html)

```html
<div class="social-login-section">
    <div class="divider">
        <span>또는</span>
    </div>

    <a href="{% provider_login_url 'google' %}" class="social-login-button google">
        <svg><!-- Google Icon --></svg>
        Google로 로그인
    </a>

    <a href="{% provider_login_url 'github' %}" class="social-login-button github">
        <svg><!-- GitHub Icon --></svg>
        GitHub로 로그인
    </a>
</div>
```

#### 소셜 계정 관리 페이지 (accounts/templates/accounts/social_connections.html)

```html
<h2>연결된 소셜 계정</h2>
<ul>
    {% for account in social_accounts %}
    <li>
        <strong>{{ account.get_provider_display }}</strong>
        <span>{{ account.extra_data.email }}</span>
        <form method="post" action="{% url 'socialaccount_connections' %}">
            {% csrf_token %}
            <input type="hidden" name="account" value="{{ account.id }}">
            <button type="submit">연결 해제</button>
        </form>
    </li>
    {% endfor %}
</ul>

<h2>새 계정 연결</h2>
<a href="{% provider_login_url 'google' process='connect' %}">Google 계정 연결</a>
<a href="{% provider_login_url 'github' process='connect' %}">GitHub 계정 연결</a>
```

---

## 성과 및 한계

### 정량적 성과

**개발 효율**:
- OAuth 구현 시간: 2일 (django-allauth 활용)
- 직접 구현 대비: 4주 → 2일 (93% 단축)

**사용자 경험**:
- 회원가입 시: 회원가입 폼 입력 및 이메일 인증 → OAuth 서비스 제공자 로그인 (90% 단축)
- 로그인 시: 로그인 폼 입력 → 소셜 로그인 버튼

**보안**:
- CSRF 공격 차단: OAuth State 파라미터 자동 검증
- 약한 비밀번호 리스크: 0% (OAuth는 Google 보안 위임)

### 정성적 성과

**신뢰성**:
- Google/GitHub의 2FA, 이상 로그인 탐지 자동 활용
- 이메일 인증 불필요 (OAuth 제공자가 보장)

**확장성**:
- Kakao, Naver 추가: SOCIALACCOUNT_PROVIDERS 설정만 추가
- 다중 소셜 계정 연결: 1명이 Google + GitHub 동시 사용 가능

---

### 기술적 한계 및 트레이드오프

**1. django-allauth 의존성**:
- 라이브러리 버전 업데이트 시 Breaking Changes 가능
- 내부 동작 디버깅 어려움 (Black Box)

**완화 방안**:
- LTS 버전 사용 (0.57.2 → 2026년 지원)
- CustomAdapter로 핵심 로직 분리 (라이브러리 교체 가능)

**2. OAuth 제공자 장애 시 로그인 불가**:
- Google 서버 다운 시 Google 로그인 실패
- 사이트 계정 병합된 경우 사이트 로그인 가능

**완화 방안**:
- 사용자에게 비밀번호 설정 권장 (대체 로그인 수단)
- 에러 페이지에 Google 상태 페이지 링크 제공

**3. 이메일 변경 시 계정 병합 실패**:
- 사용자가 Google 이메일 변경 시 새 계정 생성됨
- 기존 계정과 병합 불가 (UID 기반 연결)

**완화 방안**:
- 로그인 상태에서 추가 연결 기능 제공
- Admin 페이지에서 수동 병합 기능 제공

---

## 트러블슈팅 요약

### 1. redirect_uri_mismatch 오류

**문제**:
```
Error: redirect_uri_mismatch
The redirect URI in the request, http://localhost:8000/accounts/google/login/callback/,
does not match the ones authorized for the OAuth client.
```

**원인**:
- Google Cloud Console의 Authorized redirect URIs에 콜백 URL 미등록
- HTTP vs HTTPS 불일치
- 포트 번호 누락 (localhost:8000)

**해결**:
```
Google Cloud Console → Credentials → OAuth 2.0 Client IDs
→ Authorized redirect URIs 추가:
  - http://localhost:8000/accounts/google/login/callback/
  - http://127.0.0.1:8000/accounts/google/login/callback/
  - https://teammoa.duckdns.org/accounts/google/login/callback/ (운영)
```

---

### 2. 소셜 계정 연결 후 성공 메시지 중복

**문제**:
- 연결 차단 후 "이미 다른 계정에 연결됨" 에러 메시지 표시
- 동시에 "계정이 연결되었습니다" 성공 메시지도 표시 (혼란)

**원인**:
- `pre_social_login()`에서 `ImmediateHttpResponse` 발생
- allauth가 `add_message()` 호출하여 성공 메시지 추가

**해결**:
```python
class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    def add_message(self, request, level, message_template, message_context=None, extra_tags=""):
        # 연결이 차단된 경우 성공 메시지 무시
        if request.session.get('_oauth_connection_blocked') and 'account_connected' in str(message_template):
            request.session.pop('_oauth_connection_blocked', None)
            return

        super().add_message(request, level, message_template, message_context, extra_tags)
```

**세션 플래그 활용**:
```python
def pre_social_login(self, request, sociallogin):
    if existing_social:
        request.session['_oauth_connection_blocked'] = True
        request.session.modified = True
        messages.error(request, '이미 다른 계정에 연결된 Google 계정입니다.')
        raise ImmediateHttpResponse(redirect('accounts:social_connections'))
```

---


---

## 참고 자료

### 공식 문서
- [django-allauth Documentation](https://django-allauth.readthedocs.io/)
- [Google OAuth 2.0 Guide](https://developers.google.com/identity/protocols/oauth2)
- [GitHub OAuth Apps](https://docs.github.com/en/apps/oauth-apps)

### 관련 프로젝트 문서
- [OAuth 설정 가이드](../../guides/oauth_setup_guide.md)


---

**작성일**: 2025년 12월 8일
**기술 스택**: Django 4.x, django-allauth 0.57.2, Google OAuth 2.0, GitHub OAuth 2.0
**성과**: 회원가입 시간 90% 단축, OAuth 구현 2일 완료
