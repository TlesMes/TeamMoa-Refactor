from django.conf import settings
from django.conf.urls.static import static
from django.urls import path
from . import views
from django.contrib import messages
from django.shortcuts import redirect
def protected_file(request, path, document_root=None):
    messages.error(request, "접근 불가")
    return redirect('/')

app_name = 'shares'
urlpatterns =[

    path('<int:pk>', views.PostListView.as_view(), name='post_list'),   #게시판 리스트
    path('detail/<int:pk>/',views.post_detail_view, name='post_detail1'),  #게시물 상세
    path('write/',views.post_write_view,name='post_write'),   #게시물 작성
    path('<int:pk>/edit/' ,views.post_edit_view,name='post_edit'),  #게시물 수정
    path('<int:pk>/delete/', views.post_delete_view, name='post_delete'),# 게시물 삭제
    path('download/<int:pk>',views.post_download_view,name="post_download",) #첨부파일 다운로드
]
urlpatterns += static(settings.MEDIA_URL, protected_file, document_root=settings.MEDIA_ROOT)


