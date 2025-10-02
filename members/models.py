from django.db import models

# Create your models here.

class Todo(models.Model):
    content = models.TextField(default="", null=True, blank=True)
    is_completed = models.BooleanField(default=False)
    assignee = models.ForeignKey('teams.TeamUser', on_delete=models.CASCADE, null=True, blank=True, related_name='todo_set')
    team = models.ForeignKey('teams.Team', on_delete=models.CASCADE, default=1)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['order', 'created_at']
    
    def __str__(self):
        return self.content