from django.urls import path
from . import views

app_name = 'members'

urlpatterns = [
    path('team_members_page/<int:pk>/', views.team_members_page, name='team_members_page'),
    path('member_add_Todo/<int:pk>/', views.member_add_Todo, name = 'member_add_Todo'),
    path('member_complete_Todo/<int:pk>/<int:todo_id>', views.member_complete_Todo, name = 'member_complete_Todo'),
    path('member_delete_Todo/<int:pk>/<int:todo_id>', views.member_delete_Todo, name = 'member_delete_Todo'),
]