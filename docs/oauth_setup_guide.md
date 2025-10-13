# Google OAuth 2.0 설정 가이드

## 📋 목차
1. [Google Cloud Console 설정](#1-google-cloud-console-설정)
2. [Django 프로젝트 설정](#2-django-프로젝트-설정)
3. [어드민 페이지 설정](#3-어드민-페이지-설정)
4. [테스트 방법](#4-테스트-방법)
5. [문제 해결](#5-문제-해결)

---

## 1. Google Cloud Console 설정

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

## 2. Django 프로젝트 설정

### 2.1 환경변수 설정

`.env` 파일에 Google OAuth 정보 추가:

```env
# Google OAuth 2.0
GOOGLE_OAUTH_CLIENT_ID=your-client-id-here.apps.googleusercontent.com
GOOGLE_OAUTH_CLIENT_SECRET=your-client-secret-here
```

### 2.2 패키지 설치 (이미 완료)

```bash
pip install django-allauth
```

### 2.3 설정 확인

`TeamMoa/settings/base.py`에 다음 설정이 추가되었는지 확인:

```python
INSTALLED_APPS = [
    # ...
    'django.contrib.sites',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
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

## 3. 어드민 페이지 설정

### 3.1 마이그레이션 실행

```bash
python manage.py migrate
```

### 3.2 Django Admin에서 Social Application 추가

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

3. **Social applications 추가**
   ```
   Social applications → Add social application
   ```

   - **Provider**: Google
   - **Name**: Google OAuth
   - **Client id**: Google Cloud Console에서 생성한 Client ID
   - **Secret key**: Google Cloud Console에서 생성한 Client Secret
   - **Sites**: `localhost:8000` (또는 설정한 사이트) 선택하여 Chosen sites로 이동
   - **Save** 클릭

---

## 4. 테스트 방법

### 4.1 로그인 페이지 접속

```
http://localhost:8000/accounts/login/
```

### 4.2 Google로 로그인 버튼 클릭

- "Google로 로그인" 버튼 클릭
- Google 계정 선택
- TeamMoa 앱에 대한 권한 허용
- 자동으로 로그인 및 `/teams/` 페이지로 리다이렉트

### 4.3 확인 사항

1. **사용자 생성 확인**
   - Admin 페이지 → Users에서 Google 계정으로 생성된 사용자 확인
   - username은 Google 이메일 주소 기반으로 자동 생성

2. **소셜 계정 연결 확인**
   - Admin 페이지 → Social accounts에서 연결된 Google 계정 확인

---

## 5. 문제 해결

### 5.1 "redirect_uri_mismatch" 오류

**원인**: Google Cloud Console에 등록된 Redirect URI와 실제 요청 URI가 다름

**해결방법**:
1. Google Cloud Console → Credentials → OAuth 2.0 Client IDs 클릭
2. Authorized redirect URIs에 다음 추가:
   ```
   http://localhost:8000/accounts/google/login/callback/
   http://127.0.0.1:8000/accounts/google/login/callback/
   ```
3. 변경사항 저장 (최대 5분 소요)

### 5.2 "Site matching query does not exist" 오류

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

### 5.3 "Social application not found" 오류

**원인**: Admin에서 Social application 설정이 누락됨

**해결방법**:
- [3.2 Django Admin에서 Social Application 추가](#32-django-admin에서-social-application-추가) 단계 재확인
- Client ID와 Secret Key가 정확히 입력되었는지 확인
- Sites가 올바르게 선택되었는지 확인

### 5.4 테스트 사용자 제한

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

*최종 업데이트: 2025.10.12*
