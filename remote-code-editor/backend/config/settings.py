"""
Django项目设置
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 构建路径
BASE_DIR = Path(__file__).resolve().parent.parent

# 安全配置
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'django-insecure-dev-key-change-in-production-12345')

DEBUG = os.getenv('DEBUG', 'True').lower() == 'true'

ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')

# URL配置
ROOT_URLCONF = 'config.urls'

# WSGI/ASGI配置
WSGI_APPLICATION = 'config.wsgi.application'
ASGI_APPLICATION = 'config.asgi.application'

# 应用定义
INSTALLED_APPS = [
    'daphne',  # ASGI服务器，必须放在第一位
    'django.contrib.contenttypes',
    'django.contrib.staticfiles',
    
    # 第三方应用
    'rest_framework',
    'corsheaders',
    'channels',
    
    # 本地应用
    'api',
]

# 中间件
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',  # CORS中间件，放在CommonMiddleware之前
    'django.middleware.common.CommonMiddleware',
]

# CORS配置
CORS_ALLOW_ALL_ORIGINS = True  # 开发环境允许所有来源
CORS_ALLOW_CREDENTIALS = True

# REST Framework配置
REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.AllowAny',
    ],
    'DEFAULT_AUTHENTICATION_CLASSES': [],  # 无需认证
    'EXCEPTION_HANDLER': 'api.exceptions.custom_exception_handler',  # 自定义异常处理
}

# Channel Layer配置（用于WebSocket）
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels.layers.InMemoryChannelLayer',  # 开发环境使用内存
    },
}

# 模板配置（暂不需要模板）
TEMPLATES = []

# 数据库配置
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# 国际化
LANGUAGE_CODE = 'zh-hans'
TIME_ZONE = 'Asia/Shanghai'
USE_I18N = True
USE_TZ = True

# 静态文件
STATIC_URL = 'static/'

# 默认主键字段类型
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# 工作目录配置
# 优先从配置文件读取，其次从环境变量读取，最后使用默认值
_config_file = BASE_DIR / 'workspace_config.json'
WORKSPACE_PATH = ''  # 默认为空白，用户设置后才会有值

if _config_file.exists():
    try:
        import json
        with open(_config_file, 'r', encoding='utf-8') as f:
            _config = json.load(f)
            _workspace = _config.get('workspace_path', '')
            # 只有当配置文件中存在有效路径时才使用
            if _workspace and os.path.isdir(_workspace):
                WORKSPACE_PATH = _workspace
    except Exception:
        pass

# 如果配置文件没有设置，使用环境变量（仅用于开发环境）
if not WORKSPACE_PATH and os.getenv('WORKSPACE_PATH'):
    WORKSPACE_PATH = os.getenv('WORKSPACE_PATH')

# 智谱AI API密钥
ZHIPU_API_KEY = os.getenv('ZHIPU_API_KEY', '')

# GitHub访问令牌
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN', '')

# 日志配置
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
        'detailed': {
            'format': '{asctime} {levelname} {name} {module}:{lineno} - {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
        'file': {
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'django.log'),
            'when': 'M',             # 按分钟轮转
            'interval': 20,          # 每20分钟创建一个新文件
            'backupCount': 504,      # 保留7天日志（7天*24小时*3个/小时=504）
            'formatter': 'detailed',
            'encoding': 'utf-8',
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'api': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}
