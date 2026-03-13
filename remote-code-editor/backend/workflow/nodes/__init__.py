"""Workflow 节点执行器"""
from __future__ import annotations

from typing import Any, Callable, Dict
from .input_node import input_node
from .prompt_node import prompt_node
from .agent_node import agent_node
from .tool_node import tool_node
from .condition_node import condition_node, condition_router
from .output_node import output_node
# 流程控制节点
from .branch_node import branch_node, branch_router
from .for_loop_node import for_loop_node, for_loop_router
# 匹配节点
from .match_node import match_node


NODE_EXECUTORS = {
    'input': input_node,
    'prompt': prompt_node,
    'agent': agent_node,
    'tool': tool_node,
    'condition': condition_node,
    'output': output_node,
    # 流程控制节点
    'branch': branch_node,
    'for_loop': for_loop_node,
    # 匹配节点
    'match': match_node,
}

# 条件路由器映射
CONDITION_ROUTERS = {
    'condition': condition_router,
    'branch': branch_router,
    'for_loop': for_loop_router,
}


def create_node_executor(node: Dict[str, Any]) -> Callable[[Dict[str, Any]], Dict[str, Any]]:
    node_type = str(node.get('type', '')).lower()
    config = node.get('config') or {}

    factory = NODE_EXECUTORS.get(node_type)
    if not factory:
        return lambda state: state

    return factory(config)


def create_condition_router(node: Dict[str, Any]) -> Callable[[Dict[str, Any]], str]:
    node_type = str(node.get('type', '')).lower()
    config = node.get('config') or {}
    
    # 优先使用专用路由器
    router_factory = CONDITION_ROUTERS.get(node_type)
    if router_factory:
        return router_factory(config)
    
    # 回退到条件路由器
    return condition_router(config)
