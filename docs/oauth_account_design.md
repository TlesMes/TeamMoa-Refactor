# TeamMoa OAuth 계정 관리 설계 문서

## 📋 목차
1. [개요](#1-개요)
2. [계정 모델 구조](#2-계정-모델-구조)
3. [주요 시나리오 및 시퀀스](#3-주요-시나리오-및-시퀀스)
4. [정책 및 설정](#4-정책-및-설정)
5. [데이터베이스 구조](#5-데이터베이스-구조)
6. [UX 가이드라인](#6-ux-가이드라인)
7. [보안 고려사항](#7-보안-고려사항)

---

## 1. 개요

### 1.1 목적
TeamMoa에서 Google OAuth를 통한 소셜 로그인 기능을 구현하면서, **사이트 계정**과 **소셜 계정**의 통합 관리 정책을 정의합니다.

### 1.2 대상
- 웹사이트 사용자 (신규/기존 회원)
- 사이트 관리자
- 개발자

### 1.3 목표
- OAuth 로그인/연동 시 보안 보장
- 사용자 편의성 극대화
- 계정 통합 관리 일관성 유지

---

## 2. 계정 모델 구조

### 2.1 사이트 계정 (User)

**모델 위치**: `accounts.models.User`

**핵심 필드**:
```python
class User(AbstractUser):
    username = models.CharField(max_length=150, unique=True)  # 핵심 식별자
    email = models.EmailField(unique=True)                     # OAuth 연동 시 중복 확인
    nickname = models.CharField(max_length=10)                 # 표시 이름
    profile = models.TextField(max_length=500)                 # 프로필 소개
```

**역할**:
- 모든 로그인/회원가입 활동의 **중심 주체**
- 팀 관리, 스케줄, 마인드맵, TODO 등 모든 기능과 연결
- 권한, 활동 기록, 팀 멤버십 정보 보유

### 2.2 소셜 계정 (SocialAccount)

**모델 위치**: `allauth.socialaccount.models.SocialAccount` (django-allauth 제공)

**핵심 필드**:
```python
class SocialAccount(models.Model):
    user = models.ForeignKey(User)              # 연결된 사이트 계정
    provider = models.CharField(max_length=30)  # 'google', 'github' 등
    uid = models.CharField(max_length=255)      # OAuth 제공자 고유 ID
    extra_data = models.JSONField()             # OAuth 프로필 정보 (email, name, picture 등)
```

**역할**:
- 사이트 계정과 외부 OAuth 계정의 **연결 매핑**
- 여러 OAuth 제공자 지원 (Google, GitHub 등)
- 한 사용자가 여러 소셜 계정 연동 가능

### 2.3 소셜 앱 (SocialApp)

**모델 위치**: `allauth.socialaccount.models.SocialApp` (django-allauth 제공)

**핵심 필드**:
```python
class SocialApp(models.Model):
    provider = models.CharField(max_length=30)  # 'google'
    name = models.CharField(max_length=40)      # 'Google OAuth'
    client_id = models.CharField(max_length=191) # Google Client ID
    secret = models.CharField(max_length=191)    # Google Client Secret
    sites = models.ManyToManyField(Site)         # 연결된 Django Site
```

**역할**:
- OAuth 제공자별 인증 정보 저장
- Django Admin에서 관리
- 환경변수 또는 DB에서 동적으로 로드

### 2.4 소셜 토큰 (SocialToken)

**모델 위치**: `allauth.socialaccount.models.SocialToken` (django-allauth 제공)

**역할**:
- OAuth Access Token 및 Refresh Token 저장
- 필요 시 Google API 호출에 사용 (예: Gmail, Calendar 연동)
- TeamMoa에서는 현재 프로필 정보만 사용하므로 토큰 저장은 선택적

---

## 3. 주요 시나리오 및 시퀀스

### 3.1 신규 사용자가 Google 로그인 시

**사용자 동선**:
1. 사용자가 [/accounts/login/](http://localhost:8000/accounts/login/)에서 "Google로 로그인" 버튼 클릭
2. Google OAuth 인증 화면으로 리다이렉트
3. Google 계정 선택 및 권한 동의
4. TeamMoa로 돌아와 자동 회원가입 및 로그인
5. [/teams/](http://localhost:8000/teams/) 페이지로 리다이렉트

**백엔드 처리 흐름**:
```
[User] --클릭 "Google로 로그인"--> [TeamMoa]
[TeamMoa] --OAuth 인증 요청--> [Google OAuth]
[Google OAuth] --인증 완료 (email, name, uid)--> [TeamMoa]
[TeamMoa] --SocialAccount 조회 (uid 기준)--> [DB]
[DB] --매칭 없음--> [TeamMoa]
[TeamMoa] --User 생성 (email 기반 username 생성)--> [DB]
[TeamMoa] --SocialAccount 생성 (user ↔ Google 연결)--> [DB]
[TeamMoa] --로그인 세션 생성--> [User]
[TeamMoa] --리다이렉트: /teams/--> [User]
```

**생성되는 데이터**:
```python
# User 생성
User.objects.create(
    username='user_google',  # Google 이메일 기반 자동 생성
    email='user@gmail.com',
    nickname='홍길동',        # Google 프로필의 given_name
    password=None             # OAuth 로그인은 비밀번호 불필요
)

# SocialAccount 생성
SocialAccount.objects.create(
    user=user,
    provider='google',
    uid='1234567890',  # Google 고유 ID
    extra_data={
        'email': 'user@gmail.com',
        'name': '홍길동',
        'picture': 'https://...',
        'given_name': '길동',
        'family_name': '홍'
    }
)
```

**설정**:
- `SOCIALACCOUNT_AUTO_SIGNUP = True` (자동 회원가입 허용)
- `ACCOUNT_EMAIL_REQUIRED = True` (이메일 필수)
- `ACCOUNT_EMAIL_VERIFICATION = 'optional'` (소셜 로그인은 이메일 인증 불필요)

---

### 3.2 기존 사용자가 Google 계정 연결 시

**사용자 동선**:
1. 사이트 계정으로 로그인
2. [/accounts/social-connections/](http://localhost:8000/accounts/social-connections/) 접속
3. "Google 계정 연결" 버튼 클릭
4. Google OAuth 인증 화면으로 리다이렉트
5. Google 계정 선택 및 권한 동의
6. TeamMoa로 돌아와 연결 완료 메시지 확인
7. 이후 Google 로그인으로 바로 접속 가능

**백엔드 처리 흐름**:
```
[User (로그인 상태)] --클릭 "Google 계정 연결"--> [TeamMoa]
[TeamMoa] --OAuth 인증 요청--> [Google OAuth]
[Google OAuth] --인증 완료 (uid, email)--> [TeamMoa]
[TeamMoa] --SocialAccount 조회 (uid 기준)--> [DB]
[DB] --기존 연결 없음--> [TeamMoa]
[TeamMoa] --이메일 중복 확인--> [DB]
[DB] --현재 로그인 사용자와 일치--> [TeamMoa]
[TeamMoa] --SocialAccount 생성 (user ↔ Google 연결)--> [DB]
[TeamMoa] --확인 메시지 표시--> [User]
```

**주의사항**:
- **보안상 로그인 상태에서만 연결 가능**
- 이미 다른 사용자가 연결한 Google 계정이면 연결 거부
- 사용자에게 명확한 에러 메시지 표시

**예외 처리**:
```python
# 이미 연결된 Google 계정인 경우
if SocialAccount.objects.filter(provider='google', uid=google_uid).exists():
    return error("이미 다른 계정에 연결된 Google 계정입니다.")

# 현재 사용자가 이미 Google 연결을 가진 경우
if SocialAccount.objects.filter(user=request.user, provider='google').exists():
    return error("이미 Google 계정이 연결되어 있습니다.")
```

---

### 3.3 이미 연결된 Google 계정으로 로그인 시

**사용자 동선**:
1. [/accounts/login/](http://localhost:8000/accounts/login/)에서 "Google로 로그인" 클릭
2. Google 인증 (이미 로그인된 경우 즉시 완료)
3. 기존 사이트 계정으로 자동 로그인
4. [/teams/](http://localhost:8000/teams/)로 리다이렉트

**백엔드 처리 흐름**:
```
[User] --클릭 "Google로 로그인"--> [TeamMoa]
[TeamMoa] --OAuth 인증 요청--> [Google OAuth]
[Google OAuth] --인증 완료 (uid)--> [TeamMoa]
[TeamMoa] --SocialAccount 조회 (uid 기준)--> [DB]
[DB] --매칭된 User 반환--> [TeamMoa]
[TeamMoa] --로그인 세션 생성--> [User]
[TeamMoa] --리다이렉트: /teams/--> [User]
```

**특징**:
- 가장 빠른 로그인 방식 (비밀번호 입력 불필요)
- Google에 이미 로그인되어 있으면 원클릭 로그인
- 보안: Google의 2FA/보안 정책 활용

---

### 3.4 동일 이메일로 사이트 계정과 Google 계정이 별도로 존재하는 경우

**시나리오**:
1. 사용자가 `user@gmail.com`으로 사이트 회원가입
2. 나중에 같은 `user@gmail.com`으로 Google 로그인 시도

**현재 정책** (권장):
- `SOCIALACCOUNT_AUTO_SIGNUP = True`
- **이메일 기반 자동 연결 활성화 필요** (`accounts/adapters.py` 커스터마이징)

**처리 방식**:
```python
# accounts/adapters.py
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter

class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    def pre_social_login(self, request, sociallogin):
        """Google 로그인 시 기존 사이트 계정과 자동 연결"""
        if sociallogin.is_existing:
            return

        try:
            user = User.objects.get(email=sociallogin.email_addresses[0].email)
            sociallogin.connect(request, user)  # 기존 계정에 연결
        except User.DoesNotExist:
            pass  # 신규 계정 생성 진행
```

**장점**:
- 사용자가 여러 계정을 가지는 것 방지
- UX 향상 (중복 계정 문제 해결)

**보안 주의사항**:
- Google OAuth는 이메일 인증을 Google이 보장하므로 안전
- 이메일 인증이 완료된 사이트 계정에만 자동 연결

---

## 4. 정책 및 설정

### 4.1 Django Allauth 설정 (base.py)

| 설정 항목 | 값 | 설명 |
|-----------|-----|------|
| `SITE_ID` | `1` | Django Sites Framework ID |
| `ACCOUNT_EMAIL_REQUIRED` | `True` | 이메일 필수 입력 |
| `ACCOUNT_USERNAME_REQUIRED` | `True` | username 필수 |
| `ACCOUNT_AUTHENTICATION_METHOD` | `'username_email'` | username 또는 email로 로그인 가능 |
| `ACCOUNT_EMAIL_VERIFICATION` | `'optional'` | 소셜 로그인은 이메일 인증 선택적 |
| `SOCIALACCOUNT_AUTO_SIGNUP` | `True` | 새 Google 계정 시 자동 회원가입 |
| `SOCIALACCOUNT_EMAIL_REQUIRED` | `True` | OAuth에서 이메일 필수 |
| `LOGIN_REDIRECT_URL` | `'/teams/'` | 로그인 후 리다이렉트 |
| `ACCOUNT_LOGOUT_REDIRECT_URL` | `'/accounts/login/'` | 로그아웃 후 리다이렉트 |

### 4.2 Google OAuth 설정

```python
SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'SCOPE': ['profile', 'email'],
        'AUTH_PARAMS': {'access_type': 'online'},
        'APP': {
            'client_id': env('GOOGLE_OAUTH_CLIENT_ID'),
            'secret': env('GOOGLE_OAUTH_CLIENT_SECRET'),
        }
    }
}
```

### 4.3 계정 연결 정책

| 상황(Situation)                    | 정책(Policy)                                | 비고(Note)                                              |
| -------------------------------- | ----------------------------------------- | ----------------------------------------------------- |
| Google OAuth로 신규 로그인, 기존 User 없음 | OAuth 정보 기반 User 자동 생성 + SocialAccount 연결 | `SOCIALACCOUNT_AUTO_SIGNUP=True`                      |
| 기존 사이트 계정이 있는 사용자가 Google 계정을 연결 | 로그인 후 계정 설정에서만 연결 허용                      | 비로그인 상태 연결 금지                                         |
| 이미 다른 계정에 연결된 Google 계정으로 연결 시도  | 연결 거부 + 사용자에게 에러 메시지 표시                   | SocialAccount 중복 방지                                   |
| OAuth 이메일이 기존 사이트 계정과 동일         | 이메일 기반 자동 연결                              | `CustomSocialAccountAdapter` 또는 `pre_social_login` 활용 |
| 연결된 소셜 계정 해제                     | 로그인 후 계정 설정에서 해제 가능                       | 최소 1개 로그인 방법 유지 필요                                    |


### 4.4 URL 구조

| URL | 용도 | 비고 |
|-----|------|------|
| `/accounts/login/` | 사이트 로그인 페이지 | Google 로그인 버튼 포함 |
| `/accounts/google/login/` | Google OAuth 시작 | django-allauth 자동 제공 |
| `/accounts/google/login/callback/` | Google OAuth 콜백 | Google Cloud Console에 등록 |
| `/accounts/social-connections/` | 소셜 계정 관리 | 연결/해제 UI |
| `/accounts/logout/` | 로그아웃 | 세션 삭제 후 로그인 페이지로 |

---

## 5. 데이터베이스 구조

### 5.1 ER 다이어그램

```
┌─────────────────────────┐
│ accounts.User           │
├─────────────────────────┤
│ id (PK)                 │
│ username (UNIQUE)       │◄───┐
│ email (UNIQUE)          │    │
│ nickname                │    │
│ profile                 │    │
│ password (Nullable)     │    │
│ is_active               │    │
└─────────────────────────┘    │
                               │
                               │ FK: user_id
                               │
┌─────────────────────────────┴─────┐
│ allauth.socialaccount.SocialAccount │
├───────────────────────────────────┤
│ id (PK)                           │
│ user_id (FK → User.id)            │
│ provider (VARCHAR)                │  'google', 'github' 등
│ uid (VARCHAR)                     │  Google 고유 ID
│ extra_data (JSON)                 │  OAuth 프로필 정보
│ UNIQUE(provider, uid)             │
└───────────────────────────────────┘
         │
         │ FK: account_id
         │
┌─────────────────────────────────┐
│ allauth.socialaccount.SocialToken │
├─────────────────────────────────┤
│ id (PK)                         │
│ account_id (FK)                 │
│ token (TEXT)                    │
│ token_secret (TEXT)             │
│ expires_at (DATETIME)           │
└─────────────────────────────────┘

┌───────────────────────────────┐
│ allauth.socialaccount.SocialApp │
├───────────────────────────────┤
│ id (PK)                       │
│ provider (VARCHAR)            │  'google'
│ name (VARCHAR)                │  'Google OAuth'
│ client_id (VARCHAR)           │
│ secret (VARCHAR)              │
│ sites (M2M → Site)            │
└───────────────────────────────┘
```

### 5.2 데이터 예시

**User 테이블**:
```sql
id | username      | email              | nickname | password
---|---------------|--------------------|-----------|---------
1  | user_site     | user@gmail.com     | 홍길동    | hashed_pw
2  | user_google   | test@gmail.com     | 김철수    | NULL
```

**SocialAccount 테이블**:
```sql
id | user_id | provider | uid         | extra_data
---|---------|----------|-------------|------------
1  | 2       | google   | 1234567890  | {"email": "test@gmail.com", "name": "김철수", ...}
```

**SocialApp 테이블** (Django Admin에서 설정):
```sql
id | provider | name         | client_id            | secret
---|----------|--------------|----------------------|--------
1  | google   | Google OAuth | abc123.apps.google... | secret_key
```

---

## 6. UX 가이드라인

### 6.1 로그인 페이지 ([accounts/login.html](d:/github/TeamMoa/accounts/templates/accounts/login.html))

**구성 요소**:
```html
┌───────────────────────────────────────┐
│         TeamMoa 로그인                │
├───────────────────────────────────────┤
│ Username:  [__________________]      │
│ Password:  [__________________]      │
│                                       │
│         [로그인]                      │
│                                       │
│ ──────── 또는 ────────                │
│                                       │
│    [🔵 Google로 로그인]               │
│                                       │
│  [회원가입]  [비밀번호 찾기]           │
└───────────────────────────────────────┘
```

**권장 문구**:
- "빠르고 안전한 Google 로그인"
- "Google 계정으로 3초만에 시작하기"

### 6.2 소셜 계정 관리 페이지 ([accounts/social-connections.html](d:/github/TeamMoa/accounts/templates/accounts/social_connections.html))

**구성 요소**:
```html
┌───────────────────────────────────────┐
│       연결된 소셜 계정                 │
├───────────────────────────────────────┤
│ 🔵 Google                             │
│    test@gmail.com                     │
│    연결일: 2025-10-12                 │
│    [연결 해제]                        │
├───────────────────────────────────────┤
│       새 계정 연결                     │
├───────────────────────────────────────┤
│ [🔵 Google 계정 연결]                 │
│ [🐙 GitHub 계정 연결] (준비 중)       │
└───────────────────────────────────────┘
```

**기능 요구사항**:
- ✅ 연결된 계정 목록 표시
- ✅ 연결 날짜 표시
- ✅ 연결 해제 버튼 (확인 모달 필수)
- ✅ 새 계정 연결 버튼
- ⚠️ 최소 1개 로그인 방법 유지 (마지막 계정 연결 해제 금지)

### 6.3 사용자 피드백 메시지

**성공 케이스**:
- ✅ "Google 계정이 성공적으로 연결되었습니다."
- ✅ "Google 로그인이 완료되었습니다. 환영합니다!"
- ✅ "Google 계정 연결이 해제되었습니다."

**에러 케이스**:
- ❌ "이미 다른 계정에 연결된 Google 계정입니다."
- ❌ "이미 Google 계정이 연결되어 있습니다."
- ❌ "최소 1개의 로그인 방법이 필요합니다. 연결 해제할 수 없습니다."
- ❌ "OAuth 인증에 실패했습니다. 다시 시도해주세요."

**구현 방법**:
```javascript
// static/js/common/ui-utils.js 활용
showDjangoToast('Google 계정이 연결되었습니다.', 'success');
showDjangoToast('이미 연결된 계정입니다.', 'error');
```

---

## 7. 보안 고려사항

### 7.1 인증 및 권한

| 보안 요소 | 구현 방법 | 비고 |
|-----------|----------|------|
| HTTPS 필수 | 운영 환경 필수 적용 | OAuth 리다이렉트 보안 |
| CSRF 보호 | Django 기본 CSRF 토큰 | `{% csrf_token %}` 사용 |
| OAuth State 검증 | django-allauth 자동 처리 | CSRF 공격 방지 |
| 계정 연결 권한 | `@login_required` 데코레이터 | 로그인 상태만 연결 가능 |
| 토큰 저장 보안 | DB 암호화 고려 | `SocialToken` 테이블 |

### 7.2 데이터 보호

**민감 정보 관리**:
```python
# .env 파일에 저장 (Git 제외)
GOOGLE_OAUTH_CLIENT_ID=abc123.apps.googleusercontent.com
GOOGLE_OAUTH_CLIENT_SECRET=secret_key_here

# settings/base.py
env = environ.Env()
client_id = env('GOOGLE_OAUTH_CLIENT_ID')
```

**로그 및 모니터링**:
```python
import logging
logger = logging.getLogger(__name__)

def social_login_callback(request):
    logger.info(f"OAuth login attempt: user_id={request.user.id}, provider=google")
```

### 7.3 계정 병합 보안

**이메일 인증 필수**:
- Google OAuth는 이메일 인증을 Google이 보장 ✅
- 사이트 계정 이메일은 `ACCOUNT_EMAIL_VERIFICATION = 'optional'` 설정
- 자동 병합 시 **이메일 인증 완료된 계정만** 허용

**중복 연결 방지**:
```python
# 이미 연결된 Google 계정 확인
if SocialAccount.objects.filter(provider='google', uid=google_uid).exists():
    raise ValidationError("이미 연결된 Google 계정입니다.")
```

### 7.4 세션 관리

| 설정 항목 | 값 | 설명 |
|-----------|-----|------|
| `SESSION_EXPIRE_AT_BROWSER_CLOSE` | `True` | 브라우저 종료 시 세션 삭제 |
| `SESSION_COOKIE_SECURE` | `True` (운영) | HTTPS에서만 쿠키 전송 |
| `SESSION_COOKIE_HTTPONLY` | `True` | JavaScript 접근 차단 |
| `SESSION_COOKIE_SAMESITE` | `'Lax'` | CSRF 공격 방지 |

### 7.5 OAuth Scope 최소화

**현재 설정**:
```python
'SCOPE': ['profile', 'email']
```

**권장 사항**:
- ✅ 필수 정보만 요청 (프로필, 이메일)
- ❌ 불필요한 권한 요청 금지 (Gmail, Calendar 등)
- 📌 추후 기능 확장 시 사용자 동의 재요청

---

## 8. 다중 OAuth 제공자 지원

### 8.1 확장 계획

**현재 지원**:
- ✅ Google OAuth 2.0

**향후 추가 예정**:
- 🔜 GitHub OAuth
- 🔜 Kakao OAuth
- 🔜 Naver OAuth

### 8.2 다중 소셜 계정 연결

**시나리오**:
- 한 사용자가 Google + GitHub 동시 연결 가능
- 어떤 방법으로든 로그인 가능

**DB 구조**:
```sql
user_id | provider | uid
--------|----------|------------
1       | google   | 1234567890
1       | github   | octocat_123
```

**UX**:
```
연결된 계정:
- 🔵 Google (user@gmail.com)
- 🐙 GitHub (octocat)

새 계정 연결:
- [Kakao 계정 연결]
```

---

## 9. 구현 체크리스트

### 9.1 백엔드 구현
- [x] `django-allauth` 설치 및 설정
- [x] Google OAuth 설정 (Client ID, Secret)
- [x] `SOCIALACCOUNT_AUTO_SIGNUP = True` 설정
- [ ] `accounts/adapters.py` 커스터마이징 (이메일 기반 자동 연결)
- [ ] 소셜 계정 연결/해제 뷰 구현 ([accounts/views.py:social_connections](d:/github/TeamMoa/accounts/views.py))
- [ ] 최소 1개 로그인 방법 유지 검증 로직

### 9.2 프론트엔드 구현
- [x] 로그인 페이지 Google 버튼 추가 ([accounts/login.html](d:/github/TeamMoa/accounts/templates/accounts/login.html))
- [ ] 소셜 계정 관리 페이지 UI ([accounts/social_connections.html](d:/github/TeamMoa/accounts/templates/accounts/social_connections.html))
- [ ] 연결 해제 확인 모달 (`showConfirmModal` 활용)
- [ ] 토스트 알림 통합 (`showDjangoToast` 활용)

### 9.3 보안 및 테스트
- [ ] HTTPS 적용 (운영 환경)
- [ ] CSRF 토큰 검증
- [ ] OAuth State 파라미터 검증
- [ ] 중복 연결 방지 테스트
- [ ] 계정 병합 시나리오 테스트
- [ ] 로그인/로그아웃 플로우 테스트

---

## 10. 참고 문서

- [Google OAuth 2.0 설정 가이드](./oauth_setup_guide.md)
- [django-allauth 공식 문서](https://django-allauth.readthedocs.io/)
- [TeamMoa 프로젝트 메모](../CLAUDE.md)

---

*최종 업데이트: 2025.10.13*
