"""
LangGraph 兼容层 - 为 Python 3.8 提供基本功能
"""
from typing import Any, Callable, Dict, List, Optional, Union
from typing import TypedDict


class StateGraph:
    """
    简化版 StateGraph，用于替代 langgraph.graph.StateGraph
    """
    
    def __init__(self, state_class):
        self.state_class = state_class
        self.nodes: Dict[str, Callable] = {}
        self.edges: Dict[str, str] = {}
        self.conditional_edges: Dict[str, Dict[str, str]] = {}
        self.entry_point: Optional[str] = None
    
    def add_node(self, node_name: str, func: Callable):
        """添加一个节点"""
        self.nodes[node_name] = func
        return self
    
    def add_edge(self, from_node: str, to_node: str):
        """添加普通边"""
        self.edges[from_node] = to_node
        return self
    
    def add_conditional_edges(
        self, 
        node_name: str, 
        router: Callable, 
        mapping: Dict[str, str]
    ):
        """添加条件边"""
        self.conditional_edges[node_name] = {
            'router': router,
            'mapping': mapping
        }
        return self
    
    def set_entry_point(self, node_name: str):
        """设置入口点"""
        self.entry_point = node_name
        return self
    
    def compile(self):
        """编译图为可执行对象"""
        return GraphRunner(self)


class GraphRunner:
    """编译后的图运行器"""

    def __init__(self, graph: StateGraph):
        self.graph = graph

    def invoke(self, state: Dict[str, Any], workflow_id: str = None) -> Dict[str, Any]:
        """同步执行图"""
        from .cache import set_execution_state, clear_execution_state
        import logging
        logger = logging.getLogger('workflow')

        current = self.graph.entry_point
        if not current:
            raise ValueError("No entry point set")

        visited = set()

        # 记录图结构信息
        logger.info(f"[GraphRunner] 开始执行图 | entry={current}")
        logger.info(f"[GraphRunner] 图结构信息 | nodes={list(self.graph.nodes.keys())}")
        logger.info(f"[GraphRunner] 图结构信息 | edges={self.graph.edges}")
        logger.info(f"[GraphRunner] 图结构信息 | conditional_edges={list(self.graph.conditional_edges.keys())}")

        while current:
            if current in visited:
                logger.warning(f"[GraphRunner] 检测到循环访问 | current={current}, visited={visited}")
                break
            visited.add(current)

            logger.info(f"[GraphRunner] 执行节点 | current={current}")

            # 更新执行状态
            if workflow_id:
                set_execution_state(workflow_id, current, 'running')

            # 执行当前节点
            node_func = self.graph.nodes.get(current)
            if node_func:
                state = node_func(state)

            # 检查是否有条件边
            if current in self.graph.conditional_edges:
                cond = self.graph.conditional_edges[current]
                router_result = cond['router'](state)
                next_node = cond['mapping'].get(router_result, cond['mapping'].get('default'))
                logger.info(f"[GraphRunner] 条件路由 | current={current}, router_result={router_result}, next_node={next_node}")
            else:
                # 普通边
                next_node = self.graph.edges.get(current)
                logger.info(f"[GraphRunner] 普通边查找 | current={current}, next_node={next_node}")

            if next_node == 'END' or next_node is None:
                logger.info(f"[GraphRunner] 到达终点 | next_node={next_node}")
                break

            current = next_node

        # 清除执行状态
        if workflow_id:
            clear_execution_state(workflow_id)

        logger.info(f"[GraphRunner] 图执行完成 | visited_nodes={visited}")
        return state

    async def ainvoke(self, state: Dict[str, Any], workflow_id: str = None) -> Dict[str, Any]:
        """异步执行图"""
        return self.invoke(state, workflow_id)


# END 标记
END = 'END'
