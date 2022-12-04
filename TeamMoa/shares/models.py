from django.db import models
from uuid import uuid4
from datetime import datetime
import accounts.models

def get_file_path(instance, filename):
    ymd_path = datetime.now().strftime('%Y/%m/%d')
    uuid_name = uuid4().hex
    return '/'.join(['upload_file/', ymd_path, uuid_name])
class Post(models.Model):
    title = models.CharField(max_length=64, verbose_name='제목')
    writer = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null = True, verbose_name='작성자')
    article = models.CharField(max_length=600 , verbose_name='내용')
    hits = models.PositiveIntegerField(verbose_name ='조회수', default =0)
    registered_date = models.DateTimeField(auto_now_add=True, verbose_name='등록시간')
    upload_files = models.FileField(upload_to=get_file_path, null=True, blank=True, verbose_name='파일')
    filename = models.CharField(max_length=64, null=True, verbose_name='첨부파일명')
    def __str__(self):
        return self.title
# Create your models here.





