# 工作流节点高亮功能 - 日志说明

## 功能概述

当工作流执行时，前端会以 500ms 间隔轮询后端API，获取当前正在执行的节点ID，并在画布上以**绿色呼吸灯效果**高亮显示该节点。

---

## 日志关键词

### 后端日志关键词

**文件位置**: `remote-code-editor/backend/logs/django.log`

**查看命令**:
```bash
# Windows PowerShell
Get-Content remote-code-editor\backend\logs\django.log -Wait

# Linux/Mac
tail -f remote-code-editor/backend/logs/django.log
```

**关键词**:

1. **工作流执行器**
   ```
   [Workflow Executor] 开始执行工作流
   [Workflow Executor] 获取工作流
   [Workflow Executor] 构建 LangGraph
   [Workflow Executor] 开始执行图
   [Workflow Executor] 图执行完成
   ```

2. **节点执行器**
   ```
   [Node Executor] 开始执行节点 | node_id=xxx, node_type=xxx
   [Node Executor]    节点配置 | config=xxx
   [Node Executor] 节点执行完成 | node_id=xxx, exec_time=xxxms
   [Node Executor]    输出键 | keys=xxx
   ```

3. **执行状态管理**
   ```
   [Execution State] 更新执行状态 | workflow_id=xxx, node_id=xxx, status=running
   [Execution State] 查询执行状态 | workflow_id=xxx
   [Execution State] 清除执行状态 | workflow_id=xxx
   ```

4. **执行状态API**
   ```
   [Execution API] 收到状态查询请求 | workflow_id=xxx
   [Execution API] 返回执行状态 | workflow_id=xxx, node_id=xxx
   ```

---

### 前端日志关键词

**查看方式**: 浏览器控制台（F12）

**关键词**:

1. **工作流运行流程**
   ```
   [工作流运行] 开始执行工作流
   [工作流运行]    输入: xxx
   [工作流运行]    图节点数: xxx
   [工作流运行] 启动状态轮询
   [工作流运行] 发送执行请求到后端...
   [工作流运行] 收到后端响应
   [工作流运行] 执行成功
   [工作流运行] 工作流执行流程结束
   ```

2. **执行状态轮询**
   ```
   [工作流执行] 开始轮询执行状态
   [工作流执行]    workflow_id: xxx
   [工作流执行]    轮询间隔: 500 ms
   [工作流执行] 检测到节点变化
   [工作流执行]    前一个节点: xxx
   [工作流执行]    当前节点: xxx
   [工作流执行] 停止轮询执行状态
   ```

3. **节点高亮**
   ```
   [工作流执行] 开始高亮节点 | node_id: xxx
   [工作流执行]    找到目标节点 | id: xxx, type: xxx
   [工作流执行] 节点高亮完成 | 高亮节点数: 1
   [工作流执行] 清除所有节点高亮
   ```

---

## 完整执行流程日志示例

### 后端日志示例

```log
[Workflow Executor] 开始执行工作流 | workflow_id=60, workspace=
[Workflow Executor] 获取工作流 | workflow_id=60
[Workflow Executor] 工作流信息 | name=测试工作流, version=1
[Workflow Executor] 图数据 | nodes=3, edges=2
[Workflow Executor] 构建 LangGraph
[Workflow Executor] 开始执行图 | input_type=str

[Node Executor] 开始执行节点 | node_id=prompt_1, node_type=prompt, workflow_id=60
[Node Executor]    节点配置 | config={'template': '简单回复: {input}'}
[Execution State] 更新执行状态 | workflow_id=60, node_id=prompt_1, status=running
[Execution API] 收到状态查询请求 | workflow_id=60
[Execution API] 返回执行状态 | workflow_id=60, node_id=prompt_1, status=running
[Node Executor] 节点执行完成 | node_id=prompt_1, node_type=prompt, exec_time=3200ms
[Node Executor]    输出键 | keys=['input', 'prompt', 'result']

[Workflow Executor] 图执行完成 | invoke_time=3205ms
[Workflow Executor] 执行成功 | total_time=3210ms
```

### 前端日志示例

```log
================================================================================
[工作流运行] 开始执行工作流
================================================================================
[工作流运行]    输入: 你好
[工作流运行]    图节点数: 3
[工作流运行]    图边数: 2
[工作流运行]    当前工作流ID: 60
[工作流运行] 启动状态轮询 | workflow_id: 60

============================================================
[工作流执行] 开始轮询执行状态
============================================================
[工作流执行]    workflow_id: 60
[工作流执行]    轮询间隔: 500 ms
[工作流执行] 轮询定时器已启动

------------------------------------------------------------
[工作流执行] 检测到节点变化
[工作流执行]    前一个节点: 无
[工作流执行]    当前节点: prompt_1
[工作流执行]    状态: running
[工作流执行]    请求耗时: 12 ms
------------------------------------------------------------
[工作流执行] 开始高亮节点 | node_id: prompt_1
[工作流执行]    找到目标节点 | id: prompt_1, type: prompt
[工作流执行] 节点高亮完成 | 高亮节点数: 1

[工作流运行] 发送执行请求到后端...
[工作流运行] 收到后端响应 | 耗时: 3210 ms
[工作流运行] 执行成功
[工作流运行]    执行时间: 3210ms
[工作流运行]    节点数: 3
[工作流运行]    边数: 2

============================================================
[工作流执行] 停止轮询执行状态
============================================================
[工作流执行] 清除所有节点高亮
[工作流运行] 工作流执行流程结束
================================================================================
```

---

## 测试方式

### 1. 启动后端服务

```bash
cd remote-code-editor/backend
python manage.py runserver
```

### 2. 查看后端日志

新开一个终端：
```bash
# Windows
Get-Content remote-code-editor\backend\logs\django.log -Wait

# Linux/Mac
tail -f remote-code-editor/backend/logs/django.log
```

### 3. 启动前端服务

```bash
cd remote-code-editor/frontend
npm run dev
```

### 4. 测试功能

1. 访问 `http://localhost:5173`
2. 创建一个工作流（Input → Prompt → Output）
3. 打开浏览器控制台（F12）
4. 点击运行工作流
5. 观察浏览器控制台和后端日志

---

## 日志分析技巧

### 查找特定节点的执行情况

**后端**:
```bash
grep "node_id=prompt_1" remote-code-editor/backend/logs/django.log
```

**前端**:
浏览器控制台搜索框输入：`node_id: prompt_1`

### 查找执行失败的日志

**后端**:
```bash
grep -i "error\|失败\|exception" remote-code-editor/backend/logs/django.log
```

**前端**:
浏览器控制台搜索框输入：`失败` 或 `ERROR`

### 查看完整执行链路

**后端**:
```bash
grep "workflow_id=60" remote-code-editor/backend/logs/django.log | grep -E "Node Executor|Workflow Executor"
```

**前端**:
浏览器控制台搜索框输入：`工作流运行` 或 `工作流执行`

---

## 性能监控

### 节点执行时间

从日志中提取：
```
[Node Executor] 节点执行完成 | exec_time=3200ms
```

### 轮询请求耗时

从前端日志中提取：
```
[工作流执行]    请求耗时: 12 ms
```

### 完整执行时间

```
[Workflow Executor] 执行成功 | total_time=3210ms
```
