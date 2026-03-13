"""Workflow API 视图"""
from __future__ import annotations

import json
import logging
from typing import Any
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.forms.models import model_to_dict
from django.db import transaction
from .models import Workflow, WorkflowState
from .validators import validate_workflow_graph
from .executor import run_workflow_by_id, run_workflow_by_graph
from .cache import clear_graph_cache
from services.agent_tools import get_tool_names, AGENT_TOOLS

logger = logging.getLogger('workflow')


@csrf_exempt
@require_http_methods(["GET"])
def list_workflows(request):
    # 支持通过 include_temp 参数控制是否包含临时工作流
    include_temp = request.GET.get('include_temp', 'false').lower() == 'true'
    if include_temp:
        workflows = Workflow.objects.all()
    else:
        workflows = Workflow.objects.filter(is_temp=False)
    data = [
        {
            'id': str(wf.id),
            'name': wf.name,
            'version': wf.version,
            'is_temp': wf.is_temp,
            'updated_at': wf.updated_at.isoformat(),
        }
        for wf in workflows
    ]
    return JsonResponse({'workflows': data})


@csrf_exempt
@require_http_methods(["POST"])
def create_workflow(request):
    try:
        payload = json.loads(request.body or '{}')
    except json.JSONDecodeError:
        return JsonResponse({'error': '无效的JSON数据'}, status=400)

    name = str(payload.get('name') or '新工作流')
    graph = payload.get('graph') or {
        'nodes': [{
            'id': '1',
            'type': 'input',
            'config': {'key': 'input'}
        }],
        'edges': []
    }
    is_temp = payload.get('is_temp', False)  # 是否为临时工作流

    ok, err = validate_workflow_graph(graph)
    if not ok:
        return JsonResponse({'error': err}, status=400)

    # 如果是临时工作流，检查是否已存在同名临时工作流
    if is_temp:
        existing_temp = Workflow.objects.filter(name=name, is_temp=True).first()
        if existing_temp:
            # 更新并返回已有的临时工作流（需要将dict序列化为JSON字符串）
            existing_temp.graph = json.dumps(graph, ensure_ascii=False)
            existing_temp.version += 1
            existing_temp.save(update_fields=['graph', 'version', 'updated_at'])
            clear_graph_cache(str(existing_temp.id))
            # 将 graph 解析为 Python 对象再序列化，确保返回标准 JSON
            graph_data = existing_temp.get_graph()
            return JsonResponse({'workflow': {
                'id': str(existing_temp.id),
                'name': existing_temp.name,
                'version': existing_temp.version,
                'graph': graph_data,
                'is_temp': existing_temp.is_temp,
            }})

    # 检查是否存在同名非临时工作流
    existing_workflow = Workflow.objects.filter(name=name, is_temp=False).first()
    if existing_workflow:
        return JsonResponse({
            'error': f'已存在同名工作流: {name}',
            'existing_id': str(existing_workflow.id),
            'existing_version': existing_workflow.version,
        }, status=409)

    # 将 graph 对象序列化为 JSON 字符串存储
    workflow = Workflow.objects.create(name=name, graph=json.dumps(graph, ensure_ascii=False), is_temp=is_temp)
    # 将 graph 解析为 Python 对象再序列化，确保返回标准 JSON
    graph_data = workflow.get_graph()
    logger.info(f"[Workflow] create 返回的 graph_data: {graph_data}")
    return JsonResponse({'workflow': {
        'id': str(workflow.id),
        'name': workflow.name,
        'version': workflow.version,
        'graph': graph_data,
        'is_temp': workflow.is_temp,
    }})


@csrf_exempt
@require_http_methods(["GET"])
def get_workflow(request):
    workflow_id = request.GET.get('id')
    if not workflow_id:
        return JsonResponse({'error': '缺少 workflow id'}, status=400)

    try:
        workflow = Workflow.objects.get(id=workflow_id)
    except Workflow.DoesNotExist:
        return JsonResponse({'error': '工作流不存在'}, status=404)

    # 将 graph 解析为 Python 对象再序列化，确保返回标准 JSON
    graph_data = workflow.get_graph()
    return JsonResponse({'workflow': {
        'id': str(workflow.id),
        'name': workflow.name,
        'version': workflow.version,
        'graph': graph_data,
        'updated_at': workflow.updated_at.isoformat(),
    }})


@csrf_exempt
@require_http_methods(["POST"])
def update_workflow(request):
    # 添加入口日志
    logger.info(f"[Workflow] update_workflow 被调用 | body长度: {len(request.body)}")
    print(f"[DEBUG] update_workflow called, body: {request.body}")
    try:
        payload = json.loads(request.body or '{}')
    except json.JSONDecodeError:
        logger.error(f"[Workflow] JSON解析失败 | body: {request.body}")
        return JsonResponse({'error': '无效的JSON数据'}, status=400)

    workflow_id = payload.get('id')
    logger.info(f"[Workflow] 收到保存请求 | id={workflow_id}, keys={list(payload.keys())}")
    if not workflow_id:
        logger.warning("[Workflow] 缺少 workflow id")
        return JsonResponse({'error': '缺少 workflow id'}, status=400)

    try:
        workflow = Workflow.objects.get(id=workflow_id)
    except Workflow.DoesNotExist:
        logger.warning(f"[Workflow] 工作流不存在: {workflow_id}")
        return JsonResponse({'error': '工作流不存在'}, status=404)

    graph = payload.get('graph')
    if graph is None:
        logger.warning("[Workflow] 缺少 graph")
        return JsonResponse({'error': '缺少 graph'}, status=400)

    # 调试日志：显示 graph 的 nodes 和 edges 数量
    nodes_count = len(graph.get('nodes', []))
    edges_count = len(graph.get('edges', []))
    logger.info(f"[Workflow] 收到 graph | nodes: {nodes_count}, edges: {edges_count}")
    if edges_count > 0:
        logger.info(f"[Workflow] edges 内容: {graph.get('edges')}")

    ok, err = validate_workflow_graph(graph)
    if not ok:
        logger.warning(f"[Workflow] 图验证失败: {err}")
        return JsonResponse({'error': err}, status=400)

    name = payload.get('name')
    # 添加保存工作流的日志
    logger.info(f"[Workflow] 保存工作流: id={workflow_id}, name={name or workflow.name}, version={workflow.version + 1}")
    with transaction.atomic():
        if name:
            workflow.name = str(name)
        # 将 graph 对象序列化为 JSON 字符串存储
        workflow.graph = json.dumps(graph, ensure_ascii=False)
        workflow.version += 1
        workflow.save(update_fields=['name', 'graph', 'version', 'updated_at'])

    clear_graph_cache(str(workflow.id))
    # 将 graph 解析为 Python 对象再序列化，确保返回标准 JSON
    graph_data = workflow.get_graph()

    return JsonResponse({'workflow': {
        'id': str(workflow.id),
        'name': workflow.name,
        'version': workflow.version,
        'graph': graph_data,
    }})


@csrf_exempt
@require_http_methods(["POST"])
def delete_workflow(request):
    try:
        payload = json.loads(request.body or '{}')
    except json.JSONDecodeError:
        return JsonResponse({'error': '无效的JSON数据'}, status=400)

    workflow_id = payload.get('id')
    if not workflow_id:
        return JsonResponse({'error': '缺少 workflow id'}, status=400)

    try:
        workflow = Workflow.objects.get(id=workflow_id)
    except Workflow.DoesNotExist:
        return JsonResponse({'error': '工作流不存在'}, status=404)

    # 记录删除前的日志
    logger.info(f"[Workflow] 删除工作流 | id: {workflow_id}, name: {workflow.name}")

    workflow.delete()
    clear_graph_cache(str(workflow_id))

    # 如果删除的是上次打开的工作流，清理记录
    last_id = WorkflowState.get_last_workflow_id()
    if last_id and str(last_id) == str(workflow_id):
        WorkflowState.clear_last_workflow_id()
        logger.info(f"[Workflow] 删除工作流时清理上次记录 | id: {workflow_id}")

    return JsonResponse({'success': True})


@csrf_exempt
@require_http_methods(["POST"])
def run_workflow(request):
    """执行工作流

    请求格式 (v2.0):
    {
        "workflow_id": "可选，工作流ID",
        "graph": "可选，直接传递的图数据",
        "input": "输入数据",
        "workspace": "工作区路径",
        "execution_context": {  // 执行上下文（可选）
            "user_id": "用户ID",
            "session_id": "会话ID",
            "metadata": {}  // 额外元数据
        }
    }

    返回格式:
    {
        "success": true,
        "result": {},
        "execution_info": {
            "version": "2.0",
            "node_count": 5,
            "edge_count": 4,
            "execution_time": 1234
        }
    }
    """
    import time
    start_time = time.time()

    try:
        payload = json.loads(request.body or '{}')
    except json.JSONDecodeError:
        return JsonResponse({'error': '无效的JSON数据', 'success': False}, status=400)

    workflow_id = payload.get('workflow_id')
    graph = payload.get('graph')
    input_data = payload.get('input')
    workspace = payload.get('workspace', '')
    execution_context = payload.get('execution_context', {})

    if not workflow_id and not graph:
        return JsonResponse({'error': '缺少 workflow_id 或 graph', 'success': False}, status=400)

    # 记录执行请求
    logger.info(f"[Workflow] 执行工作流: workflow_id={workflow_id}, workspace={workspace}, input_type={type(input_data).__name__}")

    try:
        if workflow_id:
            result = run_workflow_by_id(str(workflow_id), input_data, workspace)
            # 获取图信息
            from .models import Workflow
            try:
                wf = Workflow.objects.get(id=workflow_id)
                graph_info = wf.graph if isinstance(wf.graph, dict) else json.loads(wf.graph or '{}')
            except:
                graph_info = {}
        else:
            ok, err = validate_workflow_graph(graph)
            if not ok:
                return JsonResponse({'error': err, 'success': False}, status=400)
            result = run_workflow_by_graph(graph, input_data, workspace)
            graph_info = graph

        # 计算执行时间
        execution_time = int((time.time() - start_time) * 1000)

        # 提取执行信息
        node_count = len(graph_info.get('nodes', []))
        edge_count = len(graph_info.get('edges', []))

        response = {
            'success': True,
            'result': result,
            'execution_info': {
                'version': graph_info.get('version', '1.0'),
                'node_count': node_count,
                'edge_count': edge_count,
                'execution_time_ms': execution_time,
                'workspace': workspace,
                'executed_at': time.strftime('%Y-%m-%d %H:%M:%S')
            }
        }

        logger.info(f"[Workflow] 执行完成: nodes={node_count}, edges={edge_count}, time={execution_time}ms")
        return JsonResponse(response)
    except Exception as e:
        import traceback
        error_msg = str(e)
        error_trace = traceback.format_exc()
        logger.error(f"[Workflow] 执行失败: {error_msg}\n{error_trace}")
        return JsonResponse({
            'error': error_msg,
            'success': False,
            'execution_info': {
                'execution_time_ms': int((time.time() - start_time) * 1000)
            }
        }, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def get_last_workflow(request):
    """获取上次打开的工作流ID"""
    last_id = WorkflowState.get_last_workflow_id()
    logger.info(f"[Workflow] 获取上次工作流ID: {last_id}")
    return JsonResponse({'last_workflow_id': last_id})


@csrf_exempt
@require_http_methods(["POST"])
def set_last_workflow(request):
    """设置上次打开的工作流ID"""
    try:
        payload = json.loads(request.body or '{}')
    except json.JSONDecodeError:
        return JsonResponse({'error': '无效的JSON数据'}, status=400)

    workflow_id = payload.get('workflow_id')
    if workflow_id:
        WorkflowState.set_last_workflow_id(workflow_id)
        logger.info(f"[Workflow] 设置上次工作流ID: {workflow_id}")
        return JsonResponse({'success': True, 'last_workflow_id': workflow_id})
    else:
        WorkflowState.clear_last_workflow_id()
        logger.info(f"[Workflow] 清除上次工作流ID")
        return JsonResponse({'success': True, 'last_workflow_id': None})


@csrf_exempt
@require_http_methods(["POST"])
def clear_last_workflow(request):
    """清除上次打开的工作流ID"""
    WorkflowState.clear_last_workflow_id()
    logger.info(f"[Workflow] 清除上次工作流ID")
    return JsonResponse({'success': True})


@csrf_exempt
@require_http_methods(["GET"])
def list_workflow_tools(request):
    """获取工作流可用的工具列表"""
    mode = request.GET.get('mode', 'agent')
    tools = get_tool_names(mode)
    # 工具中文解释映射
    tool_descriptions_cn = {
        'read_file': '读取指定文件的内容，查看代码或配置文件',
        'write_file': '创建新文件或修改现有文件的内容',
        'list_directory': '列出目录下的文件和子目录结构',
        'search_content': '在工作区文件中搜索指定文本或正则表达式',
        'execute_command': '执行终端命令，如运行脚本、安装依赖等',
        'create_directory': '创建新的目录',
        'delete_file': '删除指定文件或目录',
        'generate_tests': '为代码自动生成单元测试用例',
        'run_tests': '运行项目测试套件验证代码',
        'search_symbol': '搜索代码中的函数、类、变量等符号定义',
        'get_code_references': '查找符号在代码中的所有引用位置',
        'run_verification_pipeline': '运行完整代码验证流水线（语法、静态分析、测试）',
        'index_workspace': '索引工作区代码，建立代码搜索索引',
        'get_call_graph': '获取函数的调用关系图（调用链）',
        'get_file_outline': '获取文件的结构大纲（类、函数、导入等）',
        'verify_with_z3': '使用Z3求解器进行形式化验证',
    }
    # 获取工具详情
    tool_details = []
    for tool in AGENT_TOOLS:
        if tool['function']['name'] in tools:
            tool_name = tool['function']['name']
            tool_details.append({
                'name': tool_name,
                'description': tool['function']['description'],
                'description_cn': tool_descriptions_cn.get(tool_name, ''),
                'outputs': tool.get('outputs', 1),  # 默认1个输出
            })
    return JsonResponse({'tools': tool_details})


@csrf_exempt
@require_http_methods(["GET"])
def list_models(request):
    """获取可用的AI模型列表（从外部配置文件读取）"""
    from config.ai_config import get_models
    models = get_models()
    return JsonResponse({'models': models})


@csrf_exempt
@require_http_methods(["POST"])
def reload_ai_config(request):
    """重新加载 AI 配置文件"""
    from config.ai_config import reload_config
    try:
        config = reload_config()
        return JsonResponse({
            'success': True,
            'message': '配置已重新加载',
            'models_count': len(config.get('models', []))
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def debug_log(request):
    """调试日志接口"""
    try:
        payload = json.loads(request.body or '{}')
    except json.JSONDecodeError:
        return JsonResponse({'error': '无效的JSON数据'}, status=400)
    
    message = payload.get('message', '')
    logger.info(f"[DEBUG-FRONTEND] {message}")
    logger.info(f"[DEBUG-FRONTEND] payload: {payload}")
    return JsonResponse({'success': True})
