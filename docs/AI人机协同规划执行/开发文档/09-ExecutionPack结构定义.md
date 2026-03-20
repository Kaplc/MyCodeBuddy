### AI 人机协同规划执行开发文档

## 九、Execution Pack 结构定义

Execution Pack 是会话进入执行阶段的正式输入。

### 推荐结构

```json
{
  "session_id": "sess-001",
  "goal": "完成用户任务",
  "workflow_id": "12",
  "workspace": "c:/Users/.../MyCodeBuddy/remote-code-editor",
  "master_plan": {
    "version": 3,
    "plan_nodes": []
  },
  "selected_nodes": ["plan-2", "plan-3"],
  "reviewed_node_plans": [],
  "global_constraints": [
    "优先复用现有实现",
    "高风险工具需人工确认"
  ],
  "execution_mode": {
    "task_execution_mode": "task_pool",
    "max_concurrent_tasks": 1,
    "require_human_approval_for": [
      "write_file",
      "execute_command",
      "delete_file"
    ]
  },
  "task_pool": {
    "selection_strategy": "topological_priority",
    "tasks": []
  },
  "scheduler": {
    "replan_on_failure": true,
    "allow_task_skip": true,
    "allow_human_requeue": true
  }
}
```

### Execution Pack 的职责边界

- 主方案负责表达整体目标与阶段
- 节点思路负责表达局部细化策略
- 任务池负责表达最小可执行单元
- 调度器负责选择下一任务
- Agent 只负责执行当前任务

---
