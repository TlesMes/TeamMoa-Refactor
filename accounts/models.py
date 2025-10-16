
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.validators import ASCIIUsernameValidator
from django.db import models
from django.core.validators import MinLengthValidator, MaxLengthValidator

# Create your models here.


class User(AbstractUser):
    username = models.CharField(
        max_length=150,
        unique=True,
        validators=[
            ASCIIUsernameValidator(),  # 영문, 숫자, ., _, - 만 허용
            MinLengthValidator(3)      # 최소 3자
        ]
    )
    email = models.EmailField(
        unique=True,  # DB 레벨 이메일 중복 방지
        error_messages={
            'unique': '이미 사용 중인 이메일입니다.',
        }
    )
    nickname = models.CharField(
        max_length=10,
        validators=[MinLengthValidator(2)]
    )
    profile = models.TextField(
        max_length=500,
        default="",
        null=True,
        blank=True
    )

    REQUIRED_FIELDS = ['email', 'nickname'] 

    def __str__(self): #어드민 페이지에서 username으로 표시
        return self.username