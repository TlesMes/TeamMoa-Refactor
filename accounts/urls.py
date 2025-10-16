from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('', views.home, name='home'),
    path('home/', views.home, name='home'),
    path('signup/', views.signup, name='signup'),
    path('signup/success/', views.signup_success, name='signup_success'),
    path('login/', views.login, name='login'),
    path('logout/', views.logout, name='logout'),
    path('activate/<str:uid64>/<str:token>',views.activate, name='activate'),
    path('resend-activation/', views.resend_activation_email, name='resend_activation'),
    path('test-signup-success/', views.test_signup_success, name='test_signup_success'),  # 테스트용
    path('update/', views.update, name='update'),
    path('password/', views.password, name='password'),
    path('social-connections/', views.social_connections, name='social_connections'),
]