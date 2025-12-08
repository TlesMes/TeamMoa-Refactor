# OAuth 2.0 소셜 로그인 설정 가이드 (Google + GitHub)

## 📋 목차
1. [Google OAuth 설정](#1-google-oauth-설정)
2. [GitHub OAuth 설정](#2-github-oauth-설정)
3. [Django 프로젝트 설정](#3-django-프로젝트-설정)
4. [어드민 페이지 설정](#4-어드민-페이지-설정)
5. [테스트 방법](#5-테스트-방법)
6. [문제 해결](#6-문제-해결)

---

## 1. Google OAuth 설정

### 1.1 프로젝트 생성 및 OAuth 동의 화면 설정

1. **Google Cloud Console 접속**
   - https://console.cloud.google.com/ 접속
   - 로그인 후 프로젝트 선택 또는 새 프로젝트 생성

2. **OAuth 동의 화면 구성**
   ```
   좌측 메뉴 → APIs & Services → OAuth consent screen
   ```

   - **User Type**: External 선택
   - **앱 이름**: TeamMoa
   - **사용자 지원 이메일**: 본인 이메일
   - **개발자 연락처 정보**: 본인 이메일
   - **범위 추가**:
     - `../auth/userinfo.email`
     - `../auth/userinfo.profile`
     - `openid`
   - **테스트 사용자 추가**: 개발/테스트에 사용할 Google 계정 추가

3. **OAuth 2.0 클라이언트 ID 생성**
   ```
   좌측 메뉴 → APIs & Services → Credentials → Create Credentials → OAuth client ID
   ```

   - **Application type**: Web application
   - **Name**: TeamMoa Web Client
   - **Authorized JavaScript origins**:
     ```
     http://localhost:8000
     http://127.0.0.1:8000
     ```
   - **Authorized redirect URIs**:
     ```
     http://localhost:8000/accounts/google/login/callback/
     http://127.0.0.1:8000/accounts/google/login/callback/
     ```

4. **Client ID와 Client Secret 저장**
   - 생성 완료 후 표시되는 **Client ID**와 **Client Secret**을 안전하게 복사
   - 이 값들은 `.env` 파일에 저장됩니다

---

## 2. GitHub OAuth 설정

### 2.1 GitHub OAuth App 등록

1. **GitHub Developer Settings 접속**
   - https://github.com/settings/developers
   - 로그인 후 **OAuth Apps** 클릭

2. **New OAuth App 생성**
   ```
   New OAuth App 버튼 클릭
   ```

   - **Application name**: TeamMoa (Development)
   - **Homepage URL**: `http://localhost:8000`
   - **Application description**: (선택사항) TeamMoa 팀 협업 플랫폼
   - **Authorization callback URL**:
     ```
     http://localhost:8000/accounts/github/login/callback/
     ```
   - **Register application** 클릭

3. **Client ID와 Client Secret 생성**
   - 생성 완료 후 **Client ID** 자동 표시
   - **Generate a new client secret** 버튼 클릭
   - **Client Secret** 복사 (⚠️ 한 번만 표시되므로 즉시 복사!)

4. **환경변수 저장**
   `.env` 파일에 GitHub OAuth 정보 추가:
   ```env
   # GitHub OAuth 2.0
   GITHUB_OAUTH_CLIENT_ID=your-github-client-id
   GITHUB_OAUTH_CLIENT_SECRET=your-github-client-secret
   ```

### 2.2 권한 범위 (Scopes)
TeamMoa는 다음 GitHub 권한을 요청합니다:
- `user`: 사용자 프로필 정보 (이름, username)
- `read:user`: 사용자 정보 읽기
- `user:email`: 이메일 주소 접근

---

## 3. Django 프로젝트 설정

### 3.1 환경변수 설정

`.env` 파일에 OAuth 정보 추가:

```env
# Google OAuth 2.0
GOOGLE_OAUTH_CLIENT_ID=your-client-id-here.apps.googleusercontent.com
GOOGLE_OAUTH_CLIENT_SECRET=your-client-secret-here

# GitHub OAuth 2.0
GITHUB_OAUTH_CLIENT_ID=your-github-client-id
GITHUB_OAUTH_CLIENT_SECRET=your-github-client-secret
```

### 3.2 패키지 설치 (이미 완료)

```bash
pip install django-allauth
```

### 3.3 설정 확인

`TeamMoa/settings/base.py`에 다음 설정이 추가되었는지 확인:

```python
INSTALLED_APPS = [
    # ...
    'django.contrib.sites',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
    'allauth.socialaccount.providers.github',  # GitHub 추가
    # ...
]

MIDDLEWARE = [
    # ...
    'allauth.account.middleware.AccountMiddleware',
]

SITE_ID = 1

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]
```

---

## 4. 어드민 페이지 설정

### 4.1 마이그레이션 실행

```bash
python manage.py migrate
```

### 4.2 Django Admin에서 Sites 설정

1. **관리자 계정으로 로그인**
   ```
   http://localhost:8000/admin/
   ```

2. **Sites 설정 확인**
   ```
   Sites → Site ID 1 → Domain name 변경
   ```
   - Domain name: `localhost:8000` 또는 `127.0.0.1:8000`
   - Display name: `TeamMoa Local`

### 4.3 Social Applications 설정 (선택사항)

> **참고**: TeamMoa는 `settings/base.py`의 `SOCIALACCOUNT_PROVIDERS` 설정을 사용하므로, Admin에서 Social Application을 추가하지 않아도 동작합니다.

Admin에서 관리하고 싶다면:

1. **Google Social Application 추가**
   ```
   Social applications → Add social application
   ```
   - **Provider**: Google
   - **Name**: Google OAuth
   - **Client id**: Google Cloud Console에서 생성한 Client ID
   - **Secret key**: Google Cloud Console에서 생성한 Client Secret
   - **Sites**: `localhost:8000` 선택하여 Chosen sites로 이동
   - **Save** 클릭

2. **GitHub Social Application 추가**
   ```
   Social applications → Add social application
   ```
   - **Provider**: GitHub
   - **Name**: GitHub OAuth
   - **Client id**: GitHub에서 생성한 Client ID
   - **Secret key**: GitHub에서 생성한 Client Secret
   - **Sites**: `localhost:8000` 선택하여 Chosen sites로 이동
   - **Save** 클릭

---

## 5. 테스트 방법

### 5.1 로그인 페이지 접속

```
http://localhost:8000/accounts/login/
```

### 5.2 소셜 로그인 테스트

#### Google로 로그인
- "Google로 로그인" 버튼 클릭
- Google 계정 선택
- TeamMoa 앱에 대한 권한 허용
- 자동으로 로그인 및 `/teams/` 페이지로 리다이렉트

#### GitHub으로 로그인
- "GitHub으로 로그인" 버튼 클릭
- GitHub 계정 인증
- TeamMoa 앱에 대한 권한 허용 (이메일 접근 포함)
- 자동으로 로그인 및 `/teams/` 페이지로 리다이렉트

### 5.3 소셜 계정 연결 관리

로그인 후 다음 페이지에서 추가 소셜 계정 연결/해제 가능:
```
http://localhost:8000/accounts/social-connections/
```

### 5.4 확인 사항

1. **사용자 생성 확인**
   - Admin 페이지 → Users에서 소셜 계정으로 생성된 사용자 확인
   - username은 이메일 주소 기반으로 자동 생성
   - nickname은 프로바이더별로 자동 생성:
     - Google: `given_name` → `name` → `username`
     - GitHub: `name` → `login` → `username`

2. **소셜 계정 연결 확인**
   - Admin 페이지 → Social accounts에서 연결된 계정 확인

---

## 6. 문제 해결

### 6.1 "redirect_uri_mismatch" 오류

**원인**: OAuth 앱 설정의 Redirect URI와 실제 요청 URI가 다름

**해결방법**:

#### Google
1. Google Cloud Console → Credentials → OAuth 2.0 Client IDs 클릭
2. Authorized redirect URIs에 다음 추가:
   ```
   http://localhost:8000/accounts/google/login/callback/
   http://127.0.0.1:8000/accounts/google/login/callback/
   ```
3. 변경사항 저장 (최대 5분 소요)

#### GitHub
1. GitHub → Settings → Developer settings → OAuth Apps → 앱 선택
2. Authorization callback URL 확인:
   ```
   http://localhost:8000/accounts/github/login/callback/
   ```
3. Update application 클릭

### 6.2 "Site matching query does not exist" 오류

**원인**: SITE_ID 설정이 잘못되었거나 Site 객체가 없음

**해결방법**:
```bash
python manage.py shell
```
```python
from django.contrib.sites.models import Site
site = Site.objects.get(pk=1)
site.domain = 'localhost:8000'
site.name = 'TeamMoa Local'
site.save()
```

### 6.3 "Social application not found" 오류

**원인**: `.env` 파일의 OAuth 키가 누락되었거나 잘못됨

**해결방법**:
1. `.env` 파일에 다음 값들이 올바르게 설정되었는지 확인:
   ```env
   GOOGLE_OAUTH_CLIENT_ID=...
   GOOGLE_OAUTH_CLIENT_SECRET=...
   GITHUB_OAUTH_CLIENT_ID=...
   GITHUB_OAUTH_CLIENT_SECRET=...
   ```
2. Django 서버 재시작
3. (선택사항) Admin에서 Social Application 추가 ([4.3 참고](#43-social-applications-설정-선택사항))

### 6.4 테스트 사용자 제한 (Google)

**현상**: "This app is blocked" 또는 접근 제한 메시지

**원인**: OAuth 동의 화면이 Testing 단계이며, 테스트 사용자로 등록되지 않은 계정으로 로그인 시도

**해결방법**:
1. Google Cloud Console → OAuth consent screen → Test users
2. 로그인할 Google 계정 이메일 추가
3. 또는 OAuth 동의 화면을 "In production"으로 변경 (앱 검토 필요)

---

## 6. 운영 환경 배포 시 추가 설정

### 6.1 Authorized redirect URIs 추가

```
https://yourdomain.com/accounts/google/login/callback/
```

### 6.2 Site 도메인 변경

Admin → Sites → Site ID 1:
- Domain name: `yourdomain.com`
- Display name: `TeamMoa`

### 6.3 OAuth 앱 검증 (선택사항)

- 공개 배포 시 Google의 OAuth 앱 검증 프로세스 진행
- https://support.google.com/cloud/answer/9110914

---

## 7. 추가 기능

### 7.1 사용자 프로필 동기화

Google에서 제공하는 프로필 정보를 자동으로 동기화하려면 `accounts/models.py`에 커스텀 어댑터 추가 가능:

```python
# accounts/adapters.py
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter

class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    def save_user(self, request, sociallogin, form=None):
        user = super().save_user(request, sociallogin, form)
        # Google 프로필 정보 가져오기
        extra_data = sociallogin.account.extra_data
        user.nickname = extra_data.get('given_name', user.username)
        user.save()
        return user
```

`settings/base.py`에 추가:
```python
SOCIALACCOUNT_ADAPTER = 'accounts.adapters.CustomSocialAccountAdapter'
```

---

---

## 부록: 주요 기능

### 이메일 기반 자동 계정 연결
- 동일한 이메일을 가진 TeamMoa 계정이 있으면 자동으로 소셜 계정 연결
- 예: `user@example.com`으로 TeamMoa 회원가입 후, 같은 이메일의 Google로 로그인 시 자동 연결

### 다중 소셜 계정 연결
- 한 사용자가 여러 소셜 계정 연결 가능 (Google + GitHub 동시 연결)
- `/accounts/social-connections/`에서 관리

### 프로필 자동 생성
- OAuth 프로필 정보로 `username`, `nickname` 자동 생성
- 중복 방지를 위한 고유 username 생성 알고리즘 적용

---

*최종 업데이트: 2025.10.16*
