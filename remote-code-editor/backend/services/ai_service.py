"""
AI服务模块
封装智谱AI调用逻辑，支持普通对话和 Agent 模式
"""
import os
import json
import asyncio
from typing import List, Dict, AsyncGenerator, Optional, Any
from zhipuai import ZhipuAI


class AIService:
    """AI服务类"""

    def __init__(self, api_key: str):
        """
        初始化AI服务

        Args:
            api_key: 智谱AI API密钥
        """
        self.api_key = api_key
        self._client = ZhipuAI(api_key=api_key)

        # 默认配置
        self.default_model = "glm-4.7-flash"
        self.max_tokens = 4096
        self.temperature = 0.7
        
        # 模型名称映射（前端名称 -> API名称）
        self.model_aliases = {
            'glm-4-flash': 'glm-4.7-flash',
            'glm-4v-flash': 'glm-4.6v-flash'  # 4.6 视觉模型
        }
        
        # Agent 系统提示词
        self.agent_system_prompt = """你是一个智能代码助手 Agent，可以帮助用户完成各种编程任务。

你可以使用以下工具来完成任务：
1. read_file - 读取文件内容
2. write_file - 创建或修改文件
3. list_directory - 列出目录内容
4. search_content - 在文件中搜索内容
5. execute_command - 执行终端命令
6. create_directory - 创建目录
7. delete_file - 删除文件或目录

工作原则：
1. 先理解用户需求，必要时先浏览项目结构
2. 执行操作前先确认文件存在
3. 修改文件前先读取原内容
4. 如果任务需要多步完成，逐步执行
5. 每次操作后向用户报告进度
6. 出错时给出清晰的错误说明和建议

请根据用户的需求，合理使用工具完成任务。"""

    async def chat_stream(
        self,
        messages: List[Dict],
        thinking_mode: bool = False
    ) -> AsyncGenerator[Dict, None]:
        """
        流式对话

        Args:
            messages: 对话历史 [{"role": "user/assistant", "content": "..."}]
            thinking_mode: 是否启用深度思考模式

        Yields:
            包含 reasoning_content 或 content 的字典
        """
        params = {
            "model": self.default_model,
            "messages": messages,
            "stream": True,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature
        }

        # 启用 thinking 参数（大多数模型支持）
        if thinking_mode:
            params["thinking"] = {"type": "enabled"}

        try:
            # 在线程池中运行同步的 SDK 调用，避免阻塞事件循环
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(None, lambda: self._client.chat.completions.create(**params))

            # 逐个 yield 流式数据
            for chunk in response:
                delta = chunk.choices[0].delta

                # 思考内容
                if delta.reasoning_content:
                    # 每次只发送新增的思考内容（而不是累积的完整内容）
                    yield {
                        "type": "reasoning",
                        "content": delta.reasoning_content
                    }
                    # 添加小延迟以实现真正的流式效果
                    await asyncio.sleep(0.01)

                # 回答内容
                if delta.content:
                    yield {
                        "type": "content",
                        "content": delta.content
                    }
                    # 添加小延迟以实现真正的流式效果
                    await asyncio.sleep(0.01)

        except Exception as e:
            print(f"[AI Service] 错误: {str(e)}")
            yield {"type": "error", "message": str(e)}
    
    async def chat_sync(
        self,
        messages: List[Dict],
        thinking_mode: bool = False
    ) -> str:
        """
        同步对话（非流式）
        
        Args:
            messages: 对话历史
            thinking_mode: 是否启用深度思考模式
        
        Returns:
            完整的回答内容
        """
        full_content = ""
        async for chunk in self.chat_stream(messages, thinking_mode):
            if chunk.get("type") == "content":
                full_content += chunk.get("content", "")
        return full_content
    
    async def agent_chat(
        self,
        messages: List[Dict],
        tools: List[Dict]
    ) -> AsyncGenerator[Dict, None]:
        """
        Agent 模式对话（支持 function calling）
        
        Args:
            messages: 对话历史
            tools: 可用工具列表
        
        Yields:
            包含 content、tool_calls 或 error 的字典
        """
        # 添加系统提示词
        agent_messages = [
            {"role": "system", "content": self.agent_system_prompt}
        ] + messages
        
        params = {
            "model": self.default_model,
            "messages": agent_messages,
            "tools": tools,
            "tool_choice": "auto",
            "stream": True,
            "max_tokens": self.max_tokens,
            "temperature": 0.3  # Agent 模式使用较低温度提高准确性
        }
        
        try:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None, 
                lambda: self._client.chat.completions.create(**params)
            )
            
            # 收集工具调用
            tool_calls_buffer = {}
            current_content = ""
            
            for chunk in response:
                delta = chunk.choices[0].delta
                finish_reason = chunk.choices[0].finish_reason
                
                # 处理文本内容
                if delta.content:
                    current_content += delta.content
                    yield {
                        "type": "content",
                        "content": delta.content
                    }
                    await asyncio.sleep(0.01)
                
                # 处理工具调用
                if delta.tool_calls:
                    for tool_call in delta.tool_calls:
                        idx = tool_call.index
                        
                        if idx not in tool_calls_buffer:
                            tool_calls_buffer[idx] = {
                                "id": tool_call.id or "",
                                "type": "function",
                                "function": {
                                    "name": "",
                                    "arguments": ""
                                }
                            }
                        
                        if tool_call.id:
                            tool_calls_buffer[idx]["id"] = tool_call.id
                        
                        if tool_call.function:
                            if tool_call.function.name:
                                tool_calls_buffer[idx]["function"]["name"] = tool_call.function.name
                            if tool_call.function.arguments:
                                tool_calls_buffer[idx]["function"]["arguments"] += tool_call.function.arguments
                
                # 处理完成
                if finish_reason == "tool_calls" and tool_calls_buffer:
                    # 返回工具调用
                    tool_calls_list = [tool_calls_buffer[i] for i in sorted(tool_calls_buffer.keys())]
                    yield {
                        "type": "tool_calls",
                        "tool_calls": tool_calls_list
                    }
                elif finish_reason == "stop":
                    yield {"type": "done"}
        
        except Exception as e:
            print(f"[AI Service] Agent 错误: {str(e)}")
            yield {"type": "error", "message": str(e)}
    
    async def agent_chat_with_tool_result(
        self,
        messages: List[Dict],
        tools: List[Dict],
        tool_call_id: str,
        tool_name: str,
        tool_result: str
    ) -> AsyncGenerator[Dict, None]:
        """
        带工具结果的 Agent 对话
        
        Args:
            messages: 对话历史（包含 assistant 的 tool_calls 消息）
            tools: 可用工具列表
            tool_call_id: 工具调用 ID
            tool_name: 工具名称
            tool_result: 工具执行结果
        
        Yields:
            AI 响应
        """
        # 添加工具结果消息
        messages_with_result = messages + [
            {
                "role": "tool",
                "content": tool_result,
                "tool_call_id": tool_call_id
            }
        ]
        
        async for chunk in self.agent_chat(messages_with_result, tools):
            yield chunk
    
    def set_model(self, model: str):
        """设置使用的模型"""
        # 使用映射表转换模型名称
        self.default_model = self.model_aliases.get(model, model)
    
    def set_parameters(self, max_tokens: int = None, temperature: float = None):
        """设置生成参数"""
        if max_tokens:
            self.max_tokens = max_tokens
        if temperature is not None:
            self.temperature = temperature
