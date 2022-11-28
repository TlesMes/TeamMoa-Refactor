from django.db import models

import accounts.models


class Post(models.Model):
    title = models.CharField(max_length=64, verbose_name='제목')
    writer = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null = True, verbose_name='작성자')
    article = models.CharField(max_length=600 , verbose_name='내용')
    hits = models.PositiveIntegerField(verbose_name ='조회수', default =0)
    registered_date = models.DateTimeField(auto_now_add=True, verbose_name='등록시간')

    def __str__(self):
        return self.title
# Create your models here.
