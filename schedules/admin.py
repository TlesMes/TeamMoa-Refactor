from django.contrib import admin

from schedules.models import PersonalDaySchedule

# Register your models here.
class PersonalDayScheduleAdmin(admin.ModelAdmin):
    list_display = ['id', 'date', 'owner', 'available_hours']
    list_filter = ['date', 'owner__team']
    search_fields = ['owner__user__nickname']

admin.site.register(PersonalDaySchedule, PersonalDayScheduleAdmin)