"""节点细化服务"""
from __future__ import annotations

import json
import logging
from typing import Any, Dict, List
from django.conf import settings

from services.ai_service import AIService

logger = logging.getLogger('workflow')


NODE_TOOL_SUGGESTIONS = {
    'analysis': ['search_content', 'list_directory'],
    'read': ['read_file', 'search_content'],
    'modify': ['read_file', 'write_file', 'execute_command'],
    'verify': ['execute_command', 'read_file'],
    'checkpoint': ['read_file']
}


def _call_llm_for_detail_plan(node: Dict[str, Any], goal: str) -> Dict[str, Any]:
    """
    调用大模型为单个节点生成详细执行计划

    Args:
        node: 节点信息，包含 id, title, type, description 等
        goal: 用户原始目标

    Returns:
        包含详细步骤、工具计划、约束等信息的字典
    """
    node_id = node.get('id', 'unknown')
    logger.info(f"[LLM] 开始为节点 {node_id} 调用大模型生成详细计划")

    try:
        api_key = getattr(settings, 'ZHIPU_API_KEY', '')
        if not api_key:
            logger.warning(f"[LLM] 未配置 ZHIPU_API_KEY，节点 {node_id} 使用默认模板")
            return _get_default_detail(node)

        ai_service = AIService(api_key)

        node_type = node.get('type', 'analysis')
        node_title = node.get('title', '')
        node_desc = node.get('description', '')

        logger.info(f"[LLM] 节点信息: type={node_type}, title={node_title}")

        # 构造 prompt
        prompt = f"""用户目标: {goal}

请为以下任务节点生成详细的执行计划：

节点ID: {node.get('id', '')}
节点标题: {node_title}
节点类型: {node_type}
节点描述: {node_desc}

请以 JSON 格式返回，包含以下字段：
- title: 任务标题
- steps: 执行步骤列表（3-5步），每步包含 description 描述
- tool_plan: 建议使用的工具列表
- constraints: 约束条件列表
- success_criteria: 成功标准列表
- risk_flags: 风险标记列表 (low/medium/high)
- require_runtime_approval: 是否需要运行时审批 (true/false)
- fallback: 回退策略

请直接返回 JSON，不要包含其他文字。"""

        logger.info(f"[LLM] 发送请求到智谱AI, prompt长度={len(prompt)}")

        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(ai_service.chat_sync(
                messages=[{"role": "user", "content": prompt}],
                thinking_mode=False
            ))
        finally:
            loop.close()

        logger.info(f"[LLM] 收到响应, 长度={len(result) if result else 0}")

        # 解析 JSON 结果
        if result:
            result = result.strip()
            # 尝试提取 JSON
            if '{' in result:
                start = result.find('{')
                end = result.rfind('}') + 1
                json_str = result[start:end]
                detail_plan = json.loads(json_str)
                detail_plan['node_id'] = node_id
                logger.info(f"[LLM] 解析成功: 节点 {node_id}, title={detail_plan.get('title', '')}")
                return detail_plan
            else:
                logger.warning(f"[LLM] 响应中无JSON: {result[:200]}")
    except json.JSONDecodeError as e:
        logger.error(f"[LLM] JSON解析失败: {e}")
    except Exception as e:
        logger.error(f"[LLM] 调用异常: {e}")

    logger.info(f"[LLM] 节点 {node_id} 回退到默认模板")
    return _get_default_detail(node)


def _get_default_detail(node: Dict[str, Any]) -> Dict[str, Any]:
    """返回默认的详细计划模板"""
    node_type = node.get('type', 'analysis')
    return {
        'node_id': node.get('id', ''),
        'title': node.get('title', ''),
        'steps': [
            {'description': '确认输入与目标边界'},
            {'description': '按约束执行最小化动作'},
            {'description': '记录产出并更新状态'}
        ],
        'tool_plan': NODE_TOOL_SUGGESTIONS.get(node_type, ['read_file']),
        'constraints': [
            '优先只读后写',
            '修改前确认目标路径',
            '异常时输出回退建议'
        ],
        'success_criteria': [
            '任务目标达成',
            '关键校验通过',
            '结果可追踪'
        ],
        'fallback': '若关键前置条件不足，先返回分析结论，不直接进行破坏性操作',
        'risk_flags': ['high'] if node_type in ('modify', 'verify') else ['low'],
        'require_runtime_approval': node_type in ('modify', 'verify')
    }


def build_detail_plans(master_plan: Dict[str, Any], selected_node_ids: List[str], goal: str = '') -> List[Dict[str, Any]]:
    """
    为选中节点生成细化执行思路（调用大模型）

    Args:
        master_plan: 主计划字典
        selected_node_ids: 选中的节点ID列表
        goal: 用户原始目标

    Returns:
        细化后的节点详情列表
    """
    nodes = master_plan.get('plan_nodes', []) if isinstance(master_plan, dict) else []
    selected = set(selected_node_ids or [])

    logger.info(f"[DetailPlan] 开始构建详细计划: 原始节点数={len(nodes)}, 选中={list(selected)}, goal={goal[:50] if goal else ''}...")

    # 获取原始目标
    if not goal and isinstance(master_plan, dict):
        goal = master_plan.get('goal', '')

    details: List[Dict[str, Any]] = []
    for node in nodes:
        node_id = node.get('id')
        if not node_id or (selected and node_id not in selected):
            continue

        logger.info(f"[DetailPlan] 处理节点: {node_id} - {node.get('title', '')}")
        detail = _call_llm_for_detail_plan(node, goal)
        details.append(detail)
        logger.info(f"[DetailPlan] 节点 {node_id} 完成")

    logger.info(f"[DetailPlan] 构建完成, 共 {len(details)} 个详细计划")
    return details
