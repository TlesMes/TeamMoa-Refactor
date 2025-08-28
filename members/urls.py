from django.urls import path
from . import views

app_name = 'members'

urlpatterns = [
    path('team_members_page/<int:pk>/', views.team_members_page, name='team_members_page'),
    path('member_complete_Todo/<int:pk>/<int:todo_id>', views.member_complete_Todo, name = 'member_complete_Todo'),
    path('member_delete_Todo/<int:pk>/<int:todo_id>', views.member_delete_Todo, name = 'member_delete_Todo'),
    
    
    # Ajax API
    path('api/<int:pk>/move-todo/', views.move_todo, name='move_todo'),
    path('api/<int:pk>/assign-todo/', views.assign_todo, name='assign_todo'),
    path('api/<int:pk>/complete-todo/', views.complete_todo, name='complete_todo'),
    path('api/<int:pk>/return-to-board/', views.return_to_board, name='return_to_board'),
]