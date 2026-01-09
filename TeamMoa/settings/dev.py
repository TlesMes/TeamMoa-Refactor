from .base import *  # Import only the needed names from base.py
import socket

ALLOWED_HOSTS = ['*']
DEBUG = True

# Django Debug Toolbar (개발 환경 전용)
INSTALLED_APPS += ['debug_toolbar']
MIDDLEWARE = ['debug_toolbar.middleware.DebugToolbarMiddleware'] + MIDDLEWARE

# Debug Toolbar를 위한 Internal IPs 설정 (Docker 환경 지원)
INTERNAL_IPS = [
    '127.0.0.1',
    'localhost',
]

# Docker 환경에서 호스트 IP 자동 감지
hostname, _, ips = socket.gethostbyname_ex(socket.gethostname())
INTERNAL_IPS += [ip[: ip.rfind(".")] + ".1" for ip in ips]
