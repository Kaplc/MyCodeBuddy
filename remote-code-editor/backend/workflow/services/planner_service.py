"""主方案生成服务"""
from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


# 调用大模型生成方案的提示词
PLAN_GENERATION_PROMPT = """你是一个智能任务规划助手。当用户提出需求时，你需要生成多个不同的执行方案供用户选择。

用户需求：{goal}

请根据上述需求，生成 {num_options} 个不同策略的执行方案。每个方案应该：
1. 有独特的执行策略和思路
2. 适合不同的工作方式或风险偏好
3. 包含具体的执行步骤

请以JSON格式返回，格式如下：
{{
  "options": [
    {{
      "option_id": "option-1",
      "strategy_name": "方案名称（如：渐进式实施、风险优先、快速迭代等）",
      "strategy_desc": "方案策略的简要描述",
      "approach": "执行思路说明",
      "total_estimated_time": "预计总时间（如：1-2小时）",
      "plan_nodes": [
        {{
          "id": "step-1",
          "title": "步骤标题",
          "type": "步骤类型（analysis/read/modify/checkpoint等）",
          "description": "步骤详细描述",
          "depends_on": [],
          "estimated_time": "10-20分钟"
        }}
      ],
      "success_criteria": ["成功标准1", "成功标准2"],
      "assumptions": ["假设条件1", "假设条件2"],
      "risks": ["风险1", "风险2"]
    }}
  ]
}}

要求：
- 生成 {num_options} 个不同策略的方案
- plan_nodes 应包含 3-7 个步骤
- 步骤之间有合理的依赖关系
- 类型可以是：analysis(分析)、read(读取)、modify(修改)、checkpoint(检查点)、deploy(部署)
- 返回纯JSON，不要有其他文字"""


def _call_ai_for_plan_generation(goal: str, num_options: int = 3) -> List[Dict[str, Any]]:
    """调用AI服务生成多个计划选项
    
    Args:
        goal: 用户需求目标
        num_options: 需要生成的选项数量
        
    Returns:
        计划选项列表
    """
    try:
        from config.ai_config import get_api_key, get_default_provider
        
        api_key = get_api_key(get_default_provider())
        if not api_key:
            logger.warning("[Planner] 未配置AI API Key，使用默认方案")
            return _generate_default_options(goal, num_options)
        
        from zhipuai import ZhipuAI
        client = ZhipuAI(api_key=api_key)
        
        prompt = PLAN_GENERATION_PROMPT.format(goal=goal, num_options=num_options)

        messages = [{"role": "user", "content": prompt}]
        logger.info(f"[Planner] 调用AI生成方案 | goal长度: {len(goal)}, num_options: {num_options}")
        logger.info(f"[Planner] 发送消息: {json.dumps(messages, ensure_ascii=False, indent=2)}")

        response = client.chat.completions.create(
            model="glm-4.7-flash",
            messages=messages,
            max_tokens=4096,
            temperature=0.7
        )
        
        content = response.choices[0].message.content.strip()
        
        # 尝试解析JSON
        if content.startswith('```json'):
            content = content[7:]
        if content.startswith('```'):
            content = content[3:]
        if content.endswith('```'):
            content = content[:-3]
        
        data = json.loads(content.strip())
        options = data.get('options', [])
        
        # 验证并补充每个选项
        for opt in options:
            if 'option_id' not in opt:
                opt['option_id'] = f"option-{options.index(opt) + 1}"
            # 确保goal字段存在
            opt['goal'] = goal
        
        logger.info(f"[Planner] AI生成方案成功 | 生成 {len(options)} 个选项")
        return options
        
    except Exception as e:
        logger.error(f"[Planner] AI生成方案失败: {str(e)}")
        return _generate_default_options(goal, num_options)


def _generate_default_options(goal: str, num_options: int = 3) -> List[Dict[str, Any]]:
    """生成默认方案选项（当AI调用失败时使用）
    
    Args:
        goal: 用户需求目标
        num_options: 需要生成的选项数量
        
    Returns:
        默认计划选项列表
    """
    goal_text = (goal or '').strip() or '完成用户指定任务'
    
    default_strategies = [
        {
            'strategy_id': 'sequential',
            'strategy_name': '渐进式实施',
            'strategy_desc': '按步骤顺序执行，适合简单直接的任务',
            'approach': '分阶段顺序推进，每阶段完成后进入下一阶段，确保每步都可验证',
        },
        {
            'strategy_id': 'parallel',
            'strategy_name': '快速分解执行',
            'strategy_desc': '识别可并行处理的部分，加速整体执行',
            'approach': '将任务分解为多个独立子任务，并行处理后汇总验证',
        },
        {
            'strategy_id': 'iterative',
            'strategy_name': '小步迭代',
            'strategy_desc': '小步快跑，持续验证，适合复杂不确定的任务',
            'approach': '分步实施，每步验证后进入下一步，允许回退和调整',
        },
    ]
    
    options = []
    selected = default_strategies[:num_options]
    
    for idx, strategy in enumerate(selected):
        plan_nodes = [
            {
                'id': f'{strategy["strategy_id"]}-1',
                'title': '理解需求与范围',
                'type': 'analysis',
                'description': f'确认需求边界、输入输出和风险点：{goal_text[:50]}',
                'depends_on': [],
                'estimated_time': '5-10分钟'
            },
            {
                'id': f'{strategy["strategy_id"]}-2',
                'title': '分析与设计',
                'type': 'read',
                'description': '查找相关代码、配置与依赖关系，设计实施方案',
                'depends_on': [f'{strategy["strategy_id"]}-1'],
                'estimated_time': '10-20分钟'
            },
            {
                'id': f'{strategy["strategy_id"]}-3',
                'title': '实施变更',
                'type': 'modify',
                'description': strategy['approach'],
                'depends_on': [f'{strategy["strategy_id"]}-2'],
                'estimated_time': '30-60分钟'
            },
            {
                'id': f'{strategy["strategy_id"]}-4',
                'title': '验证与测试',
                'type': 'checkpoint',
                'description': '验证变更结果，确保符合预期',
                'depends_on': [f'{strategy["strategy_id"]}-3'],
                'estimated_time': '10-20分钟'
            },
            {
                'id': f'{strategy["strategy_id"]}-final',
                'title': '汇总交付',
                'type': 'checkpoint',
                'description': '产出结果摘要、风险说明与后续建议',
                'depends_on': [f'{strategy["strategy_id"]}-4'],
                'estimated_time': '5-10分钟'
            },
        ]
        
        options.append({
            'option_id': f'option-{idx + 1}',
            'goal': goal_text,
            'strategy_id': strategy['strategy_id'],
            'strategy_name': strategy['strategy_name'],
            'strategy_desc': strategy['strategy_desc'],
            'approach': strategy['approach'],
            'total_estimated_time': '1-2小时',
            'plan_nodes': plan_nodes,
            'success_criteria': [
                '实现目标对应改动',
                '关键逻辑可运行',
                '结果可审计可追踪'
            ],
            'assumptions': [
                '工作区路径可访问',
                '相关依赖已存在或可安装'
            ],
            'risks': [
                '修改高风险文件可能导致回归',
                '外部命令执行存在环境差异'
            ],
        })
    
    return options


def generate_master_plan(goal: str, workflow_id: Optional[str] = None) -> Dict[str, Any]:
    """根据目标生成主方案（通用方案）"""
    goal_text = (goal or '').strip() or '完成用户指定任务'
    
    # 生成5个不同策略的方案，取第一个作为通用方案返回给前端显示
    options = _call_ai_for_plan_generation(goal_text, num_options=5)
    if options:
        plan = options[0]  # 取第一个方案作为通用方案
        plan['workflow_id'] = str(workflow_id) if workflow_id else None
        return plan
    
    # 降级：返回默认方案
    default_options = _generate_default_options(goal_text, num_options=5)
    plan = default_options[0]
    plan['workflow_id'] = str(workflow_id) if workflow_id else None
    return plan


def generate_multiple_plans(goal: str, workflow_id: Optional[str] = None, num_options: int = 3) -> List[Dict[str, Any]]:
    """根据目标生成多个不同策略的计划选项
    
    Args:
        goal: 用户需求目标
        workflow_id: 工作流ID（可选）
        num_options: 生成选项数量，默认3个
        
    Returns:
        包含多个计划选项的列表
    """
    goal_text = (goal or '').strip() or '完成用户指定任务'
    
    plans = _call_ai_for_plan_generation(goal_text, num_options)
    
    # 确保每个plan都有workflow_id
    for plan in plans:
        plan['workflow_id'] = str(workflow_id) if workflow_id else None
    
    return plans
