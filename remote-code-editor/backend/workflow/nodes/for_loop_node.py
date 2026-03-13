"""ForLoop 节点 - 循环 (参考UE蓝图)"""
from __future__ import annotations

from typing import Any, Dict


def for_loop_node(config: Dict[str, Any]):
    """ForLoop 节点 - 循环执行指定次数
    
    配置:
    - start: 起始索引 (默认0)
    - end: 结束索引 (默认10)
    - step: 步长 (默认1)
    """
    start_index = config.get('start', 0)
    end_index = config.get('end', 10)
    step = config.get('step', 1)
    
    def run(state: Dict[str, Any]) -> Dict[str, Any]:
        loop_state = state.get('_for_loop', {})
        node_id = state.get('_current_node_id', 'default')
        
        # 获取当前循环索引
        current_index = loop_state.get(node_id, start_index)
        
        # 检查是否完成循环
        if current_index < end_index:
            # 继续循环
            state['_route_key'] = 'loop'
            state['_loop_index'] = current_index
            loop_state[node_id] = current_index + step
        else:
            # 循环完成
            state['_route_key'] = 'completed'
            loop_state[node_id] = start_index  # 重置
        
        state['_for_loop'] = loop_state
        return state

    return run


def for_loop_router(config: Dict[str, Any]):
    """路由到 loop 或 completed 输出"""
    def route(state: Dict[str, Any]) -> str:
        if '_route_key' in state:
            return str(state['_route_key'])
        return 'loop'  # 默认开始循环
    
    return route
