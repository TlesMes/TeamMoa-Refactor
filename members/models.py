from django.db import models

# Create your models here.

class Todo(models.Model):
    STATUS_CHOICES = [
        ('todo', 'To Do'),
        ('in_progress', 'In Progress'),
        ('done', 'Done')
    ]
    
    content = models.TextField(default="", null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='todo')
    assignee = models.ForeignKey('teams.TeamUser', on_delete=models.CASCADE, null=True, blank=True)
    team = models.ForeignKey('teams.Team', on_delete=models.CASCADE, default=1)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['order', 'created_at']
    
    def __str__(self):
        return self.content