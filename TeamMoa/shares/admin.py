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
        'article'
    )
    search_fields = ('title','article','writer__user_id',)
   # summernote_fields = ('content',)
    #def get_member_
admin.site.register(Post, PostAdmin)