---
name: interactive-requirement-doc-agent
overview: 实现一个交互式需求文档生成 Agent，通过多轮问答方式引导用户选择，逐步构建完整的需求文档提示词。
todos:
  - id: create-interactive-service
    content: 创建 interactive_planner_service.py，实现问题流程定义和核心逻辑
    status: completed
  - id: create-models
    content: 在 models.py 中添加 InteractiveSession 模型或扩展 metadata
    status: completed
  - id: implement-question-flow
    content: 实现 9 个章节的问题流程定义和选项生成器
    status: completed
    dependencies:
      - create-interactive-service
  - id: implement-state-management
    content: 实现会话状态管理和进度追踪
    status: completed
    dependencies:
      - implement-question-flow
  - id: create-api-views
    content: 在 views.py 中创建 API 视图 (start, answer, state, generate)
    status: completed
    dependencies:
      - implement-state-management
  - id: register-urls
    content: 在 urls.py 中注册 API URL 路由
    status: completed
    dependencies:
      - create-api-views
  - id: update-exports
    content: 更新 services/__init__.py 导出新服务
    status: completed
    dependencies:
      - register-urls
---

## 用户需求

实现一个计划模式的 agent，通过不断给选项让用户选择来构建需求文档的提示词。

## 核心功能

1. **初始目标输入**：用户输入初始目标/想法
2. **多轮选项问答**：AI 分析后生成多个选项让用户选择
3. **渐进式收集**：每轮选择后继续追问更多细节
4. **章节覆盖**：覆盖需求文档的 9 个章节（背景与目标、范围、用户与使用场景、功能需求、非功能需求、输入输出、边界情况、技术方案、验收标准）
5. **最终输出**：生成完整的《需求文档》提示词

## 交互流程

- 用户输入目标 → AI 生成第一组问题选项
- 用户选择/输入 → AI 追问下一组问题
- 循环直到所有章节信息收集完毕
- AI 生成完整需求文档提示词

## 状态管理

- 记录用户已完成选择的章节
- 保存每轮用户的回答内容
- 支持中途退出和恢复

## 技术方案

### 技术栈

- **语言**：Python (Django)
- **位置**：`backend/collaboration/services/interactive_planner_service.py`

### 核心模块设计

#### 1. 问题流程定义 (QuestionFlow)

定义每个章节的标准问题模板和选项生成策略：

- 章节1：背景与目标（Why）- 2-3个问题
- 章节2：范围（Scope）- 2个问题
- 章节3：用户与使用场景 - 2-3个问题
- 章节4-9：按需配置

#### 2. 选项生成器 (OptionGenerator)

- 基于用户目标动态生成合理选项
- 支持预设选项 + 自定义输入
- 选项数量控制在 3-5 个

#### 3. 会话状态管理

- 扩展现有 `CollaborationSession` 模型的 metadata 字段
- 新增 `InteractiveSession` 模型跟踪问答进度

### API 设计

```
POST /api/collaboration/interactive/start          # 开始新会话，输入目标
POST /api/collaboration/interactive/answer         # 提交答案
GET  /api/collaboration/interactive/state          # 获取当前状态和问题
POST /api/collaboration/interactive/generate       # 生成最终文档
POST /api/collaboration/interactive/reset          # 重置会话
```

### 数据结构

#### InteractiveSession 状态

```python
{
    "goal": "用户原始目标",
    "current_section": "3",
    "current_question_index": 0,
    "answers": {
        "1": {"background": "...", "problem": "...", "goal": "..."},
        "2": {"includes": [...], "excludes": [...]},
    },
    "completed_sections": ["1", "2"],
    "status": "in_progress"
}
```

#### 问题响应格式

```python
{
    "question_id": "2_scope_includes",
    "section_id": "2",
    "section_name": "范围（Scope）",
    "question": "这个项目需要包含哪些核心功能？",
    "options": [
        {"id": "a", "text": "用户管理（注册、登录、权限）"},
        {"id": "b", "text": "数据分析和报表"},
        {"id": "c", "text": "消息通知系统"},
    ],
    "allow_multi_select": True,
    "allow_custom_input": True,
    "hint": "可以选择多个功能模块"
}
```