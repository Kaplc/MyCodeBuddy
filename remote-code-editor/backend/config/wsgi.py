"""
WSGI配置
"""
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# 本项目主要使用ASGI，WSGI仅用于兼容
