from django.urls import path
from . import views

app_name = 'schedules'

urlpatterns = [
    path('scheduler_page/<int:pk>/', views.scheduler_page, name='scheduler_page'),
    path('upload_scheduler/<int:pk>/',views.upload_scheduler, name='upload_scheduler' )
]