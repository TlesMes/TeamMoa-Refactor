import os
from pathlib import Path
import environ
# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent



env = environ.Env()
environ.Env.read_env(os.path.join(BASE_DIR, '.env'))


X_FRAME_OPTIONS='SAMEORIGIN'

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env('SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env.bool('DEBUG', default=False)

ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=[])


# Application definition

INSTALLED_APPS = [
    'widget_tweaks',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',  # allauth 필수
    'channels',  # WebSocket 지원

    # Django REST Framework
    'rest_framework',
    'corsheaders',
    'drf_spectacular',

    # Django Allauth
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
    'allauth.socialaccount.providers.github',

    'accounts.apps.AccountsConfig',
    'teams.apps.TeamsConfig',
    'shares.apps.SharesConfig',
    'django.contrib.humanize',
    'django_summernote',
    'schedules.apps.SchedulesConfig',
    'members.apps.MembersConfig',
    'mindmaps.apps.MindmapsConfig',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # Static 파일 서빙용
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'allauth.account.middleware.AccountMiddleware',  # allauth 필수
]

AUTH_USER_MODEL = 'accounts.User'

# Django Sites Framework (allauth 필수)
SITE_ID = 1

# Django Allauth 설정
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',  # 기본 Django 인증
    'allauth.account.auth_backends.AuthenticationBackend',  # Allauth 인증
]

# Allauth 계정 설정 (최신 버전)
ACCOUNT_LOGIN_METHODS = {'username', 'email'}  # username 또는 email로 로그인
ACCOUNT_SIGNUP_FIELDS = ['email*', 'username*', 'password1*', 'password2*']  # 회원가입 필수 필드
ACCOUNT_EMAIL_VERIFICATION = 'optional'  # 소셜 로그인은 이메일 인증 선택적

# 소셜 로그인 후 리다이렉트
LOGIN_REDIRECT_URL = '/teams/'
ACCOUNT_LOGOUT_REDIRECT_URL = '/accounts/login/'

# 소셜 계정 자동 연결 (이메일 기반)
SOCIALACCOUNT_AUTO_SIGNUP = True
SOCIALACCOUNT_EMAIL_REQUIRED = True

# 소셜 로그인 시 확인 페이지 건너뛰기 (바로 Google로 리다이렉트)
SOCIALACCOUNT_LOGIN_ON_GET = True

# 소셜 계정 연결 시 User.email 업데이트 방지 (기존 이메일 유지)
SOCIALACCOUNT_EMAIL_AUTHENTICATION = False
SOCIALACCOUNT_EMAIL_AUTHENTICATION_AUTO_CONNECT = False

# Custom Adapters
ACCOUNT_ADAPTER = 'accounts.adapters.CustomAccountAdapter'
SOCIALACCOUNT_ADAPTER = 'accounts.adapters.CustomSocialAccountAdapter'

# OAuth 설정 (Google + GitHub)
SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'SCOPE': [
            'profile',
            'email',
        ],
        'AUTH_PARAMS': {
            'access_type': 'online',
        },
        'APP': {
            'client_id': env('GOOGLE_OAUTH_CLIENT_ID', default=''),
            'secret': env('GOOGLE_OAUTH_CLIENT_SECRET', default=''),
            'key': ''
        }
    },
    'github': {
        'SCOPE': [
            'user',
            'read:user',
            'user:email',
        ],
        'APP': {
            'client_id': env('GITHUB_OAUTH_CLIENT_ID', default=''),
            'secret': env('GITHUB_OAUTH_CLIENT_SECRET', default=''),
            'key': ''
        }
    }
}

# email
# 메일을 보내는 호스트 서버
EMAIL_HOST = env('EMAIL_HOST')

# ENAIL_HOST에 정의된 SMTP 서버가 사용하는 포트 (587: TLS/STARTTLS용 포트)
EMAIL_PORT = env('EMAIL_PORT')

#  발신할 이메일 주소 '~@gmail.com'
EMAIL_HOST_USER = env('EMAIL_HOST_USER')

# 발신할 이메일 비밀번호 (2단계 인증일경우 앱 비밀번호)
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD')

# TLS 보안 방법 (SMPT 서버와 통신할 떄 TLS (secure) connection 을 사용할지 말지 여부)
EMAIL_USE_TLS = True

# 사이트와 관련한 자동응답을 받을 이메일 주소
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER

ROOT_URLCONF = 'TeamMoa.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.1/howto/static-files/

STATIC_URL = '/static/'
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static')
]

# Static files collection for production
# STATIC_ROOT is where collectstatic will collect files
# Overridden in prod.py for production deployment
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

WSGI_APPLICATION = 'TeamMoa.wsgi.application'

# Django Channels 설정
ASGI_APPLICATION = 'TeamMoa.asgi.application'

# Channel layers - Redis 백엔드 사용
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels.layers.InMemoryChannelLayer',
    },
}

MEDIA_URL= '/media/'
MEDIA_ROOT= os.path.join(BASE_DIR,'media/')
# Database
# https://docs.djangoproject.com/en/4.1/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': env('DB_ENGINE', default='django.db.backends.mysql'),
        'NAME': env('DB_NAME', default='teammoa_db'),
        'USER': env('DB_USER', default='teammoa_user'),
        'PASSWORD': env('DB_PASSWORD', default=''),
        'HOST': env('DB_HOST', default='localhost'),
        'PORT': env('DB_PORT', default='3306'),
        'OPTIONS': {
            'charset': 'utf8mb4',
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
        },
    }
}


# Password validation
# https://docs.djangoproject.com/en/4.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        "OPTIONS": {"min_length": 8},
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# 로그인 세션

SESSION_EXPIRE_AT_BROWSER_CLOSE = True

# Internationalization
# https://docs.djangoproject.com/en/4.1/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Asia/Seoul'

USE_I18N = True

USE_L10N = True

USE_TZ = False


# Default primary key field type
# https://docs.djangoproject.com/en/4.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Django REST Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.BasicAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    ],
    'DEFAULT_PAGINATION_CLASS': 'api.pagination.TeamMoaPageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'EXCEPTION_HANDLER': 'api.exceptions.custom_exception_handler',
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle'
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/hour',
        'user': '1000/hour',
        'registration': '5/hour',
        'availability': '30/min',
    }
}

# API 문서화 설정 (drf-spectacular)
SPECTACULAR_SETTINGS = {
    'TITLE': 'TeamMoa API',
    'DESCRIPTION': 'TeamMoa 팀 프로젝트 관리 시스템 API',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
}

# CORS 설정
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8080",
    "http://127.0.0.1:8080",
]

# 개발 환경에서만 모든 출처 허용 (주의: 운영에서는 사용 금지)
if DEBUG:
    CORS_ALLOW_ALL_ORIGINS = True

# CORS에서 허용할 헤더
CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]

#CI/CD paths-ignore 테스트 - python 파일 변경으로, workflow 실행되어야 함