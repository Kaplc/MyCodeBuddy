"""
ASGI配置 - 支持WebSocket
"""
import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# Django ASGI应用
django_asgi_app = get_asgi_application()

# 导入WebSocket路由（必须在get_asgi_application之后）
from api.routing import websocket_urlpatterns

# 协议路由器
application = ProtocolTypeRouter({
    'http': django_asgi_app,
    'websocket': URLRouter(websocket_urlpatterns)  # 移除AuthMiddlewareStack，因为不需要认证
})
