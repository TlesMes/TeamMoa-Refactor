from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('', views.home, name='home'),
    path('home/', views.home, name='home'),
    path('signup/', views.signup, name='signup'),
    path('login/', views.login, name='login'),
    path('logout/', views.logout, name='logout'),
    path('activate/<str:uid64>/<str:token>',views.activate, name='activate'),
    path('update/', views.update, name='update'),
    path('password/', views.password, name='password'),
]