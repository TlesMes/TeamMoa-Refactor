from datetime import datetime
from django.db import models

# Create your models here.

class Mindmap(models.Model):
    title = models.CharField(max_length=64)
    team = models.ForeignKey('teams.Team',on_delete = models.CASCADE)
    
    def __str__(self):
        return self.title

class Node(models.Model):
    posX = models.PositiveIntegerField()
    posY = models.PositiveIntegerField()
    title = models.CharField(max_length=64) 
    content = models.TextField()
    mindmap = models.ForeignKey('Mindmap',on_delete = models.CASCADE)
    vote = models.PositiveSmallIntegerField(default=0)
    next = models.ManyToManyField('self', symmetrical=True, blank=True, through="NodeConnection")
    user = models.ManyToManyField('accounts.User', related_name='nodes', through="NodeUser")

    def __str__(self):
        return self.content
class NodeUser(models.Model):
    node = models.ForeignKey('Node', on_delete=models.CASCADE)
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE)
    voted = models.BooleanField(default=False)
    
class Comment(models.Model):
    comment = models.TextField(null=True, blank=True)
    node = models.ForeignKey('Node', on_delete = models.CASCADE)
    user = models.ForeignKey('accounts.User',on_delete = models.CASCADE)
    commented_at = models.DateTimeField(default=datetime.now, blank=True)
    def __str__(self):
        return self.comment

class NodeConnection(models.Model):
    from_node = models.ForeignKey('Node', related_name='outgoing_connections', on_delete=models.CASCADE)
    to_node = models.ForeignKey('Node', related_name='incoming_connections', on_delete=models.CASCADE)
    mindmap = models.ForeignKey('Mindmap', on_delete=models.CASCADE)




