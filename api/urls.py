from django.urls import path, include
from rest_framework.routers import DefaultRouter
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

# ViewSet imports
from accounts.viewsets import UserViewSet

# API 라우터 설정
router = DefaultRouter()

# ViewSet 등록
router.register(r'users', UserViewSet, basename='user')

# 향후 추가될 ViewSet들
# router.register(r'teams', TeamViewSet)

app_name = 'api'

urlpatterns = [
    # API v1 엔드포인트
    path('v1/', include(router.urls)),

    # API 문서화
    path('schema/', SpectacularAPIView.as_view(), name='schema'),
    path('docs/', SpectacularSwaggerView.as_view(url_name='api:schema'), name='swagger-ui'),

    # DRF 기본 인증 뷰 (로그인/로그아웃)
    path('auth/', include('rest_framework.urls')),
]