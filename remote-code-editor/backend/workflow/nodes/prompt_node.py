"""Prompt 节点"""
from typing import Any, Dict
from services.ai_service import AIService
from django.conf import settings
from ..utils import run_async


_ai_service = AIService(settings.ZHIPU_API_KEY)


def prompt_node(config: Dict[str, Any]):
    template = config.get('template', '{input}')
    thinking_mode = bool(config.get('thinking', False))

    def run(state: Dict[str, Any]) -> Dict[str, Any]:
        prompt = str(template).format(**state)
        messages = [{"role": "user", "content": prompt}]
        result = run_async(_ai_service.chat_sync(messages, thinking_mode=thinking_mode))
        state['prompt'] = prompt
        state['result'] = result
        return state

    return run
