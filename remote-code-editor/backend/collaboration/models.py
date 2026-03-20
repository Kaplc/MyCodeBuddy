"""Collaboration 数据模型 - 交互式需求文档生成"""
import json
from django.db import models


def _json_loads(value: str, default):
    if not value:
        return default
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return default


def _json_dumps(value):
    return json.dumps(value, ensure_ascii=False)


class CollaborationSession(models.Model):
    """交互式需求文档生成会话"""

    goal = models.TextField(verbose_name='任务目标')
    workspace = models.CharField(max_length=1024, blank=True, default='', verbose_name='工作区')
    phase = models.CharField(max_length=32, default='interactive_planning', verbose_name='当前阶段')
    status = models.CharField(max_length=32, default='in_progress', verbose_name='会话状态')
    master_plan = models.TextField(blank=True, default='', verbose_name='主计划文档')
    execution_pack = models.TextField(blank=True, default='', verbose_name='执行包')
    metadata = models.TextField(default='{}', verbose_name='扩展信息')
    latest_error = models.TextField(blank=True, default='', verbose_name='最近错误')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    def get_metadata(self):
        return _json_loads(self.metadata, {})

    def set_metadata(self, value):
        self.metadata = _json_dumps(value)

    class Meta:
        db_table = 'ai_collaboration_session'
        ordering = ['-updated_at']
        verbose_name = '交互式需求会话'
        verbose_name_plural = '交互式需求会话'


class ChatMessage(models.Model):
    """交互式问答消息记录"""

    MESSAGE_TYPES = [
        ('question', 'AI提问'),
        ('answer', '用户回答'),
        ('system', '系统消息'),
    ]

    session = models.ForeignKey(
        CollaborationSession,
        on_delete=models.CASCADE,
        related_name='messages',
        verbose_name='所属会话'
    )
    message_type = models.CharField(max_length=16, choices=MESSAGE_TYPES, verbose_name='消息类型')
    question_id = models.CharField(max_length=64, blank=True, default='', verbose_name='问题ID')
    question_text = models.TextField(blank=True, default='', verbose_name='问题文本')
    question_options = models.TextField(default='[]', verbose_name='问题选项(JSON数组)')
    selected_option_ids = models.TextField(default='[]', verbose_name='选中的选项ID(JSON数组)')
    selected_options = models.TextField(default='[]', verbose_name='选中的选项完整信息(JSON数组)')
    custom_input = models.TextField(blank=True, default='', verbose_name='用户自定义输入')
    ai_raw_request = models.TextField(blank=True, default='', verbose_name='AI原始请求')
    ai_raw_response = models.TextField(blank=True, default='', verbose_name='AI原始响应')
    index = models.IntegerField(default=0, verbose_name='消息索引')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    def get_question_options(self):
        return _json_loads(self.question_options, [])

    def set_question_options(self, value):
        self.question_options = _json_dumps(value)

    def get_selected_option_ids(self):
        return _json_loads(self.selected_option_ids, [])

    def set_selected_option_ids(self, value):
        self.selected_option_ids = _json_dumps(value)

    def get_selected_options(self):
        return _json_loads(self.selected_options, [])

    def set_selected_options(self, value):
        self.selected_options = _json_dumps(value)

    class Meta:
        db_table = 'ai_chat_message'
        ordering = ['session', 'index']
        verbose_name = '问答消息'
        verbose_name_plural = '问答消息'