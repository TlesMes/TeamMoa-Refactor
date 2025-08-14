from django.db import models

# Create your models here.

class Todo(models.Model):
    owner = models.ForeignKey('teams.TeamUser', on_delete=models.CASCADE)  # 어떤 유저의 todo인지

    content = models.TextField(default="", null=True, blank=True)
    is_completed = models.BooleanField(default=False)
    
    def __str__(self): #어드민 페이지에서 username으로 표시
        return self.content