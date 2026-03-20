#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""修复views.py乱码问题"""

# 读取临时文件
with open('remote-code-editor/backend/workflow/views_temp.py', 'r', encoding='utf-8') as f:
    base_content = f.read()

# 添加必要的导入
imports_addition = '''
from .models import (
    Workflow,
    WorkflowState,
    WorkflowExecutionSession,
    WorkflowPlanSnapshot,
    WorkflowPlanNodeReview,
    WorkflowExecutionTask,
)
from .services.planner_service import generate_master_plan
from .services.detail_plan_service import build_detail_plans
from .services.review_service import save_node_reviews
from .services.execution_pack_service import build_execution_pack
from .services.task_pool_service import init_task_pool, serialize_task
from .services.scheduler_service import refresh_ready_tasks
from .services.intervention_service import apply_intervention
from .services.session_state_service import build_session_state
from .services.runtime_executor_service import execute_next_task
from .cache import (
    get_pending_human_commands,
    set_session_state_cache,
    set_task_pool_summary_cache,
)
'''

# 新增的API函数
new_functions = '''

def _load_json_body(request):
    try:
        return json.loads(request.body or '{}'), None
    except json.JSONDecodeError:
        return None, JsonResponse({'error': '无效的JSON数据'}, status=400)


def _dump_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False)


@csrf_exempt
@require_http_methods(["POST"])
def generate_plan_api(request):
    logger.info("[STEP] generate_plan_api 开始处理")
    payload, err_response = _load_json_body(request)
    if err_response:
        logger.error(f"[ERROR] JSON解析失败: {err_response}")
        return err_response

    goal = str(payload.get('goal') or '').strip()
    logger.info(f"[INPUT] goal={goal}")
    if not goal:
        logger.error("[ERROR] 缺少 goal")
        return JsonResponse({'error': '缺少 goal'}, status=400)

    workflow_id = payload.get('workflow_id')
    workspace = str(payload.get('workspace') or '')
    logger.info(f"[INPUT] workflow_id={workflow_id}, workspace={workspace}")

    workflow = None
    if workflow_id:
        workflow = Workflow.objects.filter(id=workflow_id).first()
        if workflow is None:
            logger.error(f"[ERROR] 工作流不存在: {workflow_id}")
            return JsonResponse({'error': '工作流不存在'}, status=404)

    logger.info("[STEP] 调用 generate_master_plan 生成主计划")
    master_plan = generate_master_plan(goal=goal, workflow_id=str(workflow_id) if workflow_id else None)
    logger.info(f"[DATA] 主计划生成成功 | 包含 {len(master_plan.get('plan_nodes', []))} 个节点")

    logger.info("[STEP] 创建 WorkflowExecutionSession")
    session = WorkflowExecutionSession.objects.create(
        workflow=workflow,
        goal=goal,
        workspace=workspace,
        phase='planning',
        status='draft',
    )
    session.set_master_plan(master_plan)
    session.save(update_fields=['master_plan', 'updated_at'])
    logger.info(f"[SAVE] Session创建成功: id={session.id}")

    logger.info("[STEP] 创建 WorkflowPlanSnapshot")
    WorkflowPlanSnapshot.objects.create(
        session=session,
        source='ai',
        version=1,
        content=_dump_json(master_plan),
    )

    logger.info(f"[完成] generate_plan 完成, session_id={session.id}, phase={session.phase}")
    return JsonResponse({
        'success': True,
        'session_id': str(session.id),
        'phase': session.phase,
        'master_plan': master_plan,
    })


@csrf_exempt
@require_http_methods(["POST"])
def refine_plan_api(request):
    logger.info("[STEP] refine_plan_api 开始处理")
    payload, err_response = _load_json_body(request)
    if err_response:
        logger.error(f"[ERROR] JSON解析失败: {err_response}")
        return err_response

    session_id = payload.get('session_id')
    selected_node_ids = payload.get('selected_node_ids') or []
    logger.info(f"[INPUT] session_id={session_id}, selected_node_ids={selected_node_ids}")

    if not session_id:
        logger.error("[ERROR] 缺少 session_id")
        return JsonResponse({'error': '缺少 session_id'}, status=400)

    session = WorkflowExecutionSession.objects.filter(id=session_id).first()
    if session is None:
        logger.error(f"[ERROR] 会话不存在: {session_id}")
        return JsonResponse({'error': '会话不存在'}, status=404)

    master_plan = session.get_master_plan()
    goal = master_plan.get('goal', '')
    logger.info(f"[DATA] master_plan包含 {len(master_plan.get('plan_nodes', []))} 个节点 | goal={goal}")

    logger.info(f"[STEP] 开始调用 build_detail_plans 为 {len(selected_node_ids)} 个节点生成详细计划")
    detail_nodes = build_detail_plans(master_plan, selected_node_ids, goal)
    logger.info(f"[DATA] 返回 {len(detail_nodes)} 个详细计划")

    logger.info("[STEP] 保存节点审核记录到数据库")
    for item in detail_nodes:
        logger.info(f"[SAVE] node_id={item['node_id']}, title={item.get('title', '')}")
        WorkflowPlanNodeReview.objects.update_or_create(
            session=session,
            node_id=item['node_id'],
            defaults={
                'node_title': item.get('title', ''),
                'detail_plan': _dump_json(item),
                'review_status': 'pending',
                'reviewed_detail_plan': _dump_json({}),
                'require_runtime_approval': bool(item.get('require_runtime_approval', False)),
            }
        )

    session.phase = 'refining'
    session.save(update_fields=['phase', 'updated_at'])
    logger.info(f"[完成] refine_plan 完成, phase={session.phase}")

    return JsonResponse({
        'success': True,
        'session_id': str(session.id),
        'phase': session.phase,
        'refined_nodes': detail_nodes,
    })


@csrf_exempt
@require_http_methods(["POST"])
def submit_plan_review_api(request):
    logger.info("[STEP] submit_plan_review_api 开始处理")
    payload, err_response = _load_json_body(request)
    if err_response:
        logger.error(f"[ERROR] JSON解析失败: {err_response}")
        return err_response

    session_id = payload.get('session_id')
    reviews = payload.get('reviews') or []
    logger.info(f"[INPUT] session_id={session_id}, reviews数量={len(reviews)}")

    if not session_id:
        logger.error("[ERROR] 缺少 session_id")
        return JsonResponse({'error': '缺少 session_id'}, status=400)

    session = WorkflowExecutionSession.objects.filter(id=session_id).first()
    if session is None:
        logger.error(f"[ERROR] 会话不存在: {session_id}")
        return JsonResponse({'error': '会话不存在'}, status=404)

    logger.info("[STEP] 调用 save_node_reviews 保存审核结果")
    saved_reviews = save_node_reviews(session, reviews)
    logger.info(f"[DATA] 保存了 {len(saved_reviews)} 个审核记录")

    session.phase = 'reviewed'
    session.status = 'ready_for_pack'
    session.save(update_fields=['phase', 'status', 'updated_at'])
    logger.info(f"[完成] 审核提交完成, phase={session.phase}, status={session.status}")

    return JsonResponse({
        'success': True,
        'session_id': str(session.id),
        'phase': session.phase,
        'status': session.status,
        'review_count': len(saved_reviews),
    })


@csrf_exempt
@require_http_methods(["POST"])
def build_execution_pack_api(request):
    logger.info("[STEP] build_execution_pack_api 开始处理")
    payload, err_response = _load_json_body(request)
    if err_response:
        logger.error(f"[ERROR] JSON解析失败: {err_response}")
        return err_response

    session_id = payload.get('session_id')
    logger.info(f"[INPUT] session_id={session_id}")

    if not session_id:
        logger.error("[ERROR] 缺少 session_id")
        return JsonResponse({'error': '缺少 session_id'}, status=400)

    session = WorkflowExecutionSession.objects.filter(id=session_id).first()
    if session is None:
        logger.error(f"[ERROR] 会话不存在: {session_id}")
        return JsonResponse({'error': '会话不存在'}, status=404)

    logger.info("[STEP] 调用 build_execution_pack 构建执行包")
    execution_pack = build_execution_pack(session)
    logger.info(f"[DATA] 执行包构建成功 | 包含 {len(execution_pack.get('tasks', []))} 个任务")

    session.set_execution_pack(execution_pack)
    session.phase = 'packed'
    session.status = 'ready_to_execute'
    session.save(update_fields=['execution_pack', 'phase', 'status', 'updated_at'])


    return JsonResponse({
        'success': True,
        'session_id': str(session.id),
        'phase': session.phase,
        'status': session.status,
        'execution_pack': execution_pack,
    })


@csrf_exempt
@require_http_methods(["POST"])
def start_execution_session_api(request):
    logger.info("[STEP] start_execution_session_api 开始处理")
    payload, err_response = _load_json_body(request)
    if err_response:
        logger.error(f"[ERROR] JSON解析失败: {err_response}")
        return err_response

    session_id = payload.get('session_id')
    logger.info(f"[INPUT] session_id={session_id}")

    if not session_id:
        logger.error("[ERROR] 缺少 session_id")
        return JsonResponse({'error': '缺少 session_id'}, status=400)

    session = WorkflowExecutionSession.objects.filter(id=session_id).first()
    if session is None:
        logger.error(f"[ERROR] 会话不存在: {session_id}")
        return JsonResponse({'error': '会话不存在'}, status=404)

    logger.info("[STEP] 获取执行包")
    execution_pack = session.get_execution_pack()
    if not execution_pack:
        logger.info("[STEP] 执行包为空，构建新的执行包")
        execution_pack = build_execution_pack(session)
        session.set_execution_pack(execution_pack)

    logger.info(f"[STEP] 初始化任务池, 任务数量={len(execution_pack.get('tasks', []))}")
    tasks = init_task_pool(session, execution_pack)
    logger.info(f"[DATA] 任务池初始化完成, 任务数量={len(tasks)}")

    session.phase = 'executing'
    session.status = 'executing'
    session.save(update_fields=['execution_pack', 'phase', 'status', 'updated_at'])

    logger.info("[STEP] 构建会话状态")
    state = build_session_state(session)
    set_session_state_cache(str(session.id), state)
    set_task_pool_summary_cache(str(session.id), state.get('task_pool_summary', {}))

    logger.info(f"[完成] 执行会话启动成功, session_id={session.id}, phase={session.phase}, 任务数量={len(tasks)}")
    return JsonResponse({
        'success': True,
        'session_id': str(session.id),
        'phase': session.phase,
        'status': session.status,
        'task_count': len(tasks),
        'state': state,
    })


@csrf_exempt
@require_http_methods(["GET"])
def get_execution_session_state_api(request):
    session_id = request.GET.get('session_id')
    if not session_id:
        return JsonResponse({'error': '缺少 session_id'}, status=400)

    session = WorkflowExecutionSession.objects.filter(id=session_id).first()
    if session is None:
        return JsonResponse({'error': '会话不存在'}, status=404)

    refresh_ready_tasks(session)
    state = build_session_state(session)
    pending_human_commands = get_pending_human_commands(str(session.id))
    set_session_state_cache(str(session.id), state)
    set_task_pool_summary_cache(str(session.id), state.get('task_pool_summary', {}))

    logger.info(f"[POLL] session_id={session_id}, tasks={len(state.get('task_pool_summary', {}))}, pending_human={len(pending_human_commands)}")
    return JsonResponse({'success': True, 'state': state, 'pending_human_commands': pending_human_commands})



@csrf_exempt
@require_http_methods(["GET"])
def list_execution_tasks_api(request):
    session_id = request.GET.get('session_id')
    if not session_id:
        return JsonResponse({'error': '缺少 session_id'}, status=400)

    session = WorkflowExecutionSession.objects.filter(id=session_id).first()
    if session is None:
        return JsonResponse({'error': '会话不存在'}, status=404)

    refresh_ready_tasks(session)
    tasks = [serialize_task(task) for task in session.tasks.order_by('priority', 'created_at')]
    pending_human_commands = get_pending_human_commands(str(session.id))

    return JsonResponse({
        'success': True,
        'session_id': str(session.id),
        'tasks': tasks,
        'pending_human_commands': pending_human_commands,
    })



@csrf_exempt
@require_http_methods(["POST"])
def execute_next_task_api(request):
    logger.info("[STEP] execute_next_task_api 开始处理")
    payload, err_response = _load_json_body(request)
    if err_response:
        logger.error(f"[ERROR] JSON解析失败: {err_response}")
        return err_response

    session_id = payload.get('session_id')
    task_id = payload.get('task_id')
    logger.info(f"[INPUT] session_id={session_id}, task_id={task_id}")

    if not session_id:
        logger.error("[ERROR] 缺少 session_id")
        return JsonResponse({'error': '缺少 session_id'}, status=400)

    session = WorkflowExecutionSession.objects.filter(id=session_id).first()
    if session is None:
        logger.error(f"[ERROR] 会话不存在: {session_id}")
        return JsonResponse({'error': '会话不存在'}, status=404)

    logger.info(f"[STEP] 执行任务 task_id={task_id}")
    execute_result = execute_next_task(session, task_id=task_id)
    logger.info(f"[DATA] 任务执行结果: status={execute_result.get('status') if execute_result else 'None'}")

    logger.info("[STEP] 刷新就绪任务")
    refresh_ready_tasks(session)
    state = build_session_state(session)
    pending_human_commands = get_pending_human_commands(str(session.id))
    set_session_state_cache(str(session.id), state)
    set_task_pool_summary_cache(str(session.id), state.get('task_pool_summary', {}))

    logger.info(f"[完成] 任务执行完成, pending_human_commands={len(pending_human_commands)}")
    return JsonResponse({
        'success': True,
        'session_id': str(session.id),
        'execute_result': execute_result,
        'state': state,
        'pending_human_commands': pending_human_commands,
    })


@csrf_exempt
@require_http_methods(["POST"])
def intervene_execution_task_api(request):
    logger.info("[STEP] intervene_execution_task_api 开始处理")
    payload, err_response = _load_json_body(request)
    if err_response:
        logger.error(f"[ERROR] JSON解析失败: {err_response}")
        return err_response

    session_id = payload.get('session_id')
    task_id = payload.get('task_id')
    action = str(payload.get('action') or '').strip()
    intervention_payload = payload.get('payload') or {}
    auto_execute_next = bool(payload.get('auto_execute_next', True))
    logger.info(f"[INPUT] session_id={session_id}, task_id={task_id}, action={action}")

    if not session_id or not action:
        logger.error("[ERROR] 缺少 session_id 或action")
        return JsonResponse({'error': '缺少 session_id 或action'}, status=400)

    session = WorkflowExecutionSession.objects.filter(id=session_id).first()
    if session is None:
        logger.error(f"[ERROR] 会话不存在: {session_id}")
        return JsonResponse({'error': '会话不存在'}, status=404)

    task = None
    if task_id:
        task = WorkflowExecutionTask.objects.filter(session=session, task_id=task_id).first()
        if task is None:
            logger.error(f"[ERROR] 任务不存在: {task_id}")
            return JsonResponse({'error': '任务不存在'}, status=404)

    logger.info(f"[STEP] 应用干预: action={action}")
    intervention = apply_intervention(
        session=session,
        action=action,
        payload=intervention_payload,
        task=task,
    )
    logger.info(f"[DATA] 干预已应用: intervention_id={intervention.id}")

    execute_result = None
    if auto_execute_next and action in {'continue', 'edit_and_continue', 'retry', 'insert_task'}:
        logger.info(f"[STEP] 自动执行下一任务")
        execute_result = execute_next_task(session)

    logger.info("[STEP] 刷新任务池状态")
    refresh_ready_tasks(session)
    state = build_session_state(session)
    pending_human_commands = get_pending_human_commands(str(session.id))
    set_session_state_cache(str(session.id), state)
    set_task_pool_summary_cache(str(session.id), state.get('task_pool_summary', {}))

    logger.info(f"[完成] 干预处理完成")
    return JsonResponse({
        'success': True,
        'session_id': str(session.id),
        'intervention_id': intervention.id,
        'execute_result': execute_result,
        'state': state,
        'pending_human_commands': pending_human_commands,
    })



@csrf_exempt
@require_http_methods(["GET"])
def get_current_execution_session_api(request):
    workflow_id = request.GET.get('workflow_id')

    queryset = WorkflowExecutionSession.objects.exclude(
        status__in=['terminated', 'finished', 'finished_with_errors']
    )
    if workflow_id:
        queryset = queryset.filter(workflow_id=workflow_id)

    session = queryset.order_by('-updated_at').first()
    if session is None:
        return JsonResponse({'success': True, 'session_id': None})

    return JsonResponse({
        'success': True,
        'session_id': str(session.id),
        'status': session.status,
        'phase': session.phase,
        'updated_at': session.updated_at.isoformat(),
    })


@csrf_exempt
@require_http_methods(["GET"])
def get_execution_session_detail_api(request):

    session_id = request.GET.get('session_id')
    if not session_id:
        return JsonResponse({'error': '缺少 session_id'}, status=400)

    session = WorkflowExecutionSession.objects.filter(id=session_id).first()
    if session is None:
        return JsonResponse({'error': '会话不存在'}, status=404)

    reviews = [
        {
            'node_id': review.node_id,
            'node_title': review.node_title,
            'review_status': review.review_status,
            'human_comments': review.get_human_comments(),
            'reviewed_detail_plan': review.get_reviewed_detail_plan(),
            'require_runtime_approval': review.require_runtime_approval,
            'updated_at': review.updated_at.isoformat(),
        }
        for review in session.node_reviews.order_by('created_at')
    ]

    tasks = [serialize_task(task) for task in session.tasks.order_by('priority', 'created_at')]

    state = build_session_state(session)
    pending_human_commands = get_pending_human_commands(str(session.id))
    set_session_state_cache(str(session.id), state)
    set_task_pool_summary_cache(str(session.id), state.get('task_pool_summary', {}))


    return JsonResponse({
        'success': True,
        'session': {
            'session_id': str(session.id),
            'workflow_id': str(session.workflow_id) if session.workflow_id else None,
            'goal': session.goal,
            'workspace': session.workspace,
            'phase': session.phase,
            'status': session.status,
            'master_plan': session.get_master_plan(),
            'execution_pack': session.get_execution_pack(),

            'latest_error': session.latest_error,
            'updated_at': session.updated_at.isoformat(),
            'created_at': session.created_at.isoformat(),
        },
        'reviews': reviews,
        'tasks': tasks,
        'state': state,
        'pending_human_commands': pending_human_commands,
    })


# ==================== 历史方案管理 ====================

def list_plan_sessions_api(request):
    """获取历史方案会话列表"""
    # 获取最近的协议执行会话列表
    sessions = WorkflowExecutionSession.objects.filter(
        status__in=['draft', 'completed', 'failed', 'cancelled']
    ).order_by('-updated_at')[:50]  # 最多返回50条

    session_list = []
    for session in sessions:
        master_plan = session.get_master_plan()
        # 提取主方案的摘要信息
        plan_summary = ''
        if master_plan:
            plan_nodes = master_plan.get('plan_nodes', [])
            if plan_nodes:
                # 取第一个节点的标题作为摘要
                plan_summary = plan_nodes[0].get('title', '')[:50]

        session_list.append({
            'session_id': str(session.id),
            'goal': session.goal[:100] if session.goal else '',  # 截断显示
            'phase': session.phase,
            'status': session.status,
            'plan_summary': plan_summary,
            'updated_at': session.updated_at.isoformat(),
            'created_at': session.created_at.isoformat(),
        })

    return JsonResponse({
        'success': True,
        'sessions': session_list
    })


@csrf_exempt
@require_http_methods(["POST"])
def delete_plan_session_api(request):
    """删除历史方案会话"""
    payload, err_response = _load_json_body(request)
    if err_response:
        return err_response

    session_id = payload.get('session_id')
    if not session_id:
        return JsonResponse({'error': '缺少 session_id'}, status=400)

    session = WorkflowExecutionSession.objects.filter(id=session_id).first()
    if session is None:
        return JsonResponse({'error': '会话不存在'}, status=404)

    session.delete()
    logger.info(f"[删除历史方案] session_id={session_id}")
    return JsonResponse({'success': True})

def get_plan_session_detail_api(request):
    """获取历史方案会话详情"""
    session_id = request.GET.get('session_id')
    if not session_id:
        return JsonResponse({'error': '缺少 session_id'}, status=400)

    session = WorkflowExecutionSession.objects.filter(id=session_id).first()
    if session is None:
        return JsonResponse({'error': '会话不存在'}, status=404)

    # 获取方案快照历史
    snapshots = [
        {
            'snapshot_id': str(s.id),
            'source': s.source,
            'version': s.version,
            'content': s.get_content(),
            'created_at': s.created_at.isoformat(),
        }
        for s in session.plan_snapshots.order_by('-version')
    ]

    # 获取节点审核记录
    reviews = [
        {
            'node_id': review.node_id,
            'node_title': review.node_title,
            'review_status': review.review_status,
            'detail_plan': review.get_detail_plan(),
            'reviewed_detail_plan': review.get_reviewed_detail_plan(),
            'human_comments': review.get_human_comments(),
            'require_runtime_approval': review.require_runtime_approval,
            'updated_at': review.updated_at.isoformat(),
        }
        for review in session.node_reviews.order_by('created_at')
    ]

    return JsonResponse({
        'success': True,
        'session': {
            'session_id': str(session.id),
            'workflow_id': str(session.workflow_id) if session.workflow_id else None,
            'goal': session.goal,
            'workspace': session.workspace,
            'phase': session.phase,
            'status': session.status,
            'master_plan': session.get_master_plan(),
            'execution_pack': session.get_execution_pack(),
            'metadata': session.get_metadata(),
            'latest_error': session.latest_error,
            'updated_at': session.updated_at.isoformat(),
            'created_at': session.created_at.isoformat(),
        },
        'snapshots': snapshots,
        'reviews': reviews,
    })
'''

# 组合最终内容
final_content = base_content + new_functions

# 替换imports部分（在第12行之后）
import_section = '''from .models import Workflow, WorkflowState'''
final_content = final_content.replace(import_section, imports_addition.strip())

# 写入修复后的文件
with open('remote-code-editor/backend/workflow/views.py', 'w', encoding='utf-8') as f:
    f.write(final_content)

print("views.py 修复完成！")
