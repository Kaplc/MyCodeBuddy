"""Workflow 数据模型"""
import json
from django.db import models


class Workflow(models.Model):
    """工作流模型"""

    name = models.CharField(max_length=100, verbose_name='名称')
    graph = models.TextField(verbose_name='图定义', blank=True, default='{}')
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

    class Meta:
        db_table = 'ai_workflow'
        ordering = ['-updated_at']
        verbose_name = '工作流'
        verbose_name_plural = '工作流'

    def __str__(self) -> str:
        return f"{self.name} (v{self.version})"
