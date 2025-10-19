from django.urls import path
from . import views

app_name = 'members'

urlpatterns = [
    path('team_members_page/<int:pk>/', views.team_members_page, name='team_members_page'),
]