"""Agent 输出标准化解析"""
from __future__ import annotations

import json
import re
from typing import Any, Dict, List


def _extract_json_block(text: str) -> Dict[str, Any]:
    if not text:
        return {}

    try:
        parsed = json.loads(text)
        if isinstance(parsed, dict):
            return parsed
    except Exception:
        pass

    match = re.search(r'```json\s*(\{[\s\S]*?\})\s*```', text, flags=re.IGNORECASE)
    if match:
        try:
            parsed = json.loads(match.group(1))
            if isinstance(parsed, dict):
                return parsed
        except Exception:
            return {}

    return {}


def parse_agent_result(raw_result: Any, task_context: Dict[str, Any], iterations: List[Dict[str, Any]] | None = None) -> Dict[str, Any]:
    """将 Agent 原始输出解析为统一任务结果"""
    current_task = task_context.get('current_task', {}) if isinstance(task_context, dict) else {}
    task_id = str(current_task.get('task_id') or '')

    if isinstance(raw_result, dict):
        result_obj = raw_result
    else:
        text = str(raw_result or '').strip()
        result_obj = _extract_json_block(text)
        if not result_obj:
            result_obj = {
                'task_id': task_id,
                'status': 'done',
                'result_summary': text[:500] if text else f'任务 {task_id} 已完成',
                'artifacts': {'raw_result': text},
            }

    status = str(result_obj.get('status') or 'done').strip().lower()
    if status not in {'done', 'failed', 'waiting_human'}:
        status = 'done'

    artifacts = result_obj.get('artifacts')
    if not isinstance(artifacts, dict):
        artifacts = {}

    if iterations:
        artifacts['agent_iterations'] = iterations

    return {
        'task_id': task_id,
        'status': status,
        'result_summary': str(result_obj.get('result_summary') or '').strip() or f'任务 {task_id} 执行完成',
        'artifacts': artifacts,
        'wait_reason': result_obj.get('wait_reason'),
        'pending_action': result_obj.get('pending_action'),
        'error_type': result_obj.get('error_type'),
        'error_message': result_obj.get('error_message'),
        'suggested_next_action': result_obj.get('suggested_next_action'),
    }
