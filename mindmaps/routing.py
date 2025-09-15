from django.urls import re_path, path
from . import consumers

websocket_urlpatterns = [
    # WebSocket URL: /ws/mindmap/{team_id}/{mindmap_id}/
    re_path(r'ws/mindmap/(?P<team_id>\d+)/(?P<mindmap_id>\d+)/$', consumers.MindmapConsumer.as_asgi()),
]