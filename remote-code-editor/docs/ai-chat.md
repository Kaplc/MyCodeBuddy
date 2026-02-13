# AI聊天功能实现说明

## 功能概述

实现了基于智谱AI的实时流式对话功能，支持深度思考模式和实时打字机效果。

## 技术架构

### 后端 (Django + Channels + Daphne)

#### 1. AI服务 (backend/services/ai_service.py)

按照智谱AI官方示例实现流式调用：

```python
response = self._client.chat.completions.create(
    model="glm-4.7-flash",
    messages=messages,
    thinking={"type": "enabled"},  # 启用深度思考模式
    stream=True,                    # 启用流式输出
    max_tokens=65536,
    temperature=1.0
)

# 流式获取回复并转发给前端
for chunk in response:
    delta = chunk.choices[0].delta
    
    # 思考内容
    if delta.reasoning_content:
        yield {"type": "reasoning", "content": delta.reasoning_content}
    
    # 回答内容
    if delta.content:
        yield {"type": "content", "content": delta.content}
```

#### 2. WebSocket消费者 (backend/api/consumers.py)

接收前端WebSocket连接，调用AI服务并流式转发数据。

### 前端 (Vue 3)

#### 1. AIChat组件 (frontend/src/components/AIChat.vue)

- 建立WebSocket连接
- 接收流式消息并存储
- 支持深度思考模式

```javascript
// 发送消息
ws.send(JSON.stringify({
  type: 'chat',
  model: 'glm-4-flash',
  thinking_mode: true,  // 启用深度思考模式
  messages: chatMessages
}))

// 接收消息
if (data.type === 'reasoning') {
  streamingReasoning.value += data.content
} else if (data.type === 'content') {
  streamingContent.value += data.content
}
```

#### 2. MessageList组件 (frontend/src/components/ai-chat/MessageList.vue)

实现实时打字机效果：

- **思考区域**：独立显示AI的思考过程，带🧠图标
- **回答区域**：显示AI的最终回答
- **打字机效果**：每15ms显示一个字符
- **代码高亮**：支持多种编程语言
- **复制功能**：一键复制代码或内容

## 数据流程

```
用户输入 
  → 前端WebSocket发送请求 
  → 后端WebSocket接收
  → 调用智谱AI API（stream=True）
  → 接收流式响应（reasoning_content + content）
  → 通过WebSocket转发给前端
  → 前端逐步显示（打字机效果）
```

## 启动步骤

1. **配置环境变量** (backend/.env)
   ```
   ZHIPU_API_KEY=your_api_key_here
   ```

2. **启动后端**
   ```bash
   cd remote-code-editor
   start.bat
   ```

3. **启动前端**
   ```bash
   cd frontend
   npm run dev
   ```

4. **测试功能**
   - 在AI聊天界面发送问题
   - 观察思考过程和回答内容的实时打字机效果
   - 查看浏览器控制台和后端日志

## 调试日志

### 后端日志
```
[AI Service] 收到思考内容片段: ...
[AI Service] 收到回答内容片段: ...
[AI Service] 流式传输完成
```

### 前端控制台
```
[WebSocket] 收到消息: {type: "reasoning", content: "..."}
[WebSocket] 收到消息: {type: "content", content: "..."}
[WebSocket] 流式传输完成
```

## 功能特点

1. **实时流式显示**：思考内容和回答内容都实时显示，无需等待
2. **深度思考模式**：启用智谱AI的深度思考能力
3. **优雅的打字机效果**：每15ms显示一个字符，流畅自然
4. **独立的思考区域**：思考过程单独显示，便于理解AI的思路
5. **代码高亮**：支持多种编程语言的语法高亮
6. **响应式设计**：自适应不同屏幕尺寸

## 技术要点

1. **ASGI服务器**：使用Daphne支持WebSocket
2. **Channels**：Django的异步Web框架处理WebSocket
3. **流式处理**：后端和前端都采用流式处理，不阻塞
4. **性能优化**：增量更新DOM，避免频繁重渲染

## 参考文档

- [智谱AI官方文档](https://docs.bigmodel.cn/cn/guide/models/free/glm-4.7-flash)
- [Django Channels文档](https://channels.readthedocs.io/)
- [WebSocket API](https://developer.mozilla.org/zh-CN/docs/Web/API/WebSocket)

## 注意事项

1. 需要有效的智谱AI API密钥
2. 后端必须使用ASGI服务器（Daphne）运行，不能使用普通的runserver
3. 深度思考模式可能会消耗更多tokens
4. 建议在生产环境中添加速率限制和错误处理
