from django.contrib import admin
# 게시글(Post) Model을 불러옵니다
from .models import Post

# Register your models here.
# 관리자(admin)가 게시글(Post)에 접근 가능
class PostAdmin(admin.ModelAdmin):
    list_display =(
        'title',
        'get_writer',
        'get_team',
        'registered_date',
        'article'
    )
    search_fields = ('title','article','teamuser__user__user_id',)

    def get_writer(self, obj):
        """작성자 표시"""
        return obj.teamuser.user.nickname if obj.teamuser else '탈퇴한 사용자'
    get_writer.short_description = '작성자'

    def get_team(self, obj):
        """팀 표시"""
        return obj.teamuser.team.title if obj.teamuser else '알 수 없음'
    get_team.short_description = '팀'
   # summernote_fields = ('content',)
    #def get_member_
admin.site.register(Post, PostAdmin)