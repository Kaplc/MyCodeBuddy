### AI 人机协同规划执行开发文档

## 二十八、Agent 任务执行协议文档

### 1. 协议目标

Agent 的输入不再是原始自然语言大任务，而是 **调度器分配的一条单任务执行上下文**。协议要解决的问题是：
- 让 Agent 明确当前只做什么
- 让 Agent 知道不能做什么
- 让 Agent 在什么条件下必须暂停等待人工
- 让 Agent 输出什么结构给调度器

---

### 2. 单任务输入协议

#### 顶层结构
```json
{
  "session_id": "123",
  "workflow_id": "12",
  "goal": "完成用户目标",
  "workspace": "c:/Users/.../remote-code-editor",
  "current_task": {
    "task_id": "task-002",
    "title": "实施变更并完成校验",
    "task_type": "modify",
    "description": "修改目标实现并验证结果",
    "constraints": [
      "必须先读后写",
      "禁止直接删除核心文件"
    ],
    "success_criteria": [
      "改动完成",
      "验证通过"
    ],
    "requires_human_approval": true,
    "allowed_tools": [
      "read_file",
      "search_content",
      "write_file",
      "execute_command"
    ]
  },
  "upstream_context": {
    "artifacts": {},
    "summary": []
  },
  "global_constraints": [
    "优先复用现有实现",
    "高风险工具必须审批"
  ]
}
```

---

### 3. Prompt 组装规则

给 Agent 的消息建议按以下顺序组装：

#### system 层
- 说明当前为 **单任务执行模式**
- 强调只能围绕 `current_task` 行动
- 强调必须遵守 `allowed_tools` 与 `constraints`
- 强调如需高风险动作必须中断并请求审批

#### user 层
拼接以下内容：
- 总目标
- 当前任务标题与描述
- 成功标准
- 上游产出摘要
- 全局约束
- 当前任务约束
- 可用工具白名单

#### 禁止事项
必须显式提示 Agent：
- 不得擅自跨任务推进
- 不得自行修改未授权文件范围
- 不得跳过成功校验直接宣告完成
- 不得在审批前执行高风险工具

---

### 4. Agent 执行循环协议

#### Step 1：加载单任务上下文
- 调度器选出一个 `ready` 任务
- 构造单任务输入协议对象
- 初始化执行气泡与状态

#### Step 2：调用 AI 生成下一步动作
- 允许先输出少量分析
- 若需工具调用，则必须来自 `allowed_tools`

#### Step 3：工具执行前审批钩子
当满足以下任一条件时，不直接执行工具：
- `current_task.requires_human_approval = true`
- 工具属于高风险集合：`write_file / execute_command / delete_file`
- 工具参数命中了危险路径或危险命令

此时 Agent 需要返回中断信号给调度器。

#### Step 4：执行工具或中断等待
- 若不需审批：执行工具并回写结果
- 若需审批：任务状态改 `waiting_human`

#### Step 5：任务结束判断
- 满足成功标准：`done`
- 临时失败可恢复：`failed -> retry`
- 不可恢复：转人工或触发 `replan`

---

### 5. Agent 输出协议

#### 成功输出
```json
{
  "task_id": "task-002",
  "status": "done",
  "result_summary": "已完成目标实现修改并完成校验",
  "artifacts": {
    "modified_files": ["a.py", "b.py"],
    "verification": "passed"
  },
  "suggested_next_action": "unlock_downstream",
  "bubble_records": []
}
```

#### 等待人工输出
```json
{
  "task_id": "task-002",
  "status": "waiting_human",
  "wait_reason": "high_risk_tool",
  "pending_action": {
    "tool_name": "write_file",
    "arguments": {
      "filePath": "..."
    }
  },
  "result_summary": "准备写入文件，等待人工确认"
}
```

#### 失败输出
```json
{
  "task_id": "task-002",
  "status": "failed",
  "error_type": "tool_param_error",
  "error_message": "目标路径不存在",
  "result_summary": "写入前校验失败",
  "suggested_next_action": "retry_or_human"
}
```

---

### 6. 调度器与 Agent 的职责边界

#### 调度器负责
- 选择任务
- 管理状态流转
- 管理重试次数
- 判定是否转人工
- 解锁下游任务
- 记录会话级状态

#### Agent 负责
- 只执行当前任务
- 只消费当前上下文
- 只在允许工具范围内行动
- 返回结构化结果
- 遇到风险及时中断

> **原则：调度器做流程控制，Agent 做任务执行。**

---

### 7. 幂等与恢复要求

#### 幂等要求
对于 `modify / verify` 类任务，应尽量保证以下能力：
- 再次执行时能识别文件已修改
- 已完成任务不能重复产生破坏性结果
- `result_summary` 中明确说明“已存在/已完成”场景

#### 恢复要求
- 页面刷新不应丢失当前任务上下文
- 若任务在 `waiting_human`，恢复后必须能重新展示待审批动作
- 若任务在 `running` 时进程中断，恢复后应先回退到 `ready` 或标记为 `failed`

---

### 8. 高风险工具协议

#### 首批高风险工具
- `write_file`
- `execute_command`
- `delete_file`

#### 高风险工具审批最少字段

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `tool_name` | `string` | 工具名 |
| `arguments` | `object` | 原始参数 |
| `reason` | `string` | 为什么必须执行 |
| `expected_effect` | `string` | 预期影响 |
| `rollback_hint` | `string` | 回退建议 |

#### 前端展示要求
- 明确展示受影响文件/命令
- 明确展示是否可编辑参数
- 明确展示继续、修改后继续、拒绝、终止入口

---

### 9. 推荐后续实现点

为了让协议真正落地到 `agent_node.py`，建议后续继续补：
- `task_context_builder.py`：专门构建单任务上下文
- `risk_guard.py`：统一判断高风险工具与危险参数
- `agent_result_parser.py`：把 Agent 输出标准化为任务结果对象
- `human_wait_manager.py`：管理等待人工与恢复执行逻辑

---
