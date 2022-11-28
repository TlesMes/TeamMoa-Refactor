from django.contrib import admin
# 게시글(Post) Model을 불러옵니다
from .models import Post

# Register your models here.
# 관리자(admin)가 게시글(Post)에 접근 가능
class PostAdmin(admin.ModelAdmin):
    list_display =(
        'title',
        'writer',
        'hits',
        'registered_date',
    )
    search_fields = ('title','content','writer__user_id',)
admin.site.register(Post, PostAdmin)