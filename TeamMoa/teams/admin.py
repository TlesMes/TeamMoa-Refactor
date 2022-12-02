from django.contrib import admin
from .models import DevPhase, Team, Team_User
# Register your models here.


admin.site.register(Team)
admin.site.register(Team_User)
admin.site.register(DevPhase)