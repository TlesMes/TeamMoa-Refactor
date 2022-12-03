from django.contrib import admin
from .models import Team, Team_User
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


admin.site.register(Team,TeamAdmin)

