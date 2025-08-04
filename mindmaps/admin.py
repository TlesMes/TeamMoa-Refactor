from django.contrib import admin
from .models import Comment, Mindmap, Node, Node_Node, Node_User
# Register your models here.

admin.site.register(Mindmap)
admin.site.register(Node)
admin.site.register(Node_User)
admin.site.register(Node_Node)
admin.site.register(Comment)