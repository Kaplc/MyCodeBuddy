"""Workflow 执行器"""
from __future__ import annotations

from typing import Any, Dict
from django.core.exceptions import ObjectDoesNotExist
from .models import Workflow
from .cache import get_or_build_graph
from .builder import build_graph


def run_workflow_by_id(workflow_id: str, input_data: Any, workspace: str = '') -> Dict[str, Any]:
    workflow = Workflow.objects.get(id=workflow_id)
    # 使用 get_graph() 将 JSON 字符串解析为字典
    graph = get_or_build_graph(str(workflow.id), workflow.get_graph(), workflow.version)
    result = graph.invoke({
        'input': input_data,
        'workspace': workspace,
    })
    return result


def run_workflow_by_graph(graph_json: Dict[str, Any], input_data: Any, workspace: str = '') -> Dict[str, Any]:
    graph = build_graph(graph_json)
    result = graph.invoke({
        'input': input_data,
        'workspace': workspace,
    })
    return result
