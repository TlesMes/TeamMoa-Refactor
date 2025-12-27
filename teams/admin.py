from django.contrib import admin
from .models import Milestone, Team, TeamUser
# Register your models here.

class TeamAdmin(admin.ModelAdmin):
    list_display =(
        'title',
        'maxuser',
        'currentuser',
        'get_members_mem_id',
        'host',
        'invitecode',
        'teampasswd'
    )

    def get_members_mem_id(self, obj):
        return ', '.join([m.nickname for m in obj.members.all()])

    get_members_mem_id.short_description = 'member Nickname'


@admin.register(Milestone)
class MilestoneAdmin(admin.ModelAdmin):
    list_display = ['title', 'team', 'progress_percentage', 'progress_mode',
                    'priority', 'is_completed', 'startdate', 'enddate']
    list_filter = ['progress_mode', 'priority', 'is_completed', 'team']
    search_fields = ['title', 'description']
    fieldsets = (
        ('기본 정보', {
            'fields': ('team', 'title', 'description')
        }),
        ('일정', {
            'fields': ('startdate', 'enddate')
        }),
        ('진행 상태', {
            'fields': ('progress_mode', 'progress_percentage', 'is_completed', 'completed_date')
        }),
        ('우선순위', {
            'fields': ('priority',)
        }),
    )


admin.site.register(Team,TeamAdmin)
admin.site.register(TeamUser)
