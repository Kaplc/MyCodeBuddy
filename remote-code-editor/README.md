# 远程代码编辑器

一个轻量级的远程代码编辑器，集成AI自然语言编程功能。类似于VSCode配合AI插件的使用体验，但更加轻量级和专注。

## ✨ 功能特性

- 📁 **远程文件浏览与管理** - 浏览、创建、重命名、删除文件和目录
- ✏️ **纯文本代码编辑** - 基于Monaco Editor（VSCode核心编辑器）
- 🎨 **语法高亮** - 支持多种编程语言的语法高亮
- 🤖 **AI自然语言编程** - 基于智谱AI的代码辅助
- 💬 **AI对话交互** - 流式对话，支持代码解释、优化建议
- 🔄 **编辑器与AI协同** - 一键发送代码给AI，一键插入AI生成的代码
- 🌐 **Web远程访问** - 通过浏览器随时随地访问

## 🛠 技术栈

### 后端
- Python 3.10+
- FastAPI（异步Web框架）
- WebSocket（实时通信）
- 智谱AI API

### 前端
- Vue 3（渐进式框架）
- Monaco Editor（代码编辑器）
- Element Plus（UI组件库）
- Vite（构建工具）

## 🚀 快速开始

### 方式一：使用启动脚本（推荐）

**Windows:**
```bash
双击运行 start.bat
```

**Linux/Mac:**
```bash
chmod +x start.sh
./start.sh
```

### 方式二：手动启动

**1. 启动后端服务**
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**2. 启动前端服务**
```bash
cd frontend
npm install
npm run dev
```

**3. 访问应用**

打开浏览器访问：http://localhost:3000

## ⚙️ 配置

### 环境变量配置

复制 `backend/.env.example` 为 `backend/.env` 并填写配置：

```env
# 智谱AI API密钥（必填）
ZHIPU_API_KEY=your_api_key_here

# 工作目录（可选，默认为用户主目录下的code-editor-workspace）
WORKSPACE_PATH=/path/to/your/workspace
```

### 获取智谱AI API密钥

1. 访问 [智谱AI开放平台](https://open.bigmodel.cn/)
2. 注册/登录账号
3. 在控制台获取API密钥

## 🐳 Docker部署

```bash
# 构建并启动
docker-compose up -d

# 访问
http://localhost
```

## 📁 项目结构

```
remote-code-editor/
├── backend/                  # FastAPI后端
│   ├── main.py              # 应用入口
│   ├── routers/             # API路由
│   │   ├── files.py         # 文件操作API
│   │   └── ai.py            # AI对话API
│   ├── services/            # 业务逻辑
│   │   ├── file_service.py  # 文件服务
│   │   └── ai_service.py    # AI服务
│   ├── tests/               # 单元测试
│   ├── requirements.txt     # Python依赖
│   └── Dockerfile           # Docker配置
├── frontend/                 # Vue 3前端
│   ├── src/
│   │   ├── components/
│   │   │   ├── FileTree.vue     # 文件树组件
│   │   │   ├── CodeEditor.vue   # 代码编辑器
│   │   │   └── AIChat.vue       # AI对话组件
│   │   ├── App.vue              # 主应用
│   │   └── main.js              # 入口文件
│   ├── package.json         # 前端依赖
│   └── Dockerfile           # Docker配置
├── docker-compose.yml       # Docker Compose配置
├── start.bat                # Windows启动脚本
├── start.sh                 # Linux/Mac启动脚本
└── README.md
```

## 🧪 运行测试

```bash
cd backend
pytest
```

## 🔒 安全说明

- 文件操作有路径遍历防护，限制在工作目录内
- 生产环境请配置适当的CORS策略
- 建议使用HTTPS和身份认证

## 📝 使用说明

### 文件操作
- 左侧文件树可浏览、创建、重命名、删除文件
- 点击文件在编辑器中打开
- `Ctrl+S` 保存文件

### AI辅助
- 右侧AI对话面板可与AI交流
- 选中代码后点击"发送给AI"
- AI生成的代码可一键插入编辑器
- 支持代码解释、优化、重构等操作

## 📄 许可证

MIT License
