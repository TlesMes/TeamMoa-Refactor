from django.urls import path
from . import views

app_name = 'teams'

urlpatterns = [
    path('', views.main_page, name='main_page'),
    path('team_create/', views.team_create, name='team_create'),
    path('team_search/', views.team_search, name='team_search'),
    # AJAX 엔드포인트
    path('ajax/team-verify/', views.team_verify_code, name='team_verify_code'),
    path('ajax/team-join/', views.team_join_process, name='team_join_process'),
    # 기존 team_join/<int:pk>/ URL 제거됨 - 보안상 이유로
    path('team_info_change/<int:pk>/', views.team_info_change, name='team_info_change'),
    path('team_main_page/<int:pk>/', views.team_main_page, name='team_main_page'),
    path('team_add_milestone/<int:pk>/', views.team_add_milestone, name='team_add_milestone'),
    path('team_milestone_timeline/<int:pk>/', views.team_milestone_timeline, name='team_milestone_timeline'),
    path('team/<int:pk>/milestone/<int:milestone_id>/update/', views.milestone_update_ajax, name='milestone_update_ajax'),
    path('team/<int:pk>/milestone/<int:milestone_id>/delete/', views.milestone_delete_ajax, name='milestone_delete_ajax'),
    path('team_disband/<int:pk>/', views.team_disband, name='team_disband')
]