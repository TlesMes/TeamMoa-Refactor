from django.db import models

# Create your models here.

class Todo(models.Model):
    owner = models.ForeignKey('teams.Team_User',on_delete = models.CASCADE) #어떤 유저의 todo인지
    
    content = models.TextField(default="",null=True, blank=True)
    is_completed = models.BooleanField(default=False)
    
    