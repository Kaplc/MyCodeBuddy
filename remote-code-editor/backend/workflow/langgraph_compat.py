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
    
    def invoke(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """同步执行图"""
        current = self.graph.entry_point
        if not current:
            raise ValueError("No entry point set")
        
        visited = set()
        
        while current:
            if current in visited:
                break
            visited.add(current)
            
            # 执行当前节点
            node_func = self.graph.nodes.get(current)
            if node_func:
                state = node_func(state)
            
            # 检查是否有条件边
            if current in self.graph.conditional_edges:
                cond = self.graph.conditional_edges[current]
                router_result = cond['router'](state)
                next_node = cond['mapping'].get(router_result, cond['mapping'].get('default'))
            else:
                # 普通边
                next_node = self.graph.edges.get(current)
            
            if next_node == 'END' or next_node is None:
                break
                
            current = next_node
        
        return state
    
    async def ainvoke(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """异步执行图"""
        return self.invoke(state)


# END 标记
END = 'END'
