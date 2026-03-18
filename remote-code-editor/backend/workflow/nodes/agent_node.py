"""Agent 节点"""
import asyncio
import json
import logging
import time
from datetime import datetime
from typing import Any, Dict, List, Optional
from django.conf import settings

from services.ai_service import AIService
from services.agent_tools import AgentToolExecutor, get_tools_definition

logger = logging.getLogger('workflow')

# 全局服务实例
_ai_service = AIService(settings.ZHIPU_API_KEY)
_tool_executor = AgentToolExecutor(settings.WORKSPACE_PATH)


def agent_node(config: Dict[str, Any]):
    """
    Agent 节点执行器

    工具使用规则：
    1. 默认使用所有工具
    2. 如果用户指定了tools列表，只使用指定的工具
    3. 如果use_tools=False，则不使用工具
    """
    agent_name = config.get('name', 'general_agent')
    task = config.get('task', '')  # 任务描述
    tools_config = config.get('tools', None)  # 用户指定的工具列表，None表示使用所有工具
    use_tools = config.get('use_tools', True)  # 是否使用工具
    max_iterations = config.get('max_iterations', 5)  # 最大迭代次数

    logger.info("=" * 60)
    logger.info(f"[Agent Node] 初始化 | name={agent_name}, task={task[:50] if task else ''}..., use_tools={use_tools}, max_iterations={max_iterations}")
    logger.info("=" * 60)

    def run(state: Dict[str, Any]) -> Dict[str, Any]:
        node_start_time = time.time()

        workspace = state.get('workspace')
        # 如果workspace为空或空字符串，使用默认的settings.WORKSPACE_PATH
        if workspace:
            _tool_executor.set_workspace(workspace)
            logger.info(f"[Agent Node] 使用自定义工作区 | workspace={workspace}")
        else:
            # 使用默认工作区
            default_workspace = settings.WORKSPACE_PATH
            if default_workspace:
                _tool_executor.set_workspace(default_workspace)
                logger.info(f"[Agent Node] 使用默认工作区 | workspace={default_workspace}")
            else:
                logger.error(f"[Agent Node] 工作区未设置，工具调用可能失败")

        # 记录实际使用的工作区路径
        actual_workspace = str(_tool_executor.workspace) if _tool_executor.workspace else "未设置"
        logger.info(f"[Agent Node] 实际工作区路径 | path={actual_workspace}")

        # 构建消息
        messages = _build_messages(state, task)

        logger.info(f"[Agent Node] 开始执行 | workspace={workspace or '默认'}, messages_count={len(messages)}")

        if use_tools:
            # 工具模式：使用agent_tools
            # 如果指定了tools则使用指定的，否则使用所有工具
            workflow_id = state.get('_workflow_id')
            result_data = _run_agent_with_tools(
                messages=messages,
                tools_config=tools_config,  # None表示使用所有工具
                max_iterations=max_iterations,
                workflow_id=workflow_id
            )
            # 兼容旧返回格式（字符串）和新格式（字典）
            if isinstance(result_data, dict):
                state['result'] = result_data.get('result', '')
                state['iterations'] = result_data.get('iterations', [])
            else:
                state['result'] = result_data
                state['iterations'] = []
        else:
            # 普通模式：简单对话
            logger.info(f"[Agent Node] 使用简单对话模式")
            result = _run_simple_chat(messages)
            state['result'] = result
            state['iterations'] = []

        node_time = int((time.time() - node_start_time) * 1000)
        logger.info(f"[Agent Node] 执行完成 | result_length={len(str(state['result']))}, time={node_time}ms")

        return state

    return run


def _build_messages(state: Dict[str, Any], task: str = '') -> List[Dict[str, str]]:
    """构建消息列表"""
    if 'messages' in state and isinstance(state['messages'], list):
        return state['messages']
    
    user_input = state.get('prompt') or state.get('input') or ''
    
    if task:
        content = f"任务：{task}\n\n用户输入：{user_input}"
    else:
        content = str(user_input)
    
    return [{"role": "user", "content": content}]


def _run_simple_chat(messages: List[Dict[str, str]]) -> str:
    """简单对话模式"""
    return _ai_service.chat_sync(messages)


def _run_agent_with_tools(
    messages: List[Dict[str, str]],
    tools_config: Optional[List[str]] = None,
    max_iterations: int = 5,
    workflow_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    使用工具的Agent模式

    Args:
        messages: 消息历史
        tools_config: 工具配置列表，如 ["read_file", "write_file"]。None表示使用所有工具
        max_iterations: 最大工具调用次数
        workflow_id: 工作流ID，用于更新执行状态

    Returns:
        {
            'result': Agent最终响应,
            'iterations': 迭代历史列表
        }
    """
    # 根据配置获取工具定义
    all_tools = get_tools_definition('agent')

    if tools_config is not None and len(tools_config) > 0:
        # 用户指定了工具，只使用指定的工具
        selected_tools = [
            tool for tool in all_tools
            if tool['function']['name'] in tools_config
        ]
        tool_info = tools_config
    else:
        # 未指定工具，使用所有工具
        selected_tools = all_tools
        tool_info = [tool['function']['name'] for tool in all_tools]

    if not selected_tools:
        logger.warning("[Agent Node] 未选择任何工具，回退到普通模式")
        return {'result': _run_simple_chat(messages), 'iterations': []}

    logger.info(f"[Agent Node] 使用工具: {tool_info}, 最大迭代: {max_iterations}")

    # 转换为智谱AI格式
    zhipu_tools = _convert_to_zhipu_tools(selected_tools)

    # 迭代执行工具
    agent_messages = messages.copy()
    iteration = 0
    iterations_history = []  # 收集迭代历史

    logger.info(f"[Agent Node] 开始迭代执行 | max_iterations={max_iterations}")

    while iteration < max_iterations:
        iteration += 1
        iteration_start = time.time()
        logger.info(f"[Agent Node] ===== 迭代 {iteration}/{max_iterations} =====")

        # 发送迭代次数气泡
        if workflow_id:
            from ..cache import add_bubble_record
            add_bubble_record(workflow_id, {
                'type': 'iteration',
                'label': f'迭代 {iteration}/{max_iterations}',
                'content': f'开始第 {iteration} 次迭代，最多 {max_iterations} 次',
                'timestamp': datetime.now().isoformat()
            })

        # 更新执行状态 - 当前迭代次数
        if workflow_id:
            from ..cache import update_execution_details
            update_execution_details(workflow_id, {
                'current_iteration': iteration,
                'max_iterations': max_iterations,
                'status_message': f'正在执行第 {iteration}/{max_iterations} 次迭代'
            })

        # 调用AI
        logger.info(f"[Agent Node] 调用 AI 获取工具调用")
        
        # 更新状态 - 正在等待AI响应
        if workflow_id:
            from ..cache import update_execution_details
            update_execution_details(workflow_id, {
                'ai_status': 'waiting',
                'status_message': f'正在等待AI响应（第 {iteration} 次迭代）'
            })
        
        try:
            tool_calls, ai_content = _get_tool_calls(agent_messages, zhipu_tools)
            
            # 发送AI内容气泡
            if workflow_id and ai_content:
                from ..cache import add_bubble_record
                add_bubble_record(workflow_id, {
                    'type': 'ai_content',
                    'label': 'AI 思考',
                    'content': ai_content[:500] + ('...' if len(ai_content) > 500 else ''),
                    'timestamp': datetime.now().isoformat()
                })
            
            # 更新执行详情 - AI响应内容
            if workflow_id and ai_content:
                from ..cache import update_execution_details
                update_execution_details(workflow_id, {
                    'ai_content': ai_content[:500] + ('...' if len(ai_content) > 500 else ''),  # 限制长度
                    'ai_status': 'responded'
                })
        except Exception as e:
            logger.error(f"[Agent Node] AI调用失败: {e}")
            # 更新错误状态
            if workflow_id:
                from ..cache import update_execution_details
                update_execution_details(workflow_id, {
                    'ai_status': 'error',
                    'error': f'AI调用失败: {str(e)}',
                    'status_message': f'AI调用失败: {str(e)}'
                })
            raise

        if not tool_calls:
            # 没有更多工具调用，返回结果
            logger.info(f"[Agent Node] 无更多工具调用，结束迭代")
            break

        logger.info(f"[Agent Node] 收到 {len(tool_calls)} 个工具调用")

        # 执行工具并添加结果
        iteration_tools = []  # 本轮迭代工具调用记录
        for tool_call in tool_calls:
            tool_name = tool_call['name']
            tool_args = tool_call.get('arguments', {})
            # arguments 可能是字符串（JSON格式），需要解析为字典
            if isinstance(tool_args, str):
                try:
                    tool_args = json.loads(tool_args)
                except json.JSONDecodeError:
                    tool_args = {}
            tool_call_id = tool_call['id']

            logger.info(f"[Agent Node] 执行工具: {tool_name}")
            logger.debug(f"[Agent Node] 工具参数: {tool_args}")

            # 发送工具开始气泡
            if workflow_id:
                from ..cache import add_bubble_record
                args_summary = _generate_args_summary(tool_name, tool_args)
                add_bubble_record(workflow_id, {
                    'type': 'tool_start',
                    'tool_name': tool_name,
                    'label': f'执行: {tool_name}',
                    'content': args_summary or f'准备执行 {tool_name}',
                    'timestamp': datetime.now().isoformat()
                })

            # 更新状态 - 正在执行工具
            if workflow_id:
                from ..cache import update_execution_details
                update_execution_details(workflow_id, {
                    'current_tool': tool_name,
                    'status_message': f'正在执行工具: {tool_name}（第 {iteration} 次迭代）'
                })

            # 执行工具
            tool_start = time.time()
            try:
                tool_result = asyncio.run(
                    _tool_executor.execute_tool(tool_name, tool_args)
                )
                tool_result_str = json.dumps(tool_result, ensure_ascii=False)
                tool_success = True
                # 日志中只显示结果的前100个字符，避免日志过长
                logger.info(f"[Agent Node] 工具执行成功 | result_length={len(tool_result_str)}")

                # 更新执行详情 - 工具执行成功
                if workflow_id:
                    from ..cache import update_execution_details
                    update_execution_details(workflow_id, {
                        'current_tool': tool_name,
                        'tool_result': tool_result_str[:500] if len(tool_result_str) > 500 else tool_result_str,
                        'tool_success': True,
                        'status_message': f'工具 {tool_name} 执行成功'
                    })
            except Exception as e:
                tool_result_str = f"工具执行错误: {str(e)}"
                tool_success = False
                logger.error(f"[Agent Node] 工具执行错误: {e}")

                # 更新错误状态
                if workflow_id:
                    from ..cache import update_execution_details
                    update_execution_details(workflow_id, {
                        'current_tool': tool_name,
                        'tool_result': str(e),
                        'tool_success': False,
                        'status_message': f'工具 {tool_name} 执行失败: {str(e)}'
                    })

            tool_time = int((time.time() - tool_start) * 1000)

            # 记录工具调用
            iteration_tools.append({
                'name': tool_name,
                'args': tool_args,
                'result': tool_result_str[:2000] if len(tool_result_str) > 2000 else tool_result_str,  # 限制结果长度
                'success': tool_success,
                'time_ms': tool_time
            })

            # 发送工具结果气泡
            if workflow_id:
                from ..cache import add_bubble_record

                # 生成参数摘要
                args_summary = ''
                if tool_name == 'write_file':
                    args_summary = f"创建 {tool_args.get('file_path', '文件')}"
                elif tool_name == 'read_file':
                    args_summary = f"读取 {tool_args.get('file_path', '文件')}"
                elif tool_name == 'execute_command':
                    args_summary = f"执行: {tool_args.get('command', '')[:50]}"
                elif tool_name == 'list_directory':
                    args_summary = f"列出目录"
                elif tool_name == 'search_content':
                    args_summary = f"搜索: {tool_args.get('pattern', '')[:30]}"
                else:
                    args_summary = tool_name

                # 生成结果摘要
                result_summary = ''
                try:
                    result_data = json.loads(tool_result_str) if tool_result_str else {}
                    if result_data.get('success'):
                        result_summary = result_data.get('message', '执行成功')[:100]
                    else:
                        result_summary = result_data.get('error', '执行失败')[:100]
                except:
                    result_summary = tool_result_str[:100] if tool_result_str else ''

                bubble_record = {
                    'type': 'tool_result',
                    'tool_name': tool_name,
                    'label': f'{tool_name} 结果',
                    'execution_time_s': round(tool_time / 1000, 2),
                    'content': result_summary or '执行完成',
                    'arguments_summary': args_summary,
                    'success': tool_success,
                    'timestamp': datetime.now().isoformat()
                }
                add_bubble_record(workflow_id, bubble_record)

            # 添加工具结果到消息
            agent_messages.append({
                "role": "tool",
                "content": tool_result_str,
                "tool_call_id": tool_call_id
            })
            logger.info(f"[Agent Node] 工具结果已添加到消息历史 | tool={tool_name}, msg_count={len(agent_messages)}")

        # 记录本轮迭代
        iteration_time = int((time.time() - iteration_start) * 1000)
        iterations_history.append({
            'iteration': iteration,
            'tools': iteration_tools,
            'time_ms': iteration_time
        })

        # 本轮迭代工具执行汇总
        logger.info(f"[Agent Node] 本轮迭代完成 | tools_count={len(iteration_tools)}, msg_count={len(agent_messages)}, time={iteration_time}ms")

    # 最终响应
    logger.info(f"[Agent Node] 获取最终响应 | total_iterations={iteration}")
    final_response = _get_final_response(agent_messages)
    logger.info(f"[Agent Node] Agent执行完成 | final_response_length={len(final_response)}")

    # 发送结论气泡
    if workflow_id and final_response:
        from ..cache import add_bubble_record
        add_bubble_record(workflow_id, {
            'type': 'conclusion',
            'label': '执行结论',
            'content': final_response,
            'timestamp': datetime.now().isoformat()
        })

    # 生成气泡流记录
    bubble_records = _generate_bubble_records(iterations_history)

    return {
        'result': final_response,
        'iterations': iterations_history,
        'bubble_records': bubble_records
    }


def _generate_bubble_records(iterations_history: List[Dict]) -> List[Dict]:
    """从迭代历史中生成气泡流记录 - 与实时气泡格式一致"""
    bubble_records = []
    
    for iter_data in iterations_history:
        iteration_num = iter_data.get('iteration', 0)
        
        # 添加迭代气泡
        bubble_records.append({
            'type': 'iteration',
            'label': f'迭代 {iteration_num}',
            'content': f'第 {iteration_num} 次迭代',
            'timestamp': datetime.now().isoformat()
        })
        
        for tool in iter_data.get('tools', []):
            # 生成参数摘要
            args_summary = _generate_args_summary(
                tool['name'], 
                tool.get('args', {})
            )
            
            # 添加工具开始气泡
            bubble_records.append({
                'type': 'tool_start',
                'tool_name': tool['name'],
                'label': f'执行: {tool["name"]}',
                'content': args_summary or f'准备执行 {tool["name"]}',
                'timestamp': datetime.now().isoformat()
            })
            
            # 生成结果摘要
            result_summary = _generate_result_summary(
                tool['name'], 
                tool.get('result', ''), 
                tool.get('success', False)
            )
            
            # 添加工具结果气泡
            bubble_records.append({
                'type': 'tool_result',
                'tool_name': tool['name'],
                'label': f'{tool["name"]} 结果',
                'content': result_summary or '执行完成',
                'execution_time_s': round(tool.get('time_ms', 0) / 1000.0, 2),
                'arguments_summary': args_summary,
                'success': tool.get('success', False),
                'timestamp': datetime.now().isoformat()
            })
    
    return bubble_records


def _generate_result_summary(tool_name: str, result: str, success: bool) -> str:
    """生成工具执行结果摘要"""
    if not success:
        return f"执行失败: {result[:100]}" if len(result) > 100 else f"执行失败: {result}"
    
    try:
        # 尝试解析 JSON 结果
        if isinstance(result, str):
            result_data = json.loads(result) if result else {}
        else:
            result_data = result
        
        # 根据工具类型生成不同的摘要
        if tool_name == 'write_file':
            path = result_data.get('path', result_data.get('output', ''))
            if path:
                return f"已成功创建 `{path}` 文件！"
            return "文件写入成功"
        
        elif tool_name == 'read_file':
            content = result_data.get('content', '')
            length = len(content) if content else 0
            return f"已读取文件内容 ({length} 字符)"
        
        elif tool_name == 'list_directory':
            items = result_data.get('items', [])
            return f"找到 {len(items)} 个文件/目录"
        
        elif tool_name == 'search_content':
            matches = result_data.get('matches', [])
            return f"找到 {len(matches)} 个匹配项"
        
        elif tool_name == 'execute_command':
            output = result_data.get('output', '')
            if output:
                return output[:100] if len(output) > 100 else output
            return "命令执行成功"
        
        elif tool_name == 'create_directory':
            path = result_data.get('path', '')
            return f"已创建目录 `{path}`"
        
        elif tool_name == 'delete_file':
            path = result_data.get('path', '')
            return f"已删除 `{path}`"
        
        else:
            # 通用摘要
            message = result_data.get('message', result_data.get('output', ''))
            if message:
                return message[:100] if len(message) > 100 else message
            return "执行成功"
            
    except (json.JSONDecodeError, TypeError):
        # JSON 解析失败,直接返回原始结果的前100个字符
        return result[:100] if len(result) > 100 else result


def _generate_args_summary(tool_name: str, args: Dict) -> str:
    """生成工具参数摘要"""
    if not args:
        return ""
    
    if tool_name == 'write_file':
        path = args.get('path', '')
        if path:
            return f"创建 {path}"
        return ""
    
    elif tool_name == 'read_file':
        path = args.get('path', '')
        if path:
            return f"读取 {path}"
        return ""
    
    elif tool_name == 'list_directory':
        path = args.get('path', '')
        if path:
            return f"列出 {path}"
        return ""
    
    elif tool_name == 'search_content':
        query = args.get('query', '')
        if query:
            return f"搜索: {query[:50]}" if len(query) > 50 else f"搜索: {query}"
        return ""
    
    elif tool_name == 'execute_command':
        command = args.get('command', '')
        if command:
            return f"执行: {command[:50]}" if len(command) > 50 else f"执行: {command}"
        return ""
    
    elif tool_name == 'create_directory':
        path = args.get('path', '')
        if path:
            return f"创建目录 {path}"
        return ""
    
    elif tool_name == 'delete_file':
        path = args.get('path', '')
        if path:
            return f"删除 {path}"
        return ""
    
    return ""


def _convert_to_zhipu_tools(tools: List[Dict]) -> List[Dict]:
    """转换工具定义为智谱AI格式"""
    # AGENT_TOOLS 已经是智谱AI格式，直接返回
    return tools


def _get_tool_calls(messages: List[Dict], tools: List[Dict], max_retries: int = 2) -> tuple:
    """获取AI返回的工具调用，支持格式错误时重试
    
    Returns:
        tuple: (tool_calls, ai_content) - 工具调用列表和AI响应内容
    """
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    # 检查工具列表，如果为空则不使用工具
    if not tools:
        logger.warning("[Agent Node] 工具列表为空，回退到普通模式")
        return [], ""

    # 获取有效工具名称列表，用于验证
    valid_tool_names = {tool['function']['name'] for tool in tools}
    
    retry_count: int = 0
    
    while retry_count <= max_retries:
        if retry_count > 0:
            logger.warning(f"[Agent Node] 格式错误，尝试第 {retry_count} 次重试...")
            # 在重试时添加提示消息
            messages.append({
                "role": "user",
                "content": "上次返回的工具调用格式不正确，请严格按照工具定义格式返回，确保：1. 工具名称正确 2. 参数是有效的JSON 3. 所有必需参数都已提供"
            })
        
        tool_calls_buffer = []
        format_error: Optional[str] = None

        # 同步调用
        def sync_call():
            try:
                logger.info(f"[Agent Node] API请求: model={_ai_service.default_model}, msg_count={len(messages)}, tools_count={len(tools)}, retry={retry_count}")
                
                # 打印完整消息内容
                logger.info(f"[Agent Node] ========== 发送给AI的完整消息 ==========")
                for i, msg in enumerate(messages):
                    role = msg.get('role', 'unknown')
                    content = msg.get('content', '')
                    tool_calls = msg.get('tool_calls', [])
                    tool_call_id = msg.get('tool_call_id', '')
                    
                    # 打印消息角色和内容
                    content_preview = content[:500] if content else ''
                    logger.info(f"[Agent Node] 消息[{i}] role={role}")
                    if content:
                        logger.info(f"[Agent Node]   content: {content_preview}{'...' if len(content) > 500 else ''}")
                    if tool_calls:
                        logger.info(f"[Agent Node]   tool_calls: {[tc.get('function', {}).get('name', 'unknown') for tc in tool_calls]}")
                    if tool_call_id:
                        logger.info(f"[Agent Node]   tool_call_id: {tool_call_id}")
                logger.info(f"[Agent Node] ========== 消息结束 ==========")

                response = _ai_service._client.chat.completions.create(
                    model=_ai_service.default_model,
                    messages=messages,
                    tools=tools,
                    tool_choice="auto",
                    stream=False,
                    max_tokens=_ai_service.max_tokens,
                    temperature=0.3
                )
                return response
            except Exception as e:
                logger.error(f"[Agent Node] AI调用错误: {e}")
                return None
        
        response = loop.run_in_executor(None, sync_call)
        response = loop.run_until_complete(asyncio.coroutine(lambda: response)())
        
        if not response:
            logger.warning("[Agent Node] AI 返回空响应")
            retry_count += 1
            continue
        
        # 检查响应格式
        try:
            if not hasattr(response, 'choices') or not response.choices:
                format_error = "响应缺少 choices 字段"
                logger.warning(f"[Agent Node] 格式错误: {format_error}")
                retry_count += 1
                continue
            
            # 记录 AI 响应内容
            ai_content = response.choices[0].message.content or ""
            tool_calls_response = response.choices[0].message.tool_calls
            has_tool_calls = bool(tool_calls_response)
            logger.info(f"[Agent Node] AI响应 | has_tool_calls={has_tool_calls}, content_length={len(ai_content)}")
            if ai_content:
                logger.info(f"[Agent Node] AI响应内容: {ai_content[:500]}{'...' if len(ai_content) > 500 else ''}")
            
            # 如果没有工具调用，直接返回
            if not has_tool_calls or not tool_calls_response:
                logger.info(f"[Agent Node] AI未返回工具调用，添加文本响应到消息历史")
                agent_msg = {
                    "role": "assistant",
                    "content": ai_content
                }
                messages.append(agent_msg)
                return [], ai_content
            
            # 验证每个工具调用
            valid_tool_calls = []
            for tc in tool_calls_response:
                # 检查工具调用是否有必要的字段
                if not hasattr(tc, 'id') or not tc.id:
                    format_error = "工具调用缺少 id 字段"
                    break
                
                if not hasattr(tc, 'function') or not tc.function:
                    format_error = "工具调用缺少 function 字段"
                    break
                
                if not hasattr(tc.function, 'name') or not tc.function.name:
                    format_error = "工具调用缺少 name 字段"
                    break
                
                tool_name = tc.function.name
                
                # 检查工具名称是否有效
                if tool_name not in valid_tool_names:
                    format_error = f"未知的工具名称: {tool_name}"
                    break
                
                # 检查参数格式
                args = tc.function.arguments
                if args:
                    try:
                        # 尝试解析 JSON
                        if isinstance(args, str):
                            json.loads(args)
                    except json.JSONDecodeError as e:
                        format_error = f"工具 {tool_name} 的参数不是有效的 JSON: {str(e)}"
                        break
                
                valid_tool_calls.append(tc)
            
            # 如果有格式错误，重试
            if format_error:
                logger.warning(f"[Agent Node] 格式错误: {format_error}")
                retry_count += 1
                continue
            
            # 解析工具调用
            for tc in valid_tool_calls:
                tool_calls_buffer.append({
                    'id': tc.id,
                    'name': tc.function.name,
                    'arguments': tc.function.arguments
                })
            
            # 添加AI响应到消息历史（注意：需要包含 type 字段）
            agent_msg = {
                "role": "assistant",
                "content": ai_content,
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",  # 智谱AI要求必须有 type 字段
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments
                        }
                    }
                    for tc in valid_tool_calls
                ]
            }
            messages.append(agent_msg)
            
            return tool_calls_buffer, ai_content
            
        except Exception as e:
            logger.error(f"[Agent Node] 解析响应时发生错误: {e}")
            retry_count += 1
            continue
    
    # 达到最大重试次数仍然失败
    logger.error(f"[Agent Node] 达到最大重试次数 {max_retries}，无法获取有效格式")
    return [], ""


def _get_final_response(messages: List[Dict]) -> str:
    """获取最终响应"""
    for msg in reversed(messages):
        if msg.get('role') == 'assistant' and msg.get('content'):
            return msg.get('content', '')
    
    # 如果没有内容，尝试获取工具调用后的结果
    for msg in reversed(messages):
        if msg.get('role') == 'tool':
            return f"工具执行完成: {msg.get('content', '')}"
    
    return "Agent执行完成"
