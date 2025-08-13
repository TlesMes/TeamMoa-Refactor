from django.urls import path
from . import views

app_name = 'teams'

urlpatterns = [
    path('', views.main_page, name='main_page'),
    path('team_list/', views.team_list, name='team_list'),
    path('team_create/', views.team_create, name='team_create'),
    path('team_search/', views.team_search, name='team_search'),
    path('team_join/<int:pk>/', views.team_join, name='team_join'),
    path('team_info_change/<int:pk>/', views.team_info_change, name='team_info_change'),
    path('team_main_page/<int:pk>/', views.team_main_page, name='team_main_page'),
    path('team_add_devPhase/<int:pk>/', views.team_add_devPhase, name='team_add_devPhase'),
    path('team_delete_devPhase/<int:pk>/<int:phase_id>/', views.team_delete_devPhase, name='team_delete_devPhase'),
    path('team_disband/<int:pk>/', views.team_disband, name='team_disband')
]