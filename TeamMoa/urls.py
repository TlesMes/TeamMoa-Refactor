"""TeamMoa URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.views.generic.base import RedirectView
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_GET
from django.conf import settings
from django.conf.urls.static import static
import os


@require_GET
def health_check(request):
    """Health check endpoint for Docker and monitoring"""
    return JsonResponse({
        'status': 'healthy',
        'service': 'TeamMoa',
    })


@require_GET
def favicon(request):
    """Serve favicon.ico from static files"""
    favicon_path = os.path.join(settings.BASE_DIR, 'static', 'assets', 'img', 'LogoB.svg')
    try:
        with open(favicon_path, 'rb') as f:
            return HttpResponse(f.read(), content_type='image/svg+xml')
    except FileNotFoundError:
        return HttpResponse(status=404)


urlpatterns = [
    path('health/', health_check, name='health_check'),
    path('favicon.ico', favicon, name='favicon'),
    path('admin/', admin.site.urls),
    path('', RedirectView.as_view(url='/teams/', permanent=False)),

    # API 엔드포인트
    path('api/', include('api.urls')),

    # 기존 템플릿 기반 뷰들 (우선순위: 기존 로그인/회원가입 유지)
    path('accounts/', include('accounts.urls')),

    # Django Allauth (소셜 로그인만 사용, accounts/ 아래 남은 경로들)
    path('accounts/', include('allauth.urls')),

    path('teams/', include('teams.urls')),
    path('shares/',include('shares.urls')),
    path('schedules/', include('schedules.urls')),
    path('members/', include('members.urls')),
    path('mindmaps/', include('mindmaps.urls')),

]
