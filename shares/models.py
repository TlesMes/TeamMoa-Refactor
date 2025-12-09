from django.db import models
from datetime import datetime
from uuid import uuid4
import os
from django.conf import settings


import teams.models
def get_file_path(instance , filename ) :
    ymd_path =datetime.now().strftime('%Y/%m/%d')
    uuid_name = uuid4().hex
    return '/'.join(['upload_file/', ymd_path, uuid_name])


class Post(models.Model):
    title = models.CharField(max_length=64, verbose_name='제목')

    # 필수: 게시물이 속한 팀
    team = models.ForeignKey(
        'teams.Team',
        on_delete=models.CASCADE,
        verbose_name='팀',
        help_text='게시물이 속한 팀 (필수)'
    )

    # 선택적: 작성자 정보 (탈퇴 시 NULL)
    teamuser = models.ForeignKey(
        'teams.TeamUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='작성자',
        help_text='작성자 정보 (탈퇴 시 NULL)'
    )

    article = models.TextField(verbose_name='내용')
    registered_date = models.DateTimeField(auto_now_add=True, verbose_name='등록시간')
    upload_files = models.FileField(upload_to=get_file_path, null=True, blank=True, verbose_name='파일')
    filename = models.CharField(max_length=64, null=True, verbose_name='첨부파일명')

    def __str__(self):
        return self.title

    def delete(self, *args, **kargs):
        if self.upload_files:
            os.remove(os.path.join(settings.MEDIA_ROOT, self.upload_files.path))
        super(Post, self).delete(*args,**kargs)
    class Meta:
        db_table = '게시물'
        verbose_name = '게시물'
        verbose_name_plural = '게시물'
