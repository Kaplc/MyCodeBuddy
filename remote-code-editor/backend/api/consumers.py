"""
WebSocket消费者
处理AI对话的WebSocket连接，支持普通对话和 Agent 模式
"""
import json
import asyncio
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.conf import settings
from services.ai_service import AIService
from services.agent_tools import AgentToolExecutor, get_tools_definition


class AIChatConsumer(AsyncWebsocketConsumer):
    """AI对话WebSocket消费者"""
    
    # Agent 最大循环次数，防止无限循环
    MAX_AGENT_ITERATIONS = 10
    
    async def connect(self):
        """建立连接"""
        await self.accept()
        
        # 初始化AI服务
        if settings.ZHIPU_API_KEY:
            self.ai_service = AIService(settings.ZHIPU_API_KEY)
            self.tool_executor = AgentToolExecutor(settings.WORKSPACE_PATH)
        else:
            self.ai_service = None
            self.tool_executor = None
            await self.send(json.dumps({
                'type': 'error',
                'message': 'AI服务未配置，请设置ZHIPU_API_KEY环境变量'
            }))
            await self.close()
            return
        
        # 当前对话ID
        self.conversation_id = None
        
        print(f"WebSocket连接已建立")
    
    async def disconnect(self, close_code):
        """断开连接"""
        print(f"WebSocket连接已断开: {close_code}")
    
    async def receive(self, text_data):
        """接收消息"""
        try:
            data = json.loads(text_data)
        except json.JSONDecodeError:
            await self.send(json.dumps({
                'type': 'error',
                'message': '无效的JSON格式'
            }))
            return
        
        request_type = data.get('type')
        
        if request_type == 'chat':
            await self.handle_chat(data)
        elif request_type == 'ping':
            await self.send(json.dumps({'type': 'pong'}))
        else:
            await self.send(json.dumps({
                'type': 'error',
                'message': f'未知的请求类型: {request_type}'
            }))
    
    @database_sync_to_async
    def get_conversation_messages(self, conversation_id):
        """从数据库获取对话历史消息"""
        from api.models import Conversation
        try:
            conversation = Conversation.objects.get(id=conversation_id)
            return conversation.get_messages_for_api()
        except Conversation.DoesNotExist:
            return []
    
    @database_sync_to_async
    def save_message(self, conversation_id, role, content, reasoning='', tool_calls=None, tool_call_id='', tool_name=''):
        """保存消息到数据库"""
        from api.models import Conversation, Message
        try:
            conversation = Conversation.objects.get(id=conversation_id)
            # tool_calls 需要序列化为 JSON 字符串
            tool_calls_json = json.dumps(tool_calls) if tool_calls else ''
            message = Message.objects.create(
                conversation=conversation,
                role=role,
                content=content,
                reasoning=reasoning,
                tool_calls=tool_calls_json,
                tool_call_id=tool_call_id,
                tool_name=tool_name
            )
            
            # 如果是第一条用户消息且标题是默认的，自动更新标题
            if role == 'user' and conversation.title == '新对话':
                new_title = content[:30].strip()
                if len(content) > 30:
                    new_title += '...'
                conversation.title = new_title
            
            conversation.save()
            return str(message.id)
        except Conversation.DoesNotExist:
            return None
    
    @database_sync_to_async
    def update_conversation_model(self, conversation_id, model, mode):
        """更新对话的模型和模式"""
        from api.models import Conversation
        try:
            conversation = Conversation.objects.get(id=conversation_id)
            conversation.model = model
            conversation.mode = mode
            conversation.save()
        except Conversation.DoesNotExist:
            pass
    
    async def read_attached_files(self, file_paths):
        """读取附件文件内容"""
        import os
        
        if not file_paths:
            return ""
        
        file_contents_parts = ["以下是引用的文件内容：\n"]
        
        for file_path in file_paths:
            try:
                # 检查文件是否存在
                if not os.path.exists(file_path):
                    file_contents_parts.append(f"\n### 文件: {os.path.basename(file_path)}\n错误：文件不存在\n")
                    continue
                
                # 检查文件大小（限制为 100KB）
                file_size = os.path.getsize(file_path)
                if file_size > 100 * 1024:
                    file_contents_parts.append(f"\n### 文件: {os.path.basename(file_path)}\n错误：文件过大（超过 100KB），无法读取\n")
                    continue
                
                # 读取文件内容
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                # 添加文件内容
                file_contents_parts.append(f"\n### 文件: {os.path.basename(file_path)}\n```\n{content}\n```\n")
                
            except Exception as e:
                file_contents_parts.append(f"\n### 文件: {os.path.basename(file_path)}\n错误：{str(e)}\n")
        
        return "".join(file_contents_parts)
    
    async def handle_chat(self, data):
        """处理对话请求"""
        messages = data.get('messages', [])
        thinking_mode = data.get('thinking_mode', False)
        model = data.get('model', 'glm-4-flash')
        agent_mode = data.get('agent_mode', False)  # Agent 模式
        ai_mode = data.get('ai_mode', 'chat')       # AI 模式：'chat', 'ask', 'agent'
        workspace = data.get('workspace', '')       # 当前工作区路径
        conversation_id = data.get('conversation_id', '')  # 对话ID
        attached_files = data.get('attached_files', [])  # 附件文件路径列表
        
        # 设置使用的模型
        self.ai_service.set_model(model)
        
        # 如果是 Agent 或 Ask 模式，更新工作区
        if (agent_mode or ai_mode in ['ask', 'agent']) and workspace:
            self.tool_executor.set_workspace(workspace)
        
        # 如果提供了对话ID，从数据库加载历史消息
        if conversation_id:
            self.conversation_id = conversation_id
            # 更新对话的模型和模式
            await self.update_conversation_model(
                conversation_id, 
                model, 
                'agent' if agent_mode else 'chat'
            )
            
            # 如果前端没有提供历史消息，从数据库加载
            if not messages:
                messages = await self.get_conversation_messages(conversation_id)
        
        if not messages:
            await self.send(json.dumps({
                'type': 'error',
                'message': '消息列表不能为空'
            }))
            return
        
        # 处理文件引用：读取文件内容并添加到最后一条用户消息中
        if attached_files and len(attached_files) > 0:
            file_contents = await self.read_attached_files(attached_files)
            if file_contents:
                # 将文件内容添加到最后一条用户消息
                if messages and messages[-1].get('role') == 'user':
                    original_content = messages[-1]['content']
                    messages[-1]['content'] = f"{original_content}\n\n{file_contents}"
        
        # 获取最后一条用户消息用于保存
        last_user_message = None
        for msg in reversed(messages):
            if msg.get('role') == 'user':
                last_user_message = msg.get('content', '')
                break
        
        # 如果有对话ID，保存用户消息
        if conversation_id and last_user_message:
            await self.save_message(conversation_id, 'user', last_user_message)
        
        try:
            # 判断是否需要使用工具（Agent 模式或 Ask 模式）
            use_tools = agent_mode or ai_mode in ['ask', 'agent']
            
            if use_tools:
                # 检查工作区是否已设置
                if not self.tool_executor.workspace:
                    await self.send(json.dumps({
                        'type': 'error',
                        'message': '请先选择工作区后再使用 Agent/Ask 模式'
                    }))
                    return
                # Agent/Ask 模式：支持工具调用
                # 根据 ai_mode 决定可用的工具范围
                tool_mode = ai_mode if ai_mode in ['ask', 'agent'] else ('agent' if agent_mode else 'chat')
                await self.handle_agent_chat(messages, conversation_id, tool_mode)
            else:
                # 普通模式：流式对话
                full_response = ""
                full_reasoning = ""
                
                async for chunk in self.ai_service.chat_stream(messages, thinking_mode):
                    await self.send(json.dumps(chunk))
                    
                    # 收集完整响应
                    if chunk.get('type') == 'content':
                        full_response += chunk.get('content', '')
                    elif chunk.get('type') == 'reasoning':
                        full_reasoning += chunk.get('content', '')
                
                # 保存AI响应到数据库
                if conversation_id and full_response:
                    await self.save_message(
                        conversation_id, 
                        'assistant', 
                        full_response,
                        reasoning=full_reasoning
                    )
                
                # 发送完成信号
                await self.send(json.dumps({'type': 'done'}))
            
        except Exception as e:
            await self.send(json.dumps({
                'type': 'error',
                'message': f'AI请求失败: {str(e)}'
            }))
    
    async def handle_agent_chat(self, messages: list, conversation_id: str = '', mode: str = 'agent'):
        """
        处理 Agent/Ask 模式对话
        
        Args:
            messages: 对话历史
            conversation_id: 对话ID（用于保存消息）
            mode: 工具模式 ('agent' 或 'ask')
                - 'agent': 可以使用所有工具（包括写文件）
                - 'ask': 只能使用只读工具（read_file, list_directory, search_content）
        """
        # 根据模式获取可用的工具
        tools = get_tools_definition(mode)
        current_messages = messages.copy()
        iteration = 0
        
        while iteration < self.MAX_AGENT_ITERATIONS:
            iteration += 1
            
            # 先发送思考过程（使用 thinking 模式获取推理）
            if iteration == 1:
                # 第一轮：获取 AI 对任务的思考
                thinking_response = ""
                async for chunk in self.ai_service.chat_stream(messages, thinking_mode=True):
                    if chunk.get('type') == 'reasoning':
                        await self.send(json.dumps({
                            'type': 'reasoning',
                            'content': chunk['content']
                        }))
                    elif chunk.get('type') == 'content':
                        thinking_response += chunk.get('content', '')
                    elif chunk.get('type') == 'error':
                        await self.send(json.dumps(chunk))
                        return
            
            # 发送当前迭代信息
            await self.send(json.dumps({
                'type': 'agent_status',
                'status': 'thinking',
                'iteration': iteration
            }))
            
            # 收集本轮响应
            content_buffer = ""
            tool_calls = None
            
            async for chunk in self.ai_service.agent_chat(current_messages, tools):
                chunk_type = chunk.get('type')
                
                if chunk_type == 'content':
                    content_buffer += chunk.get('content', '')
                    await self.send(json.dumps(chunk))
                
                elif chunk_type == 'tool_calls':
                    tool_calls = chunk.get('tool_calls', [])
                
                elif chunk_type == 'done':
                    # AI 完成回答，没有工具调用
                    # 保存AI响应到数据库
                    if conversation_id and content_buffer:
                        await self.save_message(
                            conversation_id,
                            'assistant',
                            content_buffer
                        )
                    await self.send(json.dumps({'type': 'done'}))
                    return
                
                elif chunk_type == 'error':
                    await self.send(json.dumps(chunk))
                    return
            
            # 如果有工具调用，执行工具
            if tool_calls:
                # 添加 assistant 消息（包含工具调用）
                assistant_message = {
                    "role": "assistant",
                    "content": content_buffer or None,
                    "tool_calls": tool_calls
                }
                current_messages.append(assistant_message)
                
                # 保存带工具调用的assistant消息
                if conversation_id:
                    await self.save_message(
                        conversation_id,
                        'assistant',
                        content_buffer or '',
                        tool_calls=tool_calls
                    )
                
                # 执行每个工具调用
                for tool_call in tool_calls:
                    tool_id = tool_call.get('id', '')
                    func = tool_call.get('function', {})
                    tool_name = func.get('name', '')
                    
                    try:
                        arguments = json.loads(func.get('arguments', '{}'))
                    except json.JSONDecodeError:
                        arguments = {}
                    
                    # 通知前端正在执行工具
                    await self.send(json.dumps({
                        'type': 'tool_start',
                        'tool_name': tool_name,
                        'arguments': arguments
                    }))
                    
                    # 执行工具
                    result = await self.tool_executor.execute_tool(tool_name, arguments)
                    
                    # 通知前端工具执行结果
                    await self.send(json.dumps({
                        'type': 'tool_result',
                        'tool_name': tool_name,
                        'result': result
                    }))
                    
                    # 添加工具结果到消息
                    tool_result_content = json.dumps(result, ensure_ascii=False)
                    current_messages.append({
                        "role": "tool",
                        "content": tool_result_content,
                        "tool_call_id": tool_id
                    })
                    
                    # 保存工具结果消息
                    if conversation_id:
                        await self.save_message(
                            conversation_id,
                            'tool',
                            tool_result_content,
                            tool_call_id=tool_id,
                            tool_name=tool_name
                        )
            else:
                # 没有工具调用，结束循环
                # 保存最终响应
                if conversation_id and content_buffer:
                    await self.save_message(
                        conversation_id,
                        'assistant',
                        content_buffer
                    )
                await self.send(json.dumps({'type': 'done'}))
                return
        
        # 达到最大迭代次数
        await self.send(json.dumps({
            'type': 'warning',
            'message': f'Agent 达到最大迭代次数 ({self.MAX_AGENT_ITERATIONS})，已停止执行'
        }))
        await self.send(json.dumps({'type': 'done'}))
