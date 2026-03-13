"""Condition 节点"""
from __future__ import annotations

from typing import Any, Dict


def _safe_eval(expression: str, state: Dict[str, Any]) -> bool:
    if not expression:
        return False
    try:
        return bool(eval(expression, {"__builtins__": {}}, state))
    except Exception:
        return False


def condition_node(config: Dict[str, Any]):
    expression = str(config.get('expression', '')).strip()

    def run(state: Dict[str, Any]) -> Dict[str, Any]:
        result = _safe_eval(expression, state)
        state['_route_key'] = 'true' if result else 'false'
        return state

    return run


def condition_router(config: Dict[str, Any]):
    expression = str(config.get('expression', '')).strip()
    default_route = config.get('default', 'false')

    def route(state: Dict[str, Any]) -> str:
        if '_route_key' in state:
            return str(state['_route_key'])
        result = _safe_eval(expression, state)
        return 'true' if result else default_route

    return route
