# 实施计划

## 项目结构
```
remote-code-editor/
├── backend/              # FastAPI后端
│   ├── main.py          # 应用入口
│   ├── routers/         # API路由
│   │   ├── files.py     # 文件操作API
│   │   └── ai.py        # AI对话API
│   ├── services/        # 业务逻辑
│   │   ├── file_service.py
│   │   └── ai_service.py
│   └── requirements.txt
├── frontend/            # Vue 3前端
│   ├── src/
│   │   ├── components/
│   │   │   ├── FileTree.vue
│   │   │   ├── CodeEditor.vue
│   │   │   └── AIChat.vue
│   │   ├── App.vue
│   │   └── main.js
│   └── package.json
└── README.md
```

## 编码任务清单

- [ ] 1. 搭建项目基础结构
   - 创建项目根目录 `remote-code-editor`
   - 初始化后端目录结构（backend/）并创建 `requirements.txt`（FastAPI、uvicorn、websockets等依赖）
   - 初始化前端目录结构（frontend/）并创建 `package.json`（Vue 3、Monaco Editor、Element Plus等依赖）
   - 创建基础README文档，说明项目启动方式
   - _需求：5.1、5.2_

- [ ] 2. 实现后端文件操作API
   - 创建 `backend/main.py`，配置FastAPI应用和CORS
   - 实现 `backend/routers/files.py`，包含获取目录树、读取文件、保存文件、创建文件/文件夹的API端点
   - 实现 `backend/services/file_service.py`，封装文件系统操作逻辑（路径验证、权限检查、错误处理）
   - 添加文件锁机制，处理并发编辑冲突
   - _需求：1.1、1.2、1.3、1.4、1.5、2.1、2.2、2.3、2.4、2.5、5.4_

- [ ] 3. 实现后端AI服务集成
   - 复用现有 `zhipu_chat/api/client.py` 的智谱AI客户端代码
   - 创建 `backend/routers/ai.py`，实现AI对话的WebSocket端点
   - 实现 `backend/services/ai_service.py`，处理自然语言请求并调用智谱AI API
   - 添加请求超时和错误处理机制
   - _需求：3.1、3.2、3.6_

- [ ] 4. 开发前端文件树组件
   - 创建 `frontend/src/components/FileTree.vue`，使用Element Plus的Tree组件
   - 实现目录树的懒加载和展开/折叠功能
   - 实现文件点击加载、新建文件/文件夹的交互逻辑
   - 添加右键菜单（新建、重命名、删除等）
   - _需求：1.1、1.2、1.3、1.4、1.5_

- [ ] 5. 开发前端代码编辑器组件
   - 创建 `frontend/src/components/CodeEditor.vue`，集成Monaco Editor
   - 实现文件内容加载、编辑、保存功能
   - 添加保存快捷键（Ctrl+S）和自动保存提示
   - 实现未保存提示和语法高亮
   - _需求：2.1、2.2、2.3、2.4、2.5、2.6_

- [ ] 6. 开发前端AI对话组件
   - 创建 `frontend/src/components/AIChat.vue`，实现对话界面
   - 实现WebSocket连接和消息收发
   - 添加代码插入、复制、代码解释、优化建议等交互按钮
   - 实现对话历史管理和清空功能
   - _需求：3.1、3.2、3.3、3.4、3.5、3.6、4.2、4.4_

- [ ] 7. 实现编辑器与AI对话协同功能
   - 在CodeEditor中实现文本选择事件，支持发送选中文本到AI
   - 在AIChat中实现将AI生成的代码插入到编辑器光标位置
   - 添加AI对话窗口的可折叠和调整大小功能
   - 实现AI修改代码后的定位跳转功能
   - _需求：4.1、4.2、4.3、4.5_

- [ ] 8. 整合前端主应用和布局
   - 创建 `frontend/src/App.vue`，设计整体布局（左侧文件树、中间编辑器、右侧AI对话）
   - 配置Vue Router（如需多页面）
   - 实现全局状态管理（当前文件、编辑状态等）
   - 添加网络连接状态监测和自动重连逻辑
   - _需求：5.1、5.2、5.3、4.5_

- [ ] 9. 编写后端单元测试
   - 为文件服务编写测试用例（路径遍历、权限检查、并发处理）
   - 为AI服务编写测试用例（请求处理、错误处理）
   - _需求：1.4、2.4、3.6、5.4_

- [ ] 10. 编写集成测试和部署配置
   - 编写前后端集成测试脚本
   - 创建Docker配置文件（可选）
   - 编写部署文档和启动脚本
   - _需求：5.1、5.2_