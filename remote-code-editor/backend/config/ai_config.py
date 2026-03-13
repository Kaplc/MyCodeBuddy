"""
AI 配置管理模块
支持从外部 JSON 文件加载模型和 API 配置，支持热加载
"""
import json
import os
from pathlib import Path
from typing import Any, Optional, Dict, List
from django.conf import settings

# 配置文件路径
CONFIG_DIR = Path(__file__).parent
AI_CONFIG_FILE = CONFIG_DIR / 'ai_config.json'

# 缓存
_config_cache: Optional[Dict[str, Any]] = None
_config_mtime: float = 0


def load_ai_config() -> Dict[str, Any]:
    """
    加载 AI 配置文件
    支持热加载：如果文件被修改，自动重新加载
    """
    global _config_cache, _config_mtime
    
    try:
        # 检查文件修改时间
        current_mtime = os.path.getmtime(AI_CONFIG_FILE)
        
        # 如果缓存存在且文件未修改，返回缓存
        if _config_cache is not None and current_mtime == _config_mtime:
            return _config_cache
        
        # 重新加载配置
        with open(AI_CONFIG_FILE, 'r', encoding='utf-8') as f:
            loaded_config = json.load(f)
            _config_cache = loaded_config
            _config_mtime = current_mtime
            
        return loaded_config
        
    except FileNotFoundError:
        # 返回默认配置
        default_config: Dict[str, Any] = {
            "models": [
                {"id": "", "name": "默认", "description": "使用系统默认模型", "provider": "default"}
            ],
            "providers": {},
            "default_provider": "",
            "default_model": ""
        }
        _config_cache = default_config
        return default_config
    except json.JSONDecodeError as e:
        print(f"[AI配置] 配置文件解析错误: {e}")
        if _config_cache is not None:
            return _config_cache
        return {"models": [], "providers": {}}


def get_models() -> List[Dict[str, Any]]:
    """获取可用模型列表"""
    config = load_ai_config()
    return config.get('models', [])


def get_model_by_id(model_id: str) -> Optional[Dict[str, Any]]:
    """根据 ID 获取模型配置"""
    models = get_models()
    for model in models:
        if model.get('id') == model_id:
            return model
    return None


def get_providers() -> Dict[str, Any]:
    """获取 Provider 配置"""
    config = load_ai_config()
    return config.get('providers', {})


def get_provider(name: str) -> Optional[Dict[str, Any]]:
    """获取指定 Provider 配置"""
    providers = get_providers()
    return providers.get(name)


def get_api_key(provider: str) -> Optional[str]:
    """
    获取指定 Provider 的 API Key
    优先从配置文件中的 api_key 字段读取，其次从环境变量读取
    """
    provider_config = get_provider(provider)
    if not provider_config:
        return None
    
    # 1. 直接配置的 API Key（不推荐，仅用于测试）
    if provider_config.get('api_key'):
        return str(provider_config['api_key'])
    
    # 2. 从环境变量读取
    env_key = provider_config.get('api_key_env')
    if env_key:
        return os.environ.get(str(env_key))
    
    return None


def get_default_provider() -> str:
    """获取默认 Provider"""
    config = load_ai_config()
    return str(config.get('default_provider', ''))


def get_default_model() -> str:
    """获取默认模型"""
    config = load_ai_config()
    return str(config.get('default_model', ''))


def get_model_config(model_id: Optional[str] = None) -> Dict[str, Any]:
    """
    获取完整的模型运行配置
    包含模型信息、Provider 配置、API Key 等
    """
    if model_id is None:
        model_id = get_default_model()
    
    model = get_model_by_id(model_id)
    if not model:
        return {}
    
    provider_name = model.get('provider')
    provider = get_provider(str(provider_name)) if provider_name else None
    api_key = get_api_key(str(provider_name)) if provider_name else None
    
    return {
        'model': model,
        'provider': provider,
        'api_key': api_key,
        'base_url': provider.get('base_url') if provider else None
    }


def reload_config() -> Dict[str, Any]:
    """强制重新加载配置"""
    global _config_cache, _config_mtime
    _config_cache = None
    _config_mtime = 0
    return load_ai_config()
