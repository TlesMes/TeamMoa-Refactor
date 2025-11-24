
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

    # 탈퇴 관련 필드
    is_deleted = models.BooleanField(
        default=False,
        db_index=True,
        help_text="회원 탈퇴 여부"
    )
    deleted_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="회원 탈퇴 시점"
    )
    
    REQUIRED_FIELDS = ['email', 'nickname']

    def __str__(self): #어드민 페이지에서 username으로 표시
        return self.username

    @classmethod
    def get_display_name_in_team(cls, user_or_none, team):
        """
        팀 컨텍스트에서 사용자 이름을 안전하게 반환 (None-safe)

        Args:
            user_or_none: User 인스턴스 또는 None (hard delete된 경우)
            team: Team 인스턴스

        Returns:
            str: 표시할 이름

        처리 케이스:
        1. user=None (hard delete, SET_NULL 결과) → "탈퇴한 사용자"
        2. user.is_active=False (계정 비활성화) → "탈퇴한 사용자"
        3. TeamUser 없음 (팀 탈퇴) → "탈퇴한 사용자"
        4. 정상 → user.nickname
        """
        from teams.models import TeamUser

        # 1. None 체크 (hard delete 또는 SET_NULL)
        if user_or_none is None:
            return "탈퇴한 사용자"

        # 2. 계정 비활성화 체크
        if not user_or_none.is_active:
            return "탈퇴한 사용자"

        # 3. 팀 탈퇴 체크
        if not TeamUser.objects.filter(team=team, user=user_or_none).exists():
            return "탈퇴한 사용자"

        return user_or_none.nickname