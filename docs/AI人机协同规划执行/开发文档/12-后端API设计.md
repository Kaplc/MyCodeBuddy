### AI 人机协同规划执行开发文档

## 十二、后端 API 设计

### 1. 生成主方案

#### 接口
`POST /api/workflow/plan/generate/`

#### 请求体

```json
{
  "workflow_id": "12",
  "goal": "修复某模块中的配置读取逻辑",
  "workspace": "c:/Users/.../MyCodeBuddy/remote-code-editor"
}
```

#### 返回

```json
{
  "success": true,
  "session_id": "sess-001",
  "phase": "planning",
  "master_plan": {
    "goal": "修复某模块中的配置读取逻辑",
    "plan_nodes": []
  }
}
```

### 2. 生成节点细化思路

#### 接口
`POST /api/workflow/plan/refine/`

#### 请求体

```json
{
  "session_id": "sess-001",
  "selected_node_ids": ["plan-2", "plan-3"]
}
```

### 3. 提交人工审查结果

#### 接口
`POST /api/workflow/plan/review/submit/`

#### 请求体

```json
{
  "session_id": "sess-001",
  "reviews": [
    {
      "node_id": "plan-3",
      "review_status": "approved_with_changes",
      "human_comments": [
        "必须先读后写",
        "禁止直接覆盖已有文件"
      ],
      "require_runtime_approval": true
    }
  ]
}
```

### 4. 生成 Execution Pack

#### 接口
`POST /api/workflow/execution-pack/build/`

#### 请求体

```json
{
  "session_id": "sess-001"
}
```

### 5. 启动执行

#### 接口
`POST /api/workflow/executions/start/`

#### 请求体

```json
{
  "session_id": "sess-001"
}
```

#### 说明
执行开始后：

- 会话状态切为 `executing`
- 任务池初始化为 `ready/pending`
- 调度器启动
- 前端进入任务池轮询模式

### 6. 获取会话状态

#### 接口
`GET /api/workflow/executions/state/?session_id=sess-001`

#### 返回内容建议

- 会话状态
- 当前阶段
- 当前任务
- 主方案摘要
- 已审查节点摘要
- 任务池摘要
- 最新人工介入状态
- 气泡记录

### 7. 获取任务池列表

#### 接口
`GET /api/workflow/tasks/list/?session_id=sess-001`

### 8. 人工介入任务

#### 接口
`POST /api/workflow/tasks/intervene/`

#### 请求体示例

```json
{
  "session_id": "sess-001",
  "task_id": "task-002",
  "action": "edit_and_continue",
  "payload": {
    "constraints": [
      "必须先读后写",
      "写入前需再次确认目标路径"
    ]
  }
}
```

### 9. 查询会话详情

#### 接口
`GET /api/workflow/session/detail/?session_id=sess-001`

用于页面刷新恢复：

- 主方案
- 节点细化
- 审查结果
- Execution Pack
- 任务池
- 运行结果

---
