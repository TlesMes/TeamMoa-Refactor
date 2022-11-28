from django.contrib import admin

from schedules.models import PersonalDaySchedule, TeamDaySchedule

# Register your models here.

admin.site.register(PersonalDaySchedule)
admin.site.register(TeamDaySchedule)