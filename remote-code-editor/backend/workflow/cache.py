"""Workflow Graph 缓存"""
from __future__ import annotations

from typing import Any, Dict
from .builder import build_graph


_graph_cache: Dict[str, Dict[str, Any]] = {}

# 执行状态存储：用于实时显示当前执行的节点
_execution_state: Dict[str, Dict[str, Any]] = {}


def get_graph_cache_key(workflow_id: str) -> str:
    return str(workflow_id)


def get_or_build_graph(workflow_id: str, graph_json: Dict[str, Any], version: int) -> Any:
    """获取缓存的 Graph，如版本不一致则重建"""
    # 兼容 graph_json 是字符串的情况
    if isinstance(graph_json, str):
        import json
        graph_json = json.loads(graph_json)

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


# 执行状态管理函数
def set_execution_state(workflow_id: str, node_id: str, status: str = 'running', 
                        details: Dict[str, Any] = {}) -> None:
    """设置当前执行的节点状态"""
    current_state = _execution_state.get(workflow_id, {})
    
    _execution_state[workflow_id] = {
        'node_id': node_id,
        'status': status,
        'details': details or {},
        'updated_at': __import__('time').time()
    }
    
    # 合并之前的状态（保留一些字段）
    if current_state.get('start_time'):
        _execution_state[workflow_id]['start_time'] = current_state['start_time']
    else:
        _execution_state[workflow_id]['start_time'] = __import__('time').time()
    
    import logging
    logger = logging.getLogger('workflow')
    logger.info(f"[Execution State] 更新执行状态 | workflow_id={workflow_id}, node_id={node_id}, status={status}, details={details}")


def update_execution_details(workflow_id: str, details: Dict[str, Any]) -> None:
    """更新执行状态详情（不改变节点和状态）"""
    if workflow_id in _execution_state:
        _execution_state[workflow_id]['details'].update(details)
        _execution_state[workflow_id]['updated_at'] = __import__('time').time()
        
        import logging
        logger = logging.getLogger('workflow')
        logger.info(f"[Execution State] 更新执行详情 | workflow_id={workflow_id}, details={details}")


def get_execution_state(workflow_id: str) -> Dict[str, Any]:
    """获取当前执行的节点状态"""
    state = _execution_state.get(workflow_id, {
        'node_id': None, 
        'status': 'idle',
        'details': {},
        'start_time': None,
        'updated_at': None
    })
    import logging
    logger = logging.getLogger('workflow')
    logger.info(f"[Execution State] 查询执行状态 | workflow_id={workflow_id}, state={state}")
    return state


def clear_execution_state(workflow_id: str) -> None:
    """清除执行状态"""
    _execution_state.pop(workflow_id, None)
    import logging
    logger = logging.getLogger('workflow')
    logger.info(f"[Execution State] 清除执行状态 | workflow_id={workflow_id}")


# 气泡记录存储
_bubble_records: Dict[str, list] = {}


def add_bubble_record(workflow_id: str, record: Dict[str, Any]) -> None:
    """添加气泡记录"""
    if workflow_id not in _bubble_records:
        _bubble_records[workflow_id] = []
    _bubble_records[workflow_id].append(record)

    import logging
    logger = logging.getLogger('workflow')
    logger.info(f"[Bubble Record] 添加气泡记录 | workflow_id={workflow_id}, tool={record.get('tool_name')}")


def get_bubble_records(workflow_id: str) -> list:
    """获取气泡记录"""
    return _bubble_records.get(workflow_id, [])


def clear_bubble_records(workflow_id: str) -> None:
    """清除气泡记录"""
    _bubble_records.pop(workflow_id, None)
