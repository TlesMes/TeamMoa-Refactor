from django.urls import path
from . import views



urlpatterns = [
    path('team_list/', views.team_list, name='team_list'),
    path('team_create/', views.team_create, name='team_create'),
    path('team_search/', views.team_search, name='team_search'),
    path('team_join/<int:pk>/', views.team_join, name='team_join'),
    path('team_main_page/<int:pk>/', views.team_main_page, name='team_main_page'),
]