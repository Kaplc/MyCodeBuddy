"""Agent 节点"""
from typing import Any, Dict
from ..agent_router import route_agent


def agent_node(config: Dict[str, Any]):
    agent_name = config.get('name', 'general_agent')
    task = config.get('task', '')  # 任务描述

    def run(state: Dict[str, Any]) -> Dict[str, Any]:
        # 将任务描述传入状态
        if task:
            state['_agent_task'] = task
        result = route_agent(agent_name, state)
        state['result'] = result
        return state

    return run
