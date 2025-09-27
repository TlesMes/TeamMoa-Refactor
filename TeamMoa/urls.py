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


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', RedirectView.as_view(url='/teams/', permanent=False)),

    # API 엔드포인트
    path('api/', include('api.urls')),

    # 기존 템플릿 기반 뷰들
    path('accounts/', include('accounts.urls')),
    path('teams/', include('teams.urls')),
    path('shares/',include('shares.urls')),
    path('schedules/', include('schedules.urls')),
    path('members/', include('members.urls')),
    path('mindmaps/', include('mindmaps.urls')),

]
