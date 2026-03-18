"""Workflow 数据模型"""
import json
from django.db import models


class Workflow(models.Model):
    """工作流模型"""

    name = models.CharField(max_length=100, verbose_name='名称')
    graph = models.TextField(verbose_name='图定义', blank=True, default='{}')
    last_result = models.TextField(verbose_name='上次执行结果', blank=True, default='')
    bubble_records = models.TextField(verbose_name='气泡流记录', blank=True, default='[]')
    version = models.PositiveIntegerField(default=1, verbose_name='版本号')
    is_temp = models.BooleanField(default=False, verbose_name='是否为临时工作流')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    def get_graph(self):
        """获取图定义（自动反序列化）"""
        return json.loads(self.graph or '{}')

    def set_graph(self, value):
        """设置图定义（自动序列化）"""
        self.graph = json.dumps(value, ensure_ascii=False)

    def get_last_result(self):
        """获取上次执行结果（自动反序列化）"""
        if not self.last_result:
            return None
        try:
            return json.loads(self.last_result)
        except json.JSONDecodeError:
            return None

    def set_last_result(self, value):
        """设置执行结果（自动序列化）"""
        self.last_result = json.dumps(value, ensure_ascii=False)

    def get_bubble_records(self):
        """获取气泡流记录（自动反序列化）"""
        if not self.bubble_records:
            return []
        try:
            return json.loads(self.bubble_records)
        except json.JSONDecodeError:
            return []

    def set_bubble_records(self, value):
        """设置气泡流记录（自动序列化）"""
        self.bubble_records = json.dumps(value, ensure_ascii=False)

    def add_bubble_record(self, record):
        """添加单条气泡记录"""
        records = self.get_bubble_records()
        records.append(record)
        self.set_bubble_records(records)

    class Meta:
        db_table = 'ai_workflow'
        ordering = ['-updated_at']
        verbose_name = '工作流'
        verbose_name_plural = '工作流'

    def __str__(self) -> str:
        return f"{self.name} (v{self.version})"


class WorkflowState(models.Model):
    """工作流状态（存储上次打开的工作流ID等）"""

    key = models.CharField(max_length=50, unique=True, verbose_name='键')
    value = models.CharField(max_length=200, verbose_name='值')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'ai_workflow_state'
        verbose_name = '工作流状态'
        verbose_name_plural = '工作流状态'

    def __str__(self) -> str:
        return f"{self.key}: {self.value}"

    @classmethod
    def get_last_workflow_id(cls):
        """获取上次打开的工作流ID"""
        state = cls.objects.filter(key='last_workflow_id').first()
        return state.value if state else None

    @classmethod
    def set_last_workflow_id(cls, workflow_id):
        """设置上次打开的工作流ID"""
        cls.objects.update_or_create(
            key='last_workflow_id',
            defaults={'value': str(workflow_id)}
        )

    @classmethod
    def clear_last_workflow_id(cls):
        """清除上次打开的工作流ID"""
        cls.objects.filter(key='last_workflow_id').delete()
