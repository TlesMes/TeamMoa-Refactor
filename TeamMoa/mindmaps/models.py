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
    next = models.ManyToManyField('self', symmetrical=True, blank=True ,through = "Node_Node")
    user = models.ManyToManyField('accounts.User', related_name='Nodes', through = "Node_User")

    def __str__(self):
        return self.content

class Node_Node(models.Model):
    from_node = models.ForeignKey('Node', related_name='to+', on_delete = models.CASCADE)
    to_node = models.ForeignKey('Node', related_name='from+', on_delete = models.CASCADE)
    mindmap = models.ForeignKey('Mindmap',on_delete = models.CASCADE)

class Node_User(models.Model):
    Node = models.ForeignKey('Node',on_delete = models.CASCADE)
    User = models.ForeignKey('accounts.User',on_delete = models.CASCADE)
    voted = models.BooleanField(default=False)
    comment = models.TextField()

