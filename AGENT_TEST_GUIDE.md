# Agent 功能测试指南

## 测试结果总结

### ✅ 后端核心功能测试通过（2026-03-12）

| 测试项 | 状态 | 说明 |
|--------|------|------|
| **配置读取** | ✅ 通过 | 成功读取3个模型，包含GLM4.7-Flash |
| **AI服务** | ✅ 通过 | AI服务初始化成功，glm-4.7-flash模型响应正常 |
| **工具定义** | ✅ 通过 | 加载16个工具，Agent模式16个，Ask模式3个(只读) |
| **工具执行** | ✅ 通过 | create_directory, write_file, read_file, list_directory全部正常 |

---

## 测试 1: 工作流使用 Agent

### 前置条件
- 后端服务需要运行在 `http://localhost:8000`

### 启动后端服务

```bash
# 进入后端目录
cd remote-code-editor/backend

# 启动 Django 后端
python manage.py runserver
```

### 测试步骤

1. **测试模型列表接口**

```bash
# 测试获取模型列表
curl http://localhost:8000/api/workflow/models/
```

预期返回：
```json
{
  "models": [
    {
      "id": "",
      "name": "默认",
      "description": "使用系统默认模型",
      "provider": "default"
    },
    {
      "id": "glm-4-flash",
      "name": "GLM-4-Flash",
      "description": "智谱 GLM-4-Flash，快速响应",
      "provider": "zhipu",
      "api_key_env": "ZHIPU_API_KEY"
    },
    {
      "id": "glm-4.7-flash",
      "name": "GLM4.7-Flash",
      "description": "智谱 GLM4.7-Flash，新一代快速模型",
      "provider": "zhipu",
      "api_key_env": "ZHIPU_API_KEY"
    }
  ]
}
```

2. **测试工作流工具列表接口**

```bash
# 测试获取工作流工具
curl http://localhost:8000/api/workflow/tools/
```

3. **测试运行工作流**

```bash
curl -X POST http://localhost:8000/api/workflow/run/ \
  -H "Content-Type: application/json" \
  -d '{
    "workflow_id": "test-workflow",
    "input": "测试输入",
    "workspace": "test_workspace"
  }'
```

---

## 测试 2: 聊天助手使用 Agent

### 前置条件
- 后端服务运行（包含 WebSocket 支持）
- 前端服务运行

### 启动完整服务

```bash
# 终端 1: 启动后端
cd remote-code-editor/backend
python manage.py runserver

# 终端 2: 启动前端（如果需要）
cd remote-code-editor/frontend
npm run dev
```

### 测试步骤

#### 方式 1: 通过前端界面测试

1. 打开浏览器访问前端地址（通常是 `http://localhost:3000` 或类似地址）
2. 在 AI 聊天面板中：
   - 选择工作区
   - 选择模型：GLM4.7-Flash
   - 选择 AI 模式：
     - **Chat**: 普通对话模式
     - **Ask**: 只读 Agent 模式（可以读取文件、搜索内容等）
     - **Agent**: 完整 Agent 模式（可以读/写文件、执行命令等）

#### 方式 2: 通过 WebSocket 直接测试

使用 Python 脚本测试 WebSocket 连接：

```python
import asyncio
import websockets
import json

async def test_agent_chat():
    uri = "ws://localhost:8000/ws/ai-chat/"
    
    async with websockets.connect(uri) as websocket:
        # 发送聊天消息（Agent 模式）
        message = {
            "type": "chat",
            "messages": [
                {"role": "user", "content": "请帮我列出当前目录的文件"}
            ],
            "model": "glm-4.7-flash",
            "ai_mode": "agent",
            "workspace": "remote-code-editor/backend/workspaces/test_workspace",
            "conversation_id": ""
        }
        
        await websocket.send(json.dumps(message))
        
        # 接收响应
        while True:
            response = await websocket.recv()
            data = json.loads(response)
            
            if data.get('type') == 'content':
                print(f"内容: {data['content']}")
            elif data.get('type') == 'tool_start':
                print(f"工具开始执行: {data['tool_name']}")
            elif data.get('type') == 'tool_result':
                print(f"工具执行结果: {data['result']}")
            elif data.get('type') == 'done':
                print("对话完成")
                break
            elif data.get('type') == 'error':
                print(f"错误: {data['message']}")
                break

asyncio.run(test_agent_chat())
```

---

## 可用的 Agent 工具列表

### 基础工具（6个）
1. **read_file** - 读取文件内容
2. **write_file** - 创建或修改文件
3. **list_directory** - 列出目录内容
4. **search_content** - 在文件中搜索内容
5. **execute_command** - 执行终端命令
6. **create_directory** - 创建目录
7. **delete_file** - 删除文件或目录

### 代码验证工具（6个）
8. **generate_tests** - 生成单元测试
9. **run_tests** - 运行测试
10. **search_symbol** - 搜索代码符号
11. **get_code_references** - 查找代码引用
12. **run_verification_pipeline** - 运行验证流水线
13. **index_workspace** - 索引工作区代码

### 高级工具（3个）
14. **get_call_graph** - 获取函数调用图
15. **get_file_outline** - 获取文件结构大纲
16. **verify_with_z3** - 使用 Z3 求解器验证

### Ask 模式（只读工具）
- read_file
- list_directory
- search_content

---

## AI 模式说明

### 1. Chat 模式
- **用途**: 普通对话
- **工具**: 不使用工具
- **能力**: 纯文本对话，无法访问文件系统

### 2. Ask 模式
- **用途**: 代码阅读和理解
- **工具**: 只读工具（read_file, list_directory, search_content）
- **能力**: 可以查看和分析代码，但不能修改

### 3. Agent 模式
- **用途**: 代码生成和任务自动化
- **工具**: 所有工具（包括读写、执行命令等）
- **能力**: 可以完成完整的编程任务（读、写、运行代码）

---

## 故障排查

### 问题 1: 无法连接到 WebSocket

**检查后端是否运行**
```bash
# 检查 8000 端口
netstat -ano | findstr :8000
```

**检查 Django Channels 配置**
确保 `config/asgi.py` 和 `config/settings.py` 中正确配置了 Channels

### 问题 2: Agent 不执行工具

**检查工作区路径**
确保已经选择了有效的工作区路径

**检查 ZHIPU_API_KEY**
```bash
# 查看 .env 文件
cat remote-code-editor/backend/.env
```

### 问题 3: GLM4.7-Flash 模型不可用

**检查配置文件**
```bash
cat remote-code-editor/backend/config/ai_config.json
```

确保配置文件中包含 `glm-4.7-flash` 模型定义

---

## 性能监控

### 查看前端日志
```bash
powershell -Command "Get-Content 'remote-code-editor\backend\logs\frontend.log' -Tail 50"
```

### 查看后端日志
```bash
powershell -Command "Get-Content 'remote-code-editor\backend\logs\django.log' -Tail 50"
```

---

## 总结

### ✅ 已验证功能
- GLM4.7-Flash 模型配置正确
- AI 服务调用正常
- Agent 工具加载完整（16个）
- 工具执行器功能正常

### 🔄 待测试功能（需要启动后端）
- 工作流 API 接口
- WebSocket Agent 对话
- 前端 UI 集成

### 📝 下一步
1. 启动后端服务
2. 运行完整的功能测试
3. 通过前端界面进行实际使用测试
