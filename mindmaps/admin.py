from django.contrib import admin
from .models import Comment, Mindmap, Node, NodeConnection
# Register your models here.

admin.site.register(Mindmap)
admin.site.register(Node)
admin.site.register(NodeConnection)
admin.site.register(Comment)