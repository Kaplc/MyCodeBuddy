"""Agent Router - 统一 AI 调用入口"""
from __future__ import annotations

from typing import Any, Dict, List
from django.conf import settings
from services.ai_service import AIService
from .utils import run_async


_ai_service = AIService(settings.ZHIPU_API_KEY)


def _build_messages(state: Dict[str, Any]) -> List[Dict[str, str]]:
    if 'messages' in state and isinstance(state['messages'], list):
        return state['messages']
    
    # 获取用户输入
    user_input = state.get('prompt') or state.get('input') or ''
    
    # 获取agent任务描述
    agent_task = state.get('_agent_task', '')
    
    # 如果有agent任务，将其包含在消息中
    if agent_task:
        content = f"任务：{agent_task}\n\n用户输入：{user_input}"
    else:
        content = str(user_input)
    
    return [{"role": "user", "content": content}]


def route_agent(name: str, state: Dict[str, Any]) -> str:
    """根据 Agent 名称路由请求"""
    messages = _build_messages(state)

    # 预留：不同 Agent 可配置不同策略
    if name in {'general_agent', 'chat_agent'}:
        return run_async(_ai_service.chat_sync(messages))

    # 默认行为：使用普通对话
    return run_async(_ai_service.chat_sync(messages))
