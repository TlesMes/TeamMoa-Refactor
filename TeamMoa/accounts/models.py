
from django.contrib.auth.models import AbstractUser
from django.db import models

# Create your models here.


class User(AbstractUser):
    nickname = models.CharField(max_length=10)
    # account_number = models.CharField(max_length=32)
    profile = models.TextField(default="",null=True, blank=True)
    
    def __str__(self): #어드민 페이지에서 username으로 표시
        return self.username