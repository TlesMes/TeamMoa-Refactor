"""
ASGI config for TeamMoa project.

WebSocket과 HTTP 요청을 처리하기 위한 ASGI 애플리케이션.
"""

import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from channels.security.websocket import AllowedHostsOriginValidator

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'TeamMoa.settings.dev')

# Django ASGI 애플리케이션을 먼저 초기화
django_asgi_app = get_asgi_application()

# mindmaps routing을 import
try:
    from mindmaps.routing import websocket_urlpatterns
except ImportError:
    websocket_urlpatterns = []

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AllowedHostsOriginValidator(
        AuthMiddlewareStack(
            URLRouter(
                websocket_urlpatterns
            )
        )
    ),
})
