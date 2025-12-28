from django.urls import path, include
from rest_framework.routers import DefaultRouter
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

# ViewSet imports
from accounts.viewsets import UserViewSet
from members.viewsets import TodoViewSet, TeamMemberViewSet
from teams.viewsets import TeamViewSet, MilestoneViewSet
from schedules.viewsets import ScheduleViewSet
from mindmaps.viewsets import MindmapViewSet, NodeViewSet, NodeConnectionViewSet

# API 라우터 설정
router = DefaultRouter()

# ViewSet 등록
router.register(r'users', UserViewSet, basename='user')
router.register(r'teams', TeamViewSet, basename='team')

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
    path('v1/teams/<int:team_pk>/todos/<int:pk>/milestone/', TodoViewSet.as_view({
        'post': 'assign_milestone',
        'delete': 'detach_milestone'
    }), name='team-todos-milestone'),

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
    path('v1/teams/<int:team_pk>/milestones/<int:pk>/progress-mode/', MilestoneViewSet.as_view({
        'patch': 'toggle_progress_mode'
    }), name='team-milestones-progress-mode'),
    path('v1/teams/<int:team_pk>/milestones/<int:pk>/with-stats/', MilestoneViewSet.as_view({
        'get': 'milestone_with_stats'
    }), name='team-milestones-with-stats'),

    # 스케줄 엔드포인트
    path('v1/teams/<int:team_pk>/schedules/', ScheduleViewSet.as_view({
        'get': 'list'
    }), name='team-schedules-list'),
    path('v1/teams/<int:team_pk>/schedules/save-personal/', ScheduleViewSet.as_view({
        'post': 'save_personal_schedule'
    }), name='team-schedules-save-personal'),
    path('v1/teams/<int:team_pk>/schedules/team-availability/', ScheduleViewSet.as_view({
        'get': 'get_team_availability'
    }), name='team-schedules-availability'),
    path('v1/teams/<int:team_pk>/schedules/my-schedule/', ScheduleViewSet.as_view({
        'get': 'get_my_schedule'
    }), name='team-schedules-my-schedule'),

    # 마인드맵 엔드포인트
    path('v1/teams/<int:team_pk>/mindmaps/', MindmapViewSet.as_view({
        'get': 'list',
        'post': 'create'
    }), name='team-mindmaps-list'),
    path('v1/teams/<int:team_pk>/mindmaps/<int:pk>/', MindmapViewSet.as_view({
        'get': 'retrieve',
        'delete': 'destroy'
    }), name='team-mindmaps-detail'),

    # 노드 엔드포인트
    path('v1/teams/<int:team_pk>/mindmaps/<int:mindmap_pk>/nodes/', NodeViewSet.as_view({
        'get': 'list',
        'post': 'create'
    }), name='mindmap-nodes-list'),
    path('v1/teams/<int:team_pk>/mindmaps/<int:mindmap_pk>/nodes/<int:pk>/', NodeViewSet.as_view({
        'get': 'retrieve',
        'patch': 'partial_update',
        'delete': 'destroy'
    }), name='mindmap-nodes-detail'),
    path('v1/teams/<int:team_pk>/mindmaps/<int:mindmap_pk>/nodes/<int:pk>/recommend/', NodeViewSet.as_view({
        'post': 'recommend'
    }), name='mindmap-nodes-recommend'),
    path('v1/teams/<int:team_pk>/mindmaps/<int:mindmap_pk>/nodes/<int:pk>/comments/', NodeViewSet.as_view({
        'get': 'comments',
        'post': 'comments'
    }), name='mindmap-nodes-comments'),

    # 노드 연결선 엔드포인트
    path('v1/teams/<int:team_pk>/mindmaps/<int:mindmap_pk>/connections/', NodeConnectionViewSet.as_view({
        'get': 'list',
        'post': 'create'
    }), name='mindmap-connections-list'),
    path('v1/teams/<int:team_pk>/mindmaps/<int:mindmap_pk>/connections/<int:pk>/', NodeConnectionViewSet.as_view({
        'delete': 'destroy'
    }), name='mindmap-connections-detail'),

    # API 문서화
    path('schema/', SpectacularAPIView.as_view(), name='schema'),
    path('docs/', SpectacularSwaggerView.as_view(url_name='api:schema'), name='swagger-ui'),

    # DRF 기본 인증 뷰 (로그인/로그아웃)
    path('auth/', include('rest_framework.urls')),
]