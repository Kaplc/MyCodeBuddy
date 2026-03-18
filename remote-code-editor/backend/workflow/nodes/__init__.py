"""Workflow 节点执行器"""
from __future__ import annotations

import logging
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

logger = logging.getLogger('workflow')


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
    node_id = str(node.get('id', ''))
    node_label = node.get('label', node_type)
    config = node.get('config') or {}

    factory = NODE_EXECUTORS.get(node_type)
    if not factory:
        return lambda state: state

    executor = factory(config)

    def wrapped_executor(state: Dict[str, Any]) -> Dict[str, Any]:
        # 获取 workflow_id 用于更新执行状态
        workflow_id = state.get('_workflow_id')

        if workflow_id:
            # 导入并更新执行状态
            from ..cache import set_execution_state, add_bubble_record
            from datetime import datetime
            set_execution_state(workflow_id, node_id, 'running')

            # 发送节点开始执行的气泡消息
            add_bubble_record(workflow_id, {
                'type': 'agent_node',
                'node_id': node_id,
                'node_type': node_type,
                'label': node_label or node_type,
                'content': f'开始执行 {node_type} 节点: {node_label or node_id}',
                'timestamp': datetime.now().isoformat()
            })

            logger.info(f"[Node Executor] 开始执行节点 | node_id={node_id}, node_type={node_type}, workflow_id={workflow_id}")
            logger.info(f"[Node Executor]    节点配置 | config={config}")
        else:
            logger.warning(f"[Node Executor] 未找到 workflow_id，跳过状态更新 | node_id={node_id}")

        # 执行节点
        import time
        exec_start = time.time()
        result = executor(state)
        exec_time = int((time.time() - exec_start) * 1000)

        if workflow_id:
            logger.info(f"[Node Executor] 节点执行完成 | node_id={node_id}, node_type={node_type}, exec_time={exec_time}ms")
            logger.info(f"[Node Executor]    输出键 | keys={list(result.keys())}")

        return result

    return wrapped_executor


def create_condition_router(node: Dict[str, Any]) -> Callable[[Dict[str, Any]], str]:
    node_type = str(node.get('type', '')).lower()
    config = node.get('config') or {}
    
    # 优先使用专用路由器
    router_factory = CONDITION_ROUTERS.get(node_type)
    if router_factory:
        return router_factory(config)
    
    # 回退到条件路由器
    return condition_router(config)
