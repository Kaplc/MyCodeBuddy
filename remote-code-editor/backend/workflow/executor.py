"""Workflow 执行器"""
from __future__ import annotations

import logging
import time
from typing import Any, Dict
from django.core.exceptions import ObjectDoesNotExist
from .models import Workflow
from .cache import get_or_build_graph
from .builder import build_graph

logger = logging.getLogger('workflow')


def run_workflow_by_id(workflow_id: str, input_data: Any, workspace: str = '') -> Dict[str, Any]:
    """通过工作流ID执行工作流"""
    start_time = time.time()
    logger.info(f"[Workflow Executor] 开始执行工作流 | workflow_id={workflow_id}, workspace={workspace}")

    try:
        # 1. 获取工作流
        logger.info(f"[Workflow Executor] 获取工作流 | workflow_id={workflow_id}")
        workflow = Workflow.objects.get(id=workflow_id)
        logger.info(f"[Workflow Executor] 工作流信息 | name={workflow.name}, version={workflow.version}")

        # 2. 获取图数据
        graph_data = workflow.get_graph()
        nodes_count = len(graph_data.get('nodes', []))
        edges_count = len(graph_data.get('edges', []))
        logger.info(f"[Workflow Executor] 图数据 | nodes={nodes_count}, edges={edges_count}")

        # 3. 构建图
        logger.info(f"[Workflow Executor] 构建 LangGraph")
        graph = get_or_build_graph(str(workflow.id), graph_data, workflow.version)

        # 4. 执行图
        logger.info(f"[Workflow Executor] 开始执行图 | input_type={type(input_data).__name__}")
        invoke_start = time.time()

        result = graph.invoke({
            'input': input_data,
            'workspace': workspace,
            '_workflow_id': str(workflow.id),  # 传递 workflow_id 用于状态追踪
        }, workflow_id=str(workflow.id))

        invoke_time = int((time.time() - invoke_start) * 1000)
        logger.info(f"[Workflow Executor] 图执行完成 | invoke_time={invoke_time}ms")

        # 5. 返回结果
        total_time = int((time.time() - start_time) * 1000)
        logger.info(f"[Workflow Executor] 执行成功 | total_time={total_time}ms")
        return result

    except ObjectDoesNotExist:
        logger.error(f"[Workflow Executor] 工作流不存在 | workflow_id={workflow_id}")
        raise
    except Exception as e:
        logger.error(f"[Workflow Executor] 执行失败 | error={str(e)}")
        raise


def run_workflow_by_graph(graph_json: Dict[str, Any], input_data: Any, workspace: str = '') -> Dict[str, Any]:
    """通过图数据直接执行工作流"""
    start_time = time.time()
    nodes_count = len(graph_json.get('nodes', []))
    edges_count = len(graph_json.get('edges', []))
    logger.info(f"[Workflow Executor] 直接执行图 | nodes={nodes_count}, edges={edges_count}, workspace={workspace}")

    try:
        # 1. 构建图
        logger.info(f"[Workflow Executor] 构建 LangGraph (临时)")
        graph = build_graph(graph_json)

        # 2. 执行图
        logger.info(f"[Workflow Executor] 开始执行图 | input_type={type(input_data).__name__}")
        invoke_start = time.time()

        result = graph.invoke({
            'input': input_data,
            'workspace': workspace,
            '_workflow_id': 'temp',  # 临时工作流也传递 ID 用于状态追踪
        }, workflow_id='temp')

        invoke_time = int((time.time() - invoke_start) * 1000)
        logger.info(f"[Workflow Executor] 图执行完成 | invoke_time={invoke_time}ms")

        # 3. 返回结果
        total_time = int((time.time() - start_time) * 1000)
        logger.info(f"[Workflow Executor] 执行成功 | total_time={total_time}ms")
        return result

    except Exception as e:
        logger.error(f"[Workflow Executor] 执行失败 | error={str(e)}")
        raise
