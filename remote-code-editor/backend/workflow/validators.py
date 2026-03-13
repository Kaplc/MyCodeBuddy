"""Workflow 校验逻辑"""
from typing import Any, Dict, Set, Tuple


REQUIRED_NODE_FIELDS = {'id', 'type'}


def validate_workflow_graph(graph: Dict[str, Any]) -> Tuple[bool, str]:
    """校验工作流 JSON 结构"""
    if not isinstance(graph, dict):
        return False, 'graph 必须是对象'

    nodes = graph.get('nodes')
    edges = graph.get('edges')

    if not isinstance(nodes, list) or not nodes:
        return False, 'nodes 必须是非空数组'
    if not isinstance(edges, list):
        return False, 'edges 必须是数组'

    node_ids: Set[str] = set()
    for node in nodes:
        if not isinstance(node, dict):
            return False, 'nodes 中的每个节点必须是对象'
        if not REQUIRED_NODE_FIELDS.issubset(node.keys()):
            return False, '节点必须包含 id 和 type'
        node_id = str(node['id'])
        if node_id in node_ids:
            return False, f'节点 id 重复: {node_id}'
        node_ids.add(node_id)

    for edge in edges:
        if not isinstance(edge, dict):
            return False, 'edges 中的每个连线必须是对象'
        source = edge.get('source')
        target = edge.get('target')
        if not source or not target:
            return False, '连线必须包含 source 和 target'
        if source not in node_ids or target not in node_ids:
            return False, f'连线引用了不存在的节点: {source} -> {target}'

    return True, ''
