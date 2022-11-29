from django.urls import path
from . import views
app_name = 'members'

urlpatterns = [
    path('members_page/<int:pk>/', views.member_profile_page, name='member_profile_page'),
    path('member_add_Todo/<int:pk>/', views.member_add_Todo, name = 'member_add_Todo'),
]