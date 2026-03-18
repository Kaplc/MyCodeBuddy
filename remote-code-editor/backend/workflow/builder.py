"""Workflow Builder - JSON Graph -> LangGraph"""
from __future__ import annotations

import logging
from typing import Any, Dict
from .langgraph_compat import StateGraph, END
from .nodes import create_node_executor, create_condition_router

logger = logging.getLogger('workflow')

# 多输出节点类型(需要条件路由)
MULTI_OUTPUT_NODES = {
    'condition', 'branch', 'sequence', 'gate',
    'do_once', 'flip_flop', 'for_loop', 'delay'
}


def build_graph(workflow_json: Dict[str, Any]):
    """构建 LangGraph 图"""
    # 兼容 workflow_json 是字符串的情况
    if isinstance(workflow_json, str):
        import json
        workflow_json = json.loads(workflow_json)

    builder = StateGraph(dict)

    # 支持新版 v2.0 和旧版 v1.0 格式
    nodes = workflow_json.get('nodes', [])
    edges = workflow_json.get('edges', [])

    # 记录工作流构建元数据
    version = workflow_json.get('version', '1.0')
    logger.info(f"[Workflow Builder] 构建图: version={version}, nodes={len(nodes)}, edges={len(edges)}")

    node_map: Dict[str, Dict[str, Any]] = {}
    for node in nodes:
        node_id = str(node.get('id'))
        node_data = normalize_node_data(node)
        node_map[node_id] = node_data

        # 添加节点到图中
        builder.add_node(node_id, create_node_executor(node_data))

        # 记录节点详细信息
        node_type = node_data.get('type', 'unknown')
        node_label = node_data.get('label', node_id)
        logger.debug(f"[Workflow Builder] 添加节点: id={node_id}, type={node_type}, label={node_label}")

    # 识别多输出节点
    multi_output_nodes = {
        node_id: node
        for node_id, node in node_map.items()
        if str(node.get('type', '')).lower() in MULTI_OUTPUT_NODES
    }

    # 普通连线
    logger.info(f"[Workflow Builder] 开始添加普通边 | edges_count={len(edges)}")
    for idx, edge in enumerate(edges):
        source = str(edge.get('source', '')).strip()
        target = str(edge.get('target', '')).strip()
        edge_id = edge.get('id', 'unknown')
        logger.info(f"[Workflow Builder] 边 {idx+1}/{len(edges)} | id={edge_id}, source='{source}', target='{target}'")
        
        if not source or not target:
            logger.warning(f"[Workflow Builder] 跳过无效边 | source='{source}', target='{target}'")
            continue
            
        if source in multi_output_nodes:
            logger.info(f"[Workflow Builder] 跳过多输出节点边 | source={source}")
            continue
        builder.add_edge(source, target)
        logger.info(f"[Workflow Builder] 已添加边 | {source} -> {target}")

    # 多输出节点连线
    for node_id, node in multi_output_nodes.items():
        config = node.get('config') or {}
        routes = config.get('routes')
        if not routes:
            routes = {}
            for edge in edges:
                if str(edge.get('source')) == node_id:
                    # 兼容新旧版本：优先使用 sourceHandle，其次使用 source_handle，最后使用 condition
                    condition = edge.get('sourceHandle') or edge.get('source_handle') or edge.get('condition', 'default')
                    routes[str(condition)] = str(edge.get('target'))
        if not routes:
            routes = {'default': END}

        logger.debug(f"[Workflow Builder] 添加条件边: {node_id}, routes={list(routes.keys())}")
        builder.add_conditional_edges(
            node_id,
            create_condition_router(node),
            routes,
        )

    # 输出节点默认结束
    for node_id, node in node_map.items():
        if str(node.get('type', '')).lower() == 'output':
            has_outgoing = any(str(edge.get('source')) == node_id for edge in edges)
            if not has_outgoing:
                builder.add_edge(node_id, END)

    entry = workflow_json.get('entry')
    if not entry and nodes:
        entry = str(nodes[0].get('id'))

    if entry:
        builder.set_entry_point(str(entry))

    logger.info(f"[Workflow Builder] 图构建完成: entry={entry}")
    return builder.compile()


def normalize_node_data(node: Dict[str, Any]) -> Dict[str, Any]:
    """
    规范化节点数据，兼容新旧版本格式

    新版 v2.0 格式:
    {
        "id": "1",
        "type": "tool",
        "label": "read_file",
        "config": {...},
        "metadata": {...}
    }

    旧版 v1.0 格式:
    {
        "id": "1",
        "type": "tool",
        "config": {...}
    }
    """
    normalized = {
        'id': str(node.get('id', '')),
        'type': node.get('type', 'prompt'),
        'label': node.get('label'),
        'position': node.get('position'),
        'config': node.get('config', {}),
        'metadata': node.get('metadata', {})
    }

    # 如果没有 label，从 config 中推断
    if not normalized['label']:
        wf_type = normalized['type']
        config = normalized['config']
        if wf_type == 'tool':
            normalized['label'] = config.get('tool', 'tool')
        elif wf_type == 'agent':
            normalized['label'] = config.get('name', 'agent')
        else:
            normalized['label'] = wf_type

    return normalized
