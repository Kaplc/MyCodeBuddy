"""
AI对话历史数据模型
"""
import uuid
from django.db import models
from django.utils import timezone


class Conversation(models.Model):
    """对话会话模型"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255, default='新对话', verbose_name='对话标题')
    workspace = models.CharField(max_length=500, blank=True, default='', verbose_name='工作区路径')
    model = models.CharField(max_length=50, default='glm-4-flash', verbose_name='使用的模型')
    mode = models.CharField(max_length=20, default='chat', verbose_name='对话模式')  # chat 或 agent
    created_at = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        db_table = 'ai_conversation'
        ordering = ['-updated_at']
        verbose_name = '对话会话'
        verbose_name_plural = '对话会话'
    
    def __str__(self):
        return f"{self.title} ({self.created_at.strftime('%Y-%m-%d %H:%M')})"
    
    def get_messages_for_api(self):
        """获取用于 API 调用的消息列表"""
        import json
        messages = []
        for msg in self.messages.all().order_by('created_at'):
            message_data = {
                'role': msg.role,
                'content': msg.content
            }
            # 如果有工具调用信息，添加到消息中
            if msg.tool_calls:
                try:
                    tool_calls = json.loads(msg.tool_calls)
                    message_data['tool_calls'] = tool_calls
                except (json.JSONDecodeError, TypeError):
                    # 如果解析失败，保持原样或跳过
                    pass
            if msg.tool_call_id:
                message_data['tool_call_id'] = msg.tool_call_id
            messages.append(message_data)
        return messages


class Message(models.Model):
    """对话消息模型"""
    
    ROLE_CHOICES = [
        ('user', '用户'),
        ('assistant', 'AI助手'),
        ('system', '系统'),
        ('tool', '工具'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conversation = models.ForeignKey(
        Conversation, 
        on_delete=models.CASCADE, 
        related_name='messages',
        verbose_name='所属对话'
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, verbose_name='消息角色')
    content = models.TextField(verbose_name='消息内容')
    
    # Agent 模式相关字段
    tool_calls = models.TextField(null=True, blank=True, default='', verbose_name='工具调用信息')
    tool_call_id = models.CharField(max_length=100, blank=True, default='', verbose_name='工具调用ID')
    tool_name = models.CharField(max_length=100, blank=True, default='', verbose_name='工具名称')
    
    # 思考过程（reasoning）
    reasoning = models.TextField(blank=True, default='', verbose_name='思考过程')
    
    created_at = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    
    class Meta:
        db_table = 'ai_message'
        ordering = ['created_at']
        verbose_name = '对话消息'
        verbose_name_plural = '对话消息'
    
    def __str__(self):
        return f"[{self.role}] {self.content[:50]}..."
    
    def to_dict(self):
        """转换为字典格式"""
        import json
        data = {
            'id': str(self.id),
            'role': self.role,
            'content': self.content,
            'created_at': self.created_at.isoformat()
        }
        if self.reasoning:
            data['reasoning'] = self.reasoning
        if self.tool_calls:
            try:
                tool_calls = json.loads(self.tool_calls)
                data['tool_calls'] = tool_calls
            except (json.JSONDecodeError, TypeError):
                pass
        if self.tool_call_id:
            data['tool_call_id'] = self.tool_call_id
        if self.tool_name:
            data['tool_name'] = self.tool_name
        return data
