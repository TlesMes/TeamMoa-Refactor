from django.urls import path
from . import views
from . import templates
app_name = 'shares'
urlpatterns =[
    path('', views.PostListView.as_view(), name='post_list'),
    path('<int:pk>/',views.post_detail_view, name='post_detail1'),
    path('write/',views.post_write_view,name='post_write'),
    path('<int:pk>/edit/' ,views.post_edit_view,name='post_edit'),
    path('<int:pk>/delete/', views.post_delete_view, name='post_delete'),
    path('<int:pk>/download/', views.post_download_view, name="post_download", )

]