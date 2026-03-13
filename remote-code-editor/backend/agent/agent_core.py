"""
Agent 核心基类
提供 LLM 调用的统一接口
"""
import os
import asyncio
from typing import List, Dict, Any, Optional, AsyncGenerator
from abc import ABC, abstractmethod


class AgentCore(ABC):
    """Agent 核心基类"""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "glm-4.7-flash"):
        """
        初始化 Agent
        
        Args:
            api_key: API 密钥
            model: 模型名称
        """
        self.api_key = api_key or os.environ.get("ZHIPU_API_KEY", "")
        self.model = model
        self._client = None
    
    def _get_client(self):
        """获取 AI 客户端（懒加载）"""
        if self._client is None:
            from zhipuai import ZhipuAI
            self._client = ZhipuAI(api_key=self.api_key)
        return self._client
    
    def llm(self, prompt: str, system_prompt: str = "", **kwargs) -> str:
        """
        同步调用 LLM
        
        Args:
            prompt: 用户提示
            system_prompt: 系统提示
            **kwargs: 额外参数
            
        Returns:
            LLM 响应
        """
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        client = self._get_client()
        response = client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=kwargs.get("max_tokens", 4096),
            temperature=kwargs.get("temperature", 0.3)
        )
        
        return response.choices[0].message.content
    
    async def llm_async(self, prompt: str, system_prompt: str = "", **kwargs) -> str:
        """异步调用 LLM"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: self.llm(prompt, system_prompt, **kwargs)
        )
    
    def llm_stream(self, prompt: str, system_prompt: str = "", **kwargs) -> AsyncGenerator[str, None]:
        """流式调用 LLM"""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        client = self._get_client()
        response = client.chat.completions.create(
            model=self.model,
            messages=messages,
            stream=True,
            max_tokens=kwargs.get("max_tokens", 4096),
            temperature=kwargs.get("temperature", 0.3)
        )
        
        for chunk in response:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
    
    @abstractmethod
    def run(self, task: str, **kwargs) -> Any:
        """
        执行任务
        
        Args:
            task: 任务描述
            **kwargs: 额外参数
            
        Returns:
            执行结果
        """
        pass
