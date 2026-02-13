"""
AI服务单元测试
"""
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from services.ai_service import AIService


class TestAIService:
    """AI服务测试类"""
    
    def test_init(self):
        """测试初始化"""
        service = AIService("test_api_key")
        assert service.api_key == "test_api_key"
        assert service.default_model == "glm-4.7-flash"
    
    def test_set_model(self):
        """测试设置模型"""
        service = AIService("test_api_key")
        service.set_model("glm-4.6v-flash")
        assert service.default_model == "glm-4.6v-flash"
    
    def test_set_parameters(self):
        """测试设置参数"""
        service = AIService("test_api_key")
        service.set_parameters(max_tokens=2048, temperature=0.5)
        assert service.max_tokens == 2048
        assert service.temperature == 0.5
    
    @pytest.mark.asyncio
    async def test_chat_stream_mock(self):
        """测试流式对话（模拟）"""
        service = AIService("test_api_key")
        
        # 模拟客户端响应
        mock_chunk1 = Mock()
        mock_chunk1.choices = [Mock()]
        mock_chunk1.choices[0].delta = Mock()
        mock_chunk1.choices[0].delta.content = "Hello"
        mock_chunk1.choices[0].delta.reasoning_content = None
        
        mock_chunk2 = Mock()
        mock_chunk2.choices = [Mock()]
        mock_chunk2.choices[0].delta = Mock()
        mock_chunk2.choices[0].delta.content = " World"
        mock_chunk2.choices[0].delta.reasoning_content = None
        
        mock_response = [mock_chunk1, mock_chunk2]
        
        with patch.object(service._client.chat.completions, 'create', return_value=mock_response):
            messages = [{"role": "user", "content": "Hi"}]
            results = []
            
            async for chunk in service.chat_stream(messages):
                results.append(chunk)
            
            assert len(results) == 2
            assert results[0]["content"] == "Hello"
            assert results[1]["content"] == " World"
    
    @pytest.mark.asyncio
    async def test_chat_stream_with_thinking(self):
        """测试流式对话（带思考）"""
        service = AIService("test_api_key")
        
        # 模拟带思考的响应
        mock_chunk = Mock()
        mock_chunk.choices = [Mock()]
        mock_chunk.choices[0].delta = Mock()
        mock_chunk.choices[0].delta.content = "Answer"
        mock_chunk.choices[0].delta.reasoning_content = "Thinking..."
        
        mock_response = [mock_chunk]
        
        with patch.object(service._client.chat.completions, 'create', return_value=mock_response):
            messages = [{"role": "user", "content": "Hi"}]
            results = []
            
            async for chunk in service.chat_stream(messages, thinking_mode=True):
                results.append(chunk)
            
            assert len(results) == 2
            # 思考内容
            thinking_result = next((r for r in results if r.get("type") == "reasoning"), None)
            assert thinking_result is not None
            assert thinking_result["content"] == "Thinking..."
            
            # 回答内容
            content_result = next((r for r in results if r.get("type") == "content"), None)
            assert content_result is not None
            assert content_result["content"] == "Answer"
    
    @pytest.mark.asyncio
    async def test_chat_sync(self):
        """测试同步对话"""
        service = AIService("test_api_key")
        
        # 模拟响应
        mock_chunk1 = Mock()
        mock_chunk1.choices = [Mock()]
        mock_chunk1.choices[0].delta = Mock()
        mock_chunk1.choices[0].delta.content = "Hello"
        mock_chunk1.choices[0].delta.reasoning_content = None
        
        mock_chunk2 = Mock()
        mock_chunk2.choices = [Mock()]
        mock_chunk2.choices[0].delta = Mock()
        mock_chunk2.choices[0].delta.content = " World"
        mock_chunk2.choices[0].delta.reasoning_content = None
        
        mock_response = [mock_chunk1, mock_chunk2]
        
        with patch.object(service._client.chat.completions, 'create', return_value=mock_response):
            messages = [{"role": "user", "content": "Hi"}]
            result = await service.chat_sync(messages)
            
            assert result == "Hello World"
    
    @pytest.mark.asyncio
    async def test_chat_stream_error_handling(self):
        """测试错误处理"""
        service = AIService("test_api_key")
        
        # 模拟错误
        with patch.object(service._client.chat.completions, 'create', side_effect=Exception("API Error")):
            messages = [{"role": "user", "content": "Hi"}]
            results = []
            
            async for chunk in service.chat_stream(messages):
                results.append(chunk)
            
            assert len(results) == 1
            assert results[0]["type"] == "error"
            assert "API Error" in results[0]["message"]
