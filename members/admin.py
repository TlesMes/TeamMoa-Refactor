from django.contrib import admin

from members.models import Todo

# Register your models here.


@admin.register(Todo)
class TodoAdmin(admin.ModelAdmin):
    list_display = ['content', 'team', 'assignee', 'milestone',
                    'is_completed', 'order', 'created_at']
    list_filter = ['is_completed', 'team', 'milestone']
    search_fields = ['content']
    raw_id_fields = ['assignee', 'milestone']
    readonly_fields = ['created_at', 'completed_at']