from django.urls import path
from . import views

app_name = 'schedules'

urlpatterns = [
    path('scheduler_page/<int:pk>/', views.scheduler_page, name='scheduler_page'),
    path('scheduler_upload_page/<int:pk>/',views.scheduler_upload_page, name='scheduler_upload_page'),
]