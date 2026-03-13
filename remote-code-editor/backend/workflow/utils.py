"""Workflow 运行时工具"""
from __future__ import annotations

import asyncio
from typing import Any, Dict


def run_async(coro: Any) -> Any:
    """在同步上下文运行异步协程"""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        new_loop = asyncio.new_event_loop()
        try:
            return new_loop.run_until_complete(coro)
        finally:
            new_loop.close()

    return asyncio.run(coro)


def resolve_templates(value: Any, state: Dict[str, Any]) -> Any:
    """递归解析模板字符串"""
    if isinstance(value, str):
        try:
            return value.format(**state)
        except Exception:
            return value
    if isinstance(value, list):
        return [resolve_templates(item, state) for item in value]
    if isinstance(value, dict):
        return {key: resolve_templates(item, state) for key, item in value.items()}
    return value
