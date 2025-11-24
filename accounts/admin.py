from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """User 모델 Admin 설정"""

    # 목록 페이지에서 보여줄 필드
    list_display = ('username', 'email', 'nickname', 'is_active', 'is_deleted', 'is_staff', 'date_joined', 'deleted_at')

    # 필터 옵션
    list_filter = ('is_active', 'is_deleted', 'is_staff', 'is_superuser', 'date_joined')

    # 검색 필드
    search_fields = ('username', 'email', 'nickname')

    # 정렬 기준
    ordering = ('-date_joined',)

    # 상세 페이지 필드 그룹
    fieldsets = BaseUserAdmin.fieldsets + (
        ('추가 정보', {'fields': ('nickname', 'profile', 'is_deleted', 'deleted_at')}),
    )

    # 읽기 전용 필드
    readonly_fields = ('date_joined', 'last_login', 'deleted_at')
