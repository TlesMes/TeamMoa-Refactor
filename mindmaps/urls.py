from django.urls import path
from . import views

app_name = 'mindmaps'

urlpatterns = [
    path('mindmap_list_page/<int:pk>', views.mindmap_list_page, name='mindmap_list_page'),
    path('mindmap_detail_page/<int:pk>/<int:mindmap_id>', views.mindmap_detail_page, name='mindmap_detail_page'),
    path('mindmap_create/<int:pk>', views.mindmap_create, name='mindmap_create'),
    path('mindmap_delete/<int:pk>/<int:mindmap_id>', views.mindmap_delete, name='mindmap_delete'),
    path('mindmap_create_node/<int:pk>/<int:mindmap_id>', views.mindmap_create_node, name='mindmap_create_node'),
    path('mindmap_delete_node/<int:pk>/<int:node_id>', views.mindmap_delete_node, name='mindmap_delete_node'),
    path('mindmap_empower/<int:pk>/<int:mindmap_id>/<int:user_id>', views.mindmap_empower, name='mindmap_empower'),
    path('node_detail_page/<int:pk>/<int:node_id>', views.node_detail_page, name='node_detail_page'),
    path('node_vote/<int:pk>/<int:node_id>', views.node_vote, name='node_vote'),  # 하위 호환성
    path('node_recommend/<int:pk>/<int:node_id>', views.node_recommend, name='node_recommend'),  # 새 이름
]