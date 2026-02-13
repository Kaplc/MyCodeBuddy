"""
WebSocket路由配置
"""
from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'^api/ai/chat/?$', consumers.AIChatConsumer.as_asgi()),
]
