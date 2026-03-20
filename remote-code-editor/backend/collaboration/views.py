"""Collaboration API 视图 - 交互式需求文档生成"""
from __future__ import annotations

import json
import logging
from typing import Any
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from collaboration.models import CollaborationSession, ChatMessage
from collaboration.services.interactive_planner_service import (
    get_interactive_planner_service,
    OptionsGenerationError,
    QuestionGenerationError,
)

logger = logging.getLogger('collaboration')


def _load_json_body(request):
    try:
        return json.loads(request.body or '{}'), None
    except json.JSONDecodeError:
        return None, JsonResponse({'error': '无效的JSON数据'}, status=400)


def _dump_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False)


# ============================================================
# 历史方案管理 API
# ============================================================

@csrf_exempt
@require_http_methods(["GET"])
def list_sessions_api(request):
    """列出所有会话"""
    sessions = CollaborationSession.objects.order_by('-updated_at')[:50]
    session_list = []
    for s in sessions:
        metadata = s.get_metadata()
        session_list.append({
            'session_id': str(s.id),
            'goal': s.goal,
            'status': s.status,
            'phase': s.phase,
            'created_at': s.created_at.isoformat() if s.created_at else None,
            'updated_at': s.updated_at.isoformat() if s.updated_at else None,
            'current_question_index': metadata.get('current_question_index', 0),
            'interactive_mode': metadata.get('interactive_mode', False),
        })
    return JsonResponse({
        'success': True,
        'sessions': session_list,
    })


@csrf_exempt
@require_http_methods(["GET"])
def get_session_detail_api(request):
    """获取会话详情"""
    session_id = request.GET.get('session_id')
    if not session_id:
        return JsonResponse({'error': '缺少 session_id'}, status=400)

    session = CollaborationSession.objects.filter(id=session_id).first()
    if session is None:
        return JsonResponse({'error': '会话不存在'}, status=404)

    metadata = session.get_metadata()

    return JsonResponse({
        'success': True,
        'session': {
            'session_id': str(session.id),
            'goal': session.goal,
            'status': session.status,
            'phase': session.phase,
            'workspace': session.workspace,
            'metadata': metadata,
            'created_at': session.created_at.isoformat() if session.created_at else None,
            'updated_at': session.updated_at.isoformat() if session.updated_at else None,
        },
    })


@csrf_exempt
@require_http_methods(["POST"])
def delete_session_api(request):
    """删除会话"""
    payload, err_response = _load_json_body(request)
    if err_response:
        return err_response

    session_id = payload.get('session_id')
    if not session_id:
        return JsonResponse({'error': '缺少 session_id'}, status=400)

    session = CollaborationSession.objects.filter(id=session_id).first()
    if session is None:
        return JsonResponse({'error': '会话不存在'}, status=404)

    session.delete()
    logger.info(f"[删除] 会话已删除: {session_id}")

    return JsonResponse({
        'success': True,
        'message': '会话已删除',
    })


# ============================================================
# 交互式需求文档生成 API
# ============================================================

@csrf_exempt
@require_http_methods(["POST"])
def interactive_start_api(request):
    """开始交互式需求文档生成

    用户输入目标，开始多轮问答
    """
    logger.info("[STEP] interactive_start_api 开始处理")
    payload, err_response = _load_json_body(request)
    if err_response:
        logger.error(f"[ERROR] JSON解析失败: {err_response}")
        return err_response

    goal = str(payload.get('goal') or '').strip()
    logger.info(f"[INPUT] goal={goal}")

    if not goal:
        logger.error("[ERROR] 缺少 goal")
        return JsonResponse({'error': '缺少 goal'}, status=400)

    # 创建会话
    session = CollaborationSession.objects.create(
        goal=goal,
        workspace=str(payload.get('workspace') or ''),
        phase='interactive_planning',
        status='in_progress',
        metadata=_dump_json({
            'interactive_mode': True,
            'current_question_index': 0,
            'answers': {},
            'completed_sections': [],
        }),
    )
    logger.info(f"[SAVE] Interactive Session创建成功: id={session.id}")

    # 获取第一个问题（由 LLM 生成选项）
    planner = get_interactive_planner_service()
    try:
        first_question = planner.get_question_with_options(0, goal, None)
    except OptionsGenerationError as e:
        logger.error(f"[InteractivePlanner] 生成选项失败: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': f'生成选项失败: {str(e)}',
            'session_id': str(session.id),
        }, status=500)

    logger.info(f"[完成] interactive_start 完成, session_id={session.id}")
    return JsonResponse({
        'success': True,
        'session_id': str(session.id),
        'goal': goal,
        'total_questions': planner.get_total_questions(),
        'current_question': first_question,
        'current_index': 0,
    })


@csrf_exempt
@require_http_methods(["GET"])
def interactive_question_api(request):
    """获取当前问题"""
    session_id = request.GET.get('session_id')
    if not session_id:
        return JsonResponse({'error': '缺少 session_id'}, status=400)

    session = CollaborationSession.objects.filter(id=session_id).first()
    if session is None:
        return JsonResponse({'error': '会话不存在'}, status=404)

    metadata = session.get_metadata()
    current_index = metadata.get('current_question_index', 0)
    answers = metadata.get('answers', {})

    planner = get_interactive_planner_service()
    try:
        question = planner.get_question_with_options(current_index, session.goal, answers)
    except (OptionsGenerationError, QuestionGenerationError) as e:
        logger.error(f"[InteractivePlanner] 生成问题失败: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': f'生成问题失败: {str(e)}',
            'session_id': str(session.id),
        }, status=500)

    if question is None:
        return JsonResponse({
            'success': True,
            'session_id': str(session.id),
            'completed': True,
            'message': '所有问题已回答完毕',
        })

    return JsonResponse({
        'success': True,
        'session_id': str(session.id),
        'current_index': current_index,
        'total_questions': -1,  # 动态模式
        'current_question': question,
        'progress': f"问题 {current_index + 1}",
    })


@csrf_exempt
@require_http_methods(["POST"])
def interactive_explain_api(request):
    """解释当前问题的含义"""
    payload, err_response = _load_json_body(request)
    if err_response:
        return err_response

    session_id = payload.get('session_id')
    question_text = payload.get('question_text', '')
    user_question = payload.get('user_question', '')

    if not session_id:
        return JsonResponse({'error': '缺少 session_id'}, status=400)
    if not question_text:
        return JsonResponse({'error': '缺少 question_text'}, status=400)

    session = CollaborationSession.objects.filter(id=session_id).first()
    if session is None:
        return JsonResponse({'error': '会话不存在'}, status=404)

    # 调用 AI 解释问题
    planner = get_interactive_planner_service()
    try:
        explanation = planner.explain_question(question_text, user_question)
    except Exception as e:
        logger.error(f"[InteractivePlanner] 解释问题失败: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': f'解释问题失败: {str(e)}',
        }, status=500)

    return JsonResponse({
        'success': True,
        'explanation': explanation,
    })


@csrf_exempt
@require_http_methods(["POST"])
def interactive_answer_api(request):
    """提交用户答案并获取下一题"""
    logger.info("[STEP] interactive_answer_api 开始处理")
    payload, err_response = _load_json_body(request)
    if err_response:
        logger.error(f"[ERROR] JSON解析失败: {err_response}")
        return err_response

    session_id = payload.get('session_id')
    selected_ids = payload.get('selected_ids', [])
    custom_input = payload.get('custom_input', '')

    if not session_id:
        return JsonResponse({'error': '缺少 session_id'}, status=400)

    session = CollaborationSession.objects.filter(id=session_id).first()
    if session is None:
        return JsonResponse({'error': '会话不存在'}, status=404)

    metadata = session.get_metadata()
    current_index = metadata.get('current_question_index', 0)
    answers = metadata.get('answers', {})

    # 获取当前问题并解析答案
    planner = get_interactive_planner_service()
    try:
        question = planner.get_question_with_options(current_index, session.goal, answers)
    except OptionsGenerationError as e:
        logger.error(f"[InteractivePlanner] 生成选项失败: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': f'生成选项失败: {str(e)}',
            'session_id': str(session.id),
        }, status=500)

    if question is None:
        return JsonResponse({'error': '问题不存在'}, status=400)

    # 保存答案（包含选项完整信息）
    parsed_answer = planner.parse_answer(
        question['question_id'],
        question['question'],  # 问题文本
        selected_ids,
        question.get('options', []),
        custom_input
    )

    # 保存问答消息到数据库
    msg_index = ChatMessage.objects.filter(session=session).count()
    ChatMessage.objects.create(
        session=session,
        message_type='question',
        question_id=question['question_id'],
        question_text=question['question'],
        question_options=json.dumps(question.get('options', []), ensure_ascii=False),
        index=msg_index,
    )
    ChatMessage.objects.create(
        session=session,
        message_type='answer',
        question_id=question['question_id'],
        question_text=question['question'],
        selected_option_ids=json.dumps(selected_ids, ensure_ascii=False),
        selected_options=json.dumps(parsed_answer.get('selected_options', []), ensure_ascii=False),
        custom_input=custom_input or '',
        index=msg_index + 1,
    )

    # 按 section_id 组织答案
    section_id = question['section_id']
    if section_id not in answers:
        answers[section_id] = []
    answers[section_id].append(parsed_answer)

    # 移动到下一题
    next_index = current_index + 1
    metadata['current_question_index'] = next_index
    metadata['answers'] = answers

    # 获取下一题（由 AI 动态生成）
    try:
        next_question = planner.get_question_with_options(next_index, session.goal, answers)
    except (OptionsGenerationError, QuestionGenerationError) as e:
        logger.error(f"[InteractivePlanner] 生成问题失败: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': f'生成问题失败: {str(e)}',
            'session_id': str(session.id),
        }, status=500)

    # 检查 AI 是否认为信息足够（直接生成文档）
    if next_question and next_question.get('is_final_doc'):
        # AI 认为信息足够，直接返回生成的文档
        metadata['status'] = 'completed'
        session.status = 'completed'
        session.phase = 'doc_generated'
        session.metadata = _dump_json(metadata)
        session.save(update_fields=['metadata', 'status', 'phase', 'updated_at'])

        logger.info(f"[完成] AI认为信息足够，生成文档, session_id={session.id}")

        return JsonResponse({
            'success': True,
            'session_id': str(session.id),
            'completed': True,
            'current_question': next_question,
        })

    session.metadata = _dump_json(metadata)
    session.save(update_fields=['metadata', 'updated_at'])

    logger.info(f"[完成] 答案已保存, session_id={session.id}, next_index={next_index}")

    return JsonResponse({
        'success': True,
        'session_id': str(session.id),
        'completed': False,
        'current_index': next_index,
        'total_questions': -1,  # 动态模式，不固定问题数
        'current_question': next_question,
        'progress': f"问题 {next_index + 1}",
    })


@csrf_exempt
@require_http_methods(["POST"])
def interactive_generate_api(request):
    """生成最终需求文档"""
    logger.info("[STEP] interactive_generate_api 开始处理")
    payload, err_response = _load_json_body(request)
    if err_response:
        logger.error(f"[ERROR] JSON解析失败: {err_response}")
        return err_response

    session_id = payload.get('session_id')

    if not session_id:
        return JsonResponse({'error': '缺少 session_id'}, status=400)

    session = CollaborationSession.objects.filter(id=session_id).first()
    if session is None:
        return JsonResponse({'error': '会话不存在'}, status=404)

    metadata = session.get_metadata()
    answers = metadata.get('answers', {})

    if not answers:
        return JsonResponse({'error': '尚未回答任何问题'}, status=400)

    # 构建需求文档提示词
    planner = get_interactive_planner_service()
    requirement_doc = planner.build_requirement_doc_prompt(session.goal, answers)

    # 更新会话状态
    session.phase = 'doc_generated'
    session.metadata = _dump_json({
        **metadata,
        'requirement_doc': requirement_doc,
    })
    session.save(update_fields=['metadata', 'phase', 'updated_at'])

    logger.info(f"[完成] 需求文档生成成功, session_id={session.id}")

    return JsonResponse({
        'success': True,
        'session_id': str(session.id),
        'requirement_doc': requirement_doc,
    })


@csrf_exempt
@require_http_methods(["GET"])
def interactive_state_api(request):
    """获取交互式会话状态"""
    session_id = request.GET.get('session_id')
    if not session_id:
        return JsonResponse({'error': '缺少 session_id'}, status=400)

    session = CollaborationSession.objects.filter(id=session_id).first()
    if session is None:
        return JsonResponse({'error': '会话不存在'}, status=404)

    metadata = session.get_metadata()
    current_index = metadata.get('current_question_index', 0)

    planner = get_interactive_planner_service()
    total = planner.get_total_questions()
    completed = current_index >= total

    return JsonResponse({
        'success': True,
        'session_id': str(session.id),
        'goal': session.goal,
        'current_index': current_index,
        'total_questions': total,
        'completed': completed,
        'progress': f"{min(current_index + 1, total)}/{total}",
        'status': session.status,
        'phase': session.phase,
    })


@csrf_exempt
@require_http_methods(["POST"])
def interactive_reset_api(request):
    """重置交互式会话"""
    payload, err_response = _load_json_body(request)
    if err_response:
        return err_response

    session_id = payload.get('session_id')
    if not session_id:
        return JsonResponse({'error': '缺少 session_id'}, status=400)

    session = CollaborationSession.objects.filter(id=session_id).first()
    if session is None:
        return JsonResponse({'error': '会话不存在'}, status=404)

    # 重置会话状态
    session.status = 'in_progress'
    session.phase = 'interactive_planning'
    session.metadata = _dump_json({
        'interactive_mode': True,
        'current_question_index': 0,
        'answers': {},
        'completed_sections': [],
    })
    session.save(update_fields=['metadata', 'status', 'phase', 'updated_at'])

    planner = get_interactive_planner_service()
    try:
        first_question = planner.get_question_with_options(0, session.goal, None)
    except OptionsGenerationError as e:
        logger.error(f"[InteractivePlanner] 生成选项失败: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': f'生成选项失败: {str(e)}',
            'session_id': str(session.id),
        }, status=500)

    return JsonResponse({
        'success': True,
        'session_id': str(session.id),
        'current_question': first_question,
        'current_index': 0,
        'total_questions': planner.get_total_questions(),
    })


@csrf_exempt
@require_http_methods(["POST"])
def interactive_skip_api(request):
    """跳过当前问题"""
    payload, err_response = _load_json_body(request)
    if err_response:
        return err_response

    session_id = payload.get('session_id')
    if not session_id:
        return JsonResponse({'error': '缺少 session_id'}, status=400)

    session = CollaborationSession.objects.filter(id=session_id).first()
    if session is None:
        return JsonResponse({'error': '会话不存在'}, status=404)

    metadata = session.get_metadata()
    current_index = metadata.get('current_question_index', 0)
    answers = metadata.get('answers', {})

    # 移动到下一题
    next_index = current_index + 1
    metadata['current_question_index'] = next_index
    session.metadata = _dump_json(metadata)
    session.save(update_fields=['metadata', 'updated_at'])

    planner = get_interactive_planner_service()

    # 检查是否完成
    if next_index >= planner.get_total_questions():
        return JsonResponse({
            'success': True,
            'session_id': str(session.id),
            'completed': True,
            'message': '所有问题已回答完毕',
        })

    # 获取下一题
    try:
        next_question = planner.get_question_with_options(next_index, session.goal, answers)
    except OptionsGenerationError as e:
        logger.error(f"[InteractivePlanner] 生成选项失败: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': f'生成选项失败: {str(e)}',
            'session_id': str(session.id),
        }, status=500)

    return JsonResponse({
        'success': True,
        'session_id': str(session.id),
        'completed': False,
        'current_index': next_index,
        'total_questions': planner.get_total_questions(),
        'current_question': next_question,
        'progress': f"问题 {next_index + 1}",
    })


@csrf_exempt
@require_http_methods(["GET"])
def interactive_messages_api(request):
    """获取会话的消息历史"""
    session_id = request.GET.get('session_id')
    if not session_id:
        return JsonResponse({'error': '缺少 session_id'}, status=400)

    session = CollaborationSession.objects.filter(id=session_id).first()
    if session is None:
        return JsonResponse({'error': '会话不存在'}, status=404)

    messages = ChatMessage.objects.filter(session=session).order_by('index')
    message_list = []
    for msg in messages:
        message_data = {
            'id': msg.id,
            'type': msg.message_type,
            'index': msg.index,
            'created_at': msg.created_at.isoformat() if msg.created_at else None,
        }
        if msg.message_type == 'question':
            message_data['question_id'] = msg.question_id
            message_data['question_text'] = msg.question_text
            message_data['options'] = msg.get_question_options()
        elif msg.message_type == 'answer':
            message_data['question_id'] = msg.question_id
            message_data['selected_ids'] = msg.get_selected_option_ids()
            message_data['selected_options'] = msg.get_selected_options()
            message_data['custom_input'] = msg.custom_input
        message_list.append(message_data)

    return JsonResponse({
        'success': True,
        'session_id': str(session.id),
        'messages': message_list,
    })