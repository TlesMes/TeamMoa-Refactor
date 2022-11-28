from django.urls import path
from . import views
from . import templates
app_name = 'shares'
urlpatterns =[
    path('', views.PostListView.as_view(), name='post_list'),

]