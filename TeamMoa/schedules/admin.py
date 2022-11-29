from django.contrib import admin

from schedules.models import PersonalDaySchedule, TeamDaySchedule

# Register your models here.
class PDscheduleAdmin(admin.ModelAdmin):
    list_display = ['id', 'date', 'owner']

class TDscheduleAdmin(admin.ModelAdmin):
    list_display = ['id', 'date', 'team']

admin.site.register(PersonalDaySchedule, PDscheduleAdmin)
admin.site.register(TeamDaySchedule, TDscheduleAdmin)