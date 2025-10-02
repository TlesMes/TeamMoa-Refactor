from django.urls import path, include
from rest_framework.routers import DefaultRouter
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

# ViewSet imports
from accounts.viewsets import UserViewSet
from members.viewsets import TodoViewSet, TeamMemberViewSet
from teams.viewsets import MilestoneViewSet

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

    # 팀별 nested 엔드포인트
    path('v1/teams/<int:team_pk>/todos/', TodoViewSet.as_view({
        'get': 'list',
        'post': 'create'
    }), name='team-todos-list'),
    path('v1/teams/<int:team_pk>/todos/<int:pk>/', TodoViewSet.as_view({
        'get': 'retrieve',
        'put': 'update',
        'patch': 'partial_update',
        'delete': 'destroy'
    }), name='team-todos-detail'),

    # TODO 액션 엔드포인트
    path('v1/teams/<int:team_pk>/todos/<int:pk>/move-to-todo/', TodoViewSet.as_view({
        'post': 'move_to_todo'
    }), name='team-todos-move-to-todo'),
    path('v1/teams/<int:team_pk>/todos/<int:pk>/move-to-done/', TodoViewSet.as_view({
        'post': 'move_to_done'
    }), name='team-todos-move-to-done'),
    path('v1/teams/<int:team_pk>/todos/<int:pk>/assign/', TodoViewSet.as_view({
        'post': 'assign'
    }), name='team-todos-assign'),
    path('v1/teams/<int:team_pk>/todos/<int:pk>/complete/', TodoViewSet.as_view({
        'post': 'complete'
    }), name='team-todos-complete'),

    # 팀 멤버 엔드포인트
    path('v1/teams/<int:team_pk>/members/', TeamMemberViewSet.as_view({
        'get': 'list'
    }), name='team-members-list'),

    # 마일스톤 엔드포인트
    path('v1/teams/<int:team_pk>/milestones/', MilestoneViewSet.as_view({
        'get': 'list',
        'post': 'create'
    }), name='team-milestones-list'),
    path('v1/teams/<int:team_pk>/milestones/<int:pk>/', MilestoneViewSet.as_view({
        'get': 'retrieve',
        'put': 'update',
        'patch': 'partial_update',
        'delete': 'destroy'
    }), name='team-milestones-detail'),

    # API 문서화
    path('schema/', SpectacularAPIView.as_view(), name='schema'),
    path('docs/', SpectacularSwaggerView.as_view(url_name='api:schema'), name='swagger-ui'),

    # DRF 기본 인증 뷰 (로그인/로그아웃)
    path('auth/', include('rest_framework.urls')),
]