"""Workflow Graph 缓存"""
from __future__ import annotations

from typing import Any, Dict
from .builder import build_graph


_graph_cache: Dict[str, Dict[str, Any]] = {}


def get_graph_cache_key(workflow_id: str) -> str:
    return str(workflow_id)


def get_or_build_graph(workflow_id: str, graph_json: Dict[str, Any], version: int) -> Any:
    """获取缓存的 Graph，如版本不一致则重建"""
    cache_key = get_graph_cache_key(workflow_id)
    cached = _graph_cache.get(cache_key)

    if cached and cached.get('version') == version:
        return cached['graph']

    compiled = build_graph(graph_json)
    _graph_cache[cache_key] = {
        'version': version,
        'graph': compiled,
    }
    return compiled


def clear_graph_cache(workflow_id: str | None = None) -> None:
    if workflow_id is None:
        _graph_cache.clear()
        return
    cache_key = get_graph_cache_key(workflow_id)
    _graph_cache.pop(cache_key, None)
