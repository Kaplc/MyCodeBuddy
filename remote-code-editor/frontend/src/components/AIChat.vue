<template>
  <div class="ai-chat">
    <!-- 头部组件 -->
    <ChatHeader
      :connection-status="connectionStatus"
      :context-count="contextCount"
      :message-count="messages.length"
      @show-history="handleShowHistory"
      @new-chat="createNewChat"
    />
    
      <!-- 消息列表组件 -->
      <div class="chat-body" :style="{ '--chat-font-size': fontSize + 'px' }">
        <MessageList
          :messages="messages"
          :is-streaming="isStreaming"
          :streaming-content="streamingContent"
          :streaming-reasoning="streamingReasoning"
          :font-size="fontSize"
          :model-name="modelDisplayName"
          :agent-status="agentStatus"
          :tool-executions="toolExecutions"
          @insert-code="handleInsertCode"
        />
      
      <!-- 输入组件 -->
      <ChatInput
        ref="chatInputRef"
        v-model="inputMessage"
        :is-streaming="isStreaming"
        :selected-model="selectedModel"
        :ai-mode="aiMode"
        :ai-status="connectionStatus"
        :current-workspace="currentWorkspace"
        @send="handleSendMessage"
        @stop="handleStop"
        @update:selected-model="selectedModel = $event"
        @update:ai-mode="aiMode = $event"
        @attach-files="showFileSelector"
      />
    </div>
    <!-- 历史对话对话框 -->
    <el-dialog v-model="showHistoryDialog" title="对话历史" width="500px" class="history-dialog">
      <div class="history-list">
        <div 
          v-for="chat in chatHistory" 
          :key="chat.id"
          class="history-item"
          :class="{ active: currentChatId === chat.id }"
          @click="loadChat(chat.id)"
        >
          <div class="history-info">
            <span class="history-title">{{ chat.title || '新对话' }}</span>
            <span class="history-time">{{ formatTime(chat.updated_at) }}</span>
          </div>
          <div class="history-meta">
            <span>{{ chat.message_count }} 条消息</span>
          </div>
          <el-button 
            size="small" 
            type="danger" 
            text 
            @click.stop="deleteChat(chat.id)"
          >
            <el-icon><Delete /></el-icon>
          </el-button>
        </div>
        <div v-if="chatHistory.length === 0" class="empty-history">
          暂无历史对话
        </div>
      </div>
      <template #footer>
        <el-button type="primary" @click="createNewChat">新建对话</el-button>
        <el-button @click="showHistoryDialog = false">关闭</el-button>
      </template>
    </el-dialog>
    
    <!-- 文件选择对话框 -->
    <el-dialog v-model="showFileSelectorDialog" title="选择要引用的文件" width="600px" class="file-selector-dialog">
      <div class="file-selector-content">
        <el-input
          v-model="fileSearchQuery"
          placeholder="搜索文件..."
          clearable
          class="file-search"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
        <div class="file-list">
          <div
            v-for="file in filteredWorkspaceFiles"
            :key="file.path"
            class="file-item"
            :class="{ selected: selectedFiles.includes(file.path) }"
            @click="toggleFileSelection(file.path)"
          >
            <el-icon><Document /></el-icon>
            <span class="file-path">{{ file.relativePath }}</span>
            <el-icon v-if="selectedFiles.includes(file.path)" class="check-icon"><Check /></el-icon>
          </div>
          <div v-if="filteredWorkspaceFiles.length === 0" class="empty-files">
            {{ fileSearchQuery ? '未找到匹配的文件' : '工作区中没有文件' }}
          </div>
        </div>
      </div>
      <template #footer>
        <el-button @click="showFileSelectorDialog = false">取消</el-button>
        <el-button type="primary" @click="confirmFileSelection" :disabled="selectedFiles.length === 0">
          确定 ({{ selectedFiles.length }})
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Delete, Search, Document, Check } from '@element-plus/icons-vue'
import ChatHeader from './ai-chat/ChatHeader.vue'
import MessageList from './ai-chat/MessageList.vue'
import ChatInput from './ai-chat/ChatInput.vue'
import { API_CONFIG } from '../config/api.js'
import axios from 'axios'

// 定义事件
const emit = defineEmits(['insert-code'])

// Props
const props = defineProps({
  selectedCode: {
    type: String,
    default: ''
  },
  fontSize: {
    type: Number,
    default: 13
  },
  currentWorkspace: {
    type: String,
    default: ''
  }
})

// 状态
const messages = ref([])
const inputMessage = ref('')
const isStreaming = ref(false)
const streamingReasoning = ref('')  // 思考内容
const streamingContent = ref('')    // 回答内容
const connectionStatus = ref('disconnected')

// Agent 模式状态
const agentStatus = ref(null)  // null | 'thinking' | 'executing'
const toolExecutions = ref([])  // 工具执行记录

// 模型和模式选择
const selectedModel = ref('glm-4-flash')
const aiMode = ref('ask')

// 模型显示名称映射
const modelNames = {
  'glm-4-flash': 'GLM-4.7-Flash',
  'glm-4v-flash': 'GLM-4.6v-Flash'
}

// 当前模型显示名称
const modelDisplayName = computed(() => {
  return modelNames[selectedModel.value] || selectedModel.value
})

// 历史对话相关
const showHistoryDialog = ref(false)
const chatHistory = ref([])
const currentChatId = ref(null)
const isLoadingHistory = ref(false)

// 文件选择相关
const showFileSelectorDialog = ref(false)
const fileSearchQuery = ref('')
const selectedFiles = ref([])
const workspaceFiles = ref([])
const chatInputRef = ref(null)

// 计算上下文数量（估算 token 数）
const contextCount = computed(() => {
  let totalChars = 0
  messages.value.forEach(m => {
    totalChars += m.content.length
    if (m.reasoningContent) {
      totalChars += m.reasoningContent.length
    }
  })
  // 粗略估算：中文约1.5字符/token，英文约4字符/token，取平均约2字符/token
  return Math.ceil(totalChars / 2)
})

// 过滤后的文件列表
const filteredWorkspaceFiles = computed(() => {
  if (!fileSearchQuery.value) {
    return workspaceFiles.value
  }
  const query = fileSearchQuery.value.toLowerCase()
  return workspaceFiles.value.filter(file => 
    file.relativePath.toLowerCase().includes(query)
  )
})

// API 基础URL
const apiBaseUrl = API_CONFIG.BASE_URL

// ==================== 对话历史 API 调用 ====================

// 获取对话列表
async function fetchChatHistory() {
  try {
    isLoadingHistory.value = true
    const params = {}
    if (props.currentWorkspace) {
      params.workspace = props.currentWorkspace
    }
    const response = await axios.get(`${apiBaseUrl}/api/conversations/list/`, { params })
    chatHistory.value = response.data.conversations || []
  } catch (error) {
    console.error('获取对话历史失败:', error)
    ElMessage.error('获取对话历史失败')
  } finally {
    isLoadingHistory.value = false
  }
}

// 创建新对话
async function createNewChat() {
  try {
    const response = await axios.post(`${apiBaseUrl}/api/conversations/create/`, {
      workspace: props.currentWorkspace,
      model: selectedModel.value,
      mode: aiMode.value === 'agent' ? 'agent' : 'chat'
    })
    
    const newChat = response.data
    currentChatId.value = newChat.id
    messages.value = []
    showHistoryDialog.value = false
    
    // 刷新对话列表
    await fetchChatHistory()
    
    ElMessage.success('已创建新对话')
  } catch (error) {
    console.error('创建对话失败:', error)
    ElMessage.error('创建对话失败')
  }
}

// 加载指定对话
async function loadChat(chatId) {
  try {
    const response = await axios.get(`${apiBaseUrl}/api/conversations/get/`, {
      params: { id: chatId }
    })
    
    const chatData = response.data
    currentChatId.value = chatId
    
    // 转换消息格式
    messages.value = (chatData.messages || [])
      .filter(msg => msg.role === 'user' || msg.role === 'assistant')
      .map(msg => ({
        role: msg.role,
        content: msg.content,
        reasoningContent: msg.reasoning || '',
        hasReasoning: !!msg.reasoning,
        toolExecutions: msg.tool_calls ? [{ calls: msg.tool_calls }] : null,
        timestamp: new Date(msg.created_at)
      }))
    
    // 更新模型和模式
    if (chatData.model) {
      selectedModel.value = chatData.model
    }
    if (chatData.mode === 'agent') {
      aiMode.value = 'agent'
    } else {
      aiMode.value = 'ask'
    }
    
    showHistoryDialog.value = false
  } catch (error) {
    console.error('加载对话失败:', error)
    ElMessage.error('加载对话失败')
  }
}

// 删除对话
async function deleteChat(chatId) {
  try {
    await ElMessageBox.confirm('确定要删除这个对话吗？', '删除对话', { type: 'warning' })
    
    await axios.post(`${apiBaseUrl}/api/conversations/delete/`, {
      id: chatId
    })
    
    // 从列表中移除
    chatHistory.value = chatHistory.value.filter(c => c.id !== chatId)
    
    // 如果删除的是当前对话，创建新对话
    if (currentChatId.value === chatId) {
      currentChatId.value = null
      messages.value = []
    }
    
    ElMessage.success('对话已删除')
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除对话失败:', error)
      ElMessage.error('删除对话失败')
    }
  }
}

// 清空当前对话消息
async function clearMessages() {
  if (currentChatId.value) {
    try {
      await axios.post(`${apiBaseUrl}/api/conversations/clear/`, {
        id: currentChatId.value
      })
    } catch (error) {
      console.error('清空对话失败:', error)
    }
  }
  messages.value = []
}

// 停止生成
const handleStop = () => {
  if (ws && ws.readyState === WebSocket.OPEN) {
    // 发送停止信号
    ws.send(JSON.stringify({ type: 'stop' }))
  }

  // 如果有正在生成的内容，保存到消息列表
  if (streamingContent.value || streamingReasoning.value) {
    messages.value.push({
      role: 'assistant',
      content: streamingContent.value,
      reasoningContent: streamingReasoning.value,
      hasReasoning: !!streamingReasoning.value,
      timestamp: new Date()
    })
  }

  // 重置状态
  streamingReasoning.value = ''
  streamingContent.value = ''
  isStreaming.value = false
  agentStatus.value = null
  toolExecutions.value = []
}

// 显示历史对话框时刷新列表
async function handleShowHistory() {
  showHistoryDialog.value = true
  await fetchChatHistory()
}

// 格式化时间
function formatTime(dateStr) {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  const now = new Date()
  const diff = now - date
  
  if (diff < 60000) return '刚刚'
  if (diff < 3600000) return `${Math.floor(diff / 60000)} 分钟前`
  if (diff < 86400000) return `${Math.floor(diff / 3600000)} 小时前`
  if (diff < 604800000) return `${Math.floor(diff / 86400000)} 天前`
  
  return date.toLocaleDateString()
}

// WebSocket连接
let ws = null
let reconnectAttempts = 0
const maxReconnectAttempts = 5

// 初始化WebSocket
onMounted(async () => {
  connectWebSocket()
  // 获取对话历史列表
  await fetchChatHistory()
})

// 清理
onUnmounted(() => {
  if (ws) {
    ws.close()
  }
})

// 监听选中的代码
watch(() => props.selectedCode, (code) => {
  if (code) {
    inputMessage.value = `请帮我分析或优化这段代码：\n\`\`\`\n${code}\n\`\`\``
  }
})

// 监听工作区变化，刷新对话列表
watch(() => props.currentWorkspace, async () => {
  // 工作区变化时，创建新对话
  currentChatId.value = null
  messages.value = []
  await fetchChatHistory()
})

// 连接WebSocket
function connectWebSocket() {
  connectionStatus.value = 'connecting'
  
  // 使用配置文件中的后端WebSocket地址
  const wsUrl = `${API_CONFIG.WS_URL}${API_CONFIG.API_PATHS.AI_CHAT}`
  
  ws = new WebSocket(wsUrl)
  
  ws.onopen = () => {
    connectionStatus.value = 'connected'
    reconnectAttempts = 0
    console.log('AI WebSocket 已连接:', wsUrl)
  }
  
  ws.onmessage = (event) => {
    const data = JSON.parse(event.data)
    handleWebSocketMessage(data)
  }
  
  ws.onclose = () => {
    connectionStatus.value = 'disconnected'
    console.log('AI WebSocket 已断开')
    
    // 自动重连
    if (reconnectAttempts < maxReconnectAttempts) {
      reconnectAttempts++
      setTimeout(connectWebSocket, 2000 * reconnectAttempts)
    }
  }
  
  ws.onerror = (error) => {
    console.error('WebSocket 错误:', error)
    connectionStatus.value = 'disconnected'
    
    // 显示用户友好的错误信息
    ElMessage.error('WebSocket连接失败，请检查后端服务是否正常运行')
  }
}

// 处理WebSocket消息
function handleWebSocketMessage(data) {
  console.log('[WebSocket] 收到消息:', data)
  
  if (data.type === 'content') {
    streamingContent.value += data.content
  } else if (data.type === 'reasoning') {
    streamingReasoning.value += data.content
  } else if (data.type === 'agent_status') {
    // Agent 状态更新
    agentStatus.value = data.status
    console.log('[Agent] 状态:', data.status, '迭代:', data.iteration)
  } else if (data.type === 'tool_start') {
    // 工具开始执行
    agentStatus.value = 'executing'
    toolExecutions.value.push({
      name: data.tool_name,
      arguments: data.arguments,
      status: 'running',
      result: null
    })
  } else if (data.type === 'tool_result') {
    // 工具执行完成
    const lastTool = toolExecutions.value[toolExecutions.value.length - 1]
    if (lastTool) {
      lastTool.status = data.result.success ? 'success' : 'error'
      lastTool.result = data.result
    }
    agentStatus.value = 'thinking'
  } else if (data.type === 'warning') {
    ElMessage.warning(data.message)
  } else if (data.type === 'done') {
    console.log('[WebSocket] 流式传输完成')

    if (streamingContent.value || toolExecutions.value.length > 0) {
      messages.value.push({
        role: 'assistant',
        content: streamingContent.value,
        reasoningContent: streamingReasoning.value,
        hasReasoning: !!streamingReasoning.value,
        toolExecutions: toolExecutions.value.length > 0 ? [...toolExecutions.value] : null,
        timestamp: new Date()
      })
    }
    // 重置状态
    streamingReasoning.value = ''
    streamingContent.value = ''
    isStreaming.value = false
    agentStatus.value = null
    toolExecutions.value = []
    
    // 刷新对话历史列表（更新消息数和时间）
    fetchChatHistory()
  } else if (data.type === 'error') {
    console.error('[WebSocket] 错误:', data.message)
    ElMessage.error(data.message)
    streamingReasoning.value = ''
    streamingContent.value = ''
    isStreaming.value = false
    agentStatus.value = null
    toolExecutions.value = []
  }
}

// 发送消息
async function handleSendMessage(content, attachedFiles = []) {
  if (!content.trim()) return

  // 检查网络连接状态
  if (connectionStatus.value === 'disconnected' || (ws && ws.readyState !== WebSocket.OPEN)) {
    // 添加用户消息到界面
    messages.value.push({
      role: 'user',
      content: content,
      timestamp: new Date()
    })

    // 添加网络异常回复
    messages.value.push({
      role: 'assistant',
      content: '网络异常，无法连接到AI服务。请检查网络连接后重试。',
      timestamp: new Date()
    })
    return
  }

  // 如果没有当前对话ID，先创建一个新对话
  if (!currentChatId.value) {
    try {
      const response = await axios.post(`${apiBaseUrl}/api/conversations/create/`, {
        workspace: props.currentWorkspace,
        model: selectedModel.value,
        mode: aiMode.value === 'agent' ? 'agent' : 'chat'
      })
      currentChatId.value = response.data.id
    } catch (error) {
      console.error('创建对话失败:', error)
      ElMessage.error('创建对话失败，请重试')
      return
    }
  }

  // 如果正在流式响应，先保存当前响应为消息
  if (isStreaming.value && (streamingContent.value || streamingReasoning.value)) {
    let fullContent = ''
    if (streamingReasoning.value) {
      fullContent += `[思考过程]\n${streamingReasoning.value}\n\n`
    }
    if (streamingContent.value) {
      fullContent += streamingContent.value
    }
    if (fullContent) {
      messages.value.push({
        role: 'assistant',
        content: fullContent,
        reasoningContent: streamingReasoning.value,
        hasReasoning: !!streamingReasoning.value,
        timestamp: new Date()
      })
    }
    streamingReasoning.value = ''
    streamingContent.value = ''
  }

  // 添加用户消息到界面
  messages.value.push({
    role: 'user',
    content: content,
    timestamp: new Date()
  })

  // 构建对话历史
  const chatMessages = messages.value.map(m => ({
    role: m.role,
    content: m.content
  }))

  // 发送到服务器（携带 conversation_id 和附件）
  ws.send(JSON.stringify({
    type: 'chat',
    model: selectedModel.value,
    thinking_mode: aiMode.value === 'agent',
    agent_mode: aiMode.value === 'agent',  // Agent 模式标志（向后兼容）
    ai_mode: aiMode.value,                 // AI 模式：'ask' 或 'agent'
    workspace: props.currentWorkspace,     // 当前工作区路径
    conversation_id: currentChatId.value,  // 对话ID
    messages: chatMessages,
    attached_files: attachedFiles.map(f => f.path)  // 附件文件路径列表
  }))

  // 开始流式响应
  isStreaming.value = true
  streamingReasoning.value = ''
  streamingContent.value = ''
  toolExecutions.value = []
  agentStatus.value = aiMode.value === 'agent' ? 'thinking' : null
}

// 处理插入代码
function handleInsertCode(content) {
  // 提取代码块
  const codeBlockRegex = /```[\w]*\n([\s\S]*?)```/g
  const matches = [...content.matchAll(codeBlockRegex)]
  
  if (matches.length > 0) {
    const code = matches[0][1].trim()
    emit('insert-code', code)
  } else {
    emit('insert-code', content)
  }
}

// 外部调用：发送消息
function sendMessage(content) {
  handleSendMessage(content)
}

// 文件选择相关方法
async function showFileSelector() {
  if (!props.currentWorkspace) {
    ElMessage.warning('请先选择工作区')
    return
  }
  
  // 加载工作区文件列表
  await loadWorkspaceFiles()
  showFileSelectorDialog.value = true
  selectedFiles.value = []
  fileSearchQuery.value = ''
}

async function loadWorkspaceFiles() {
  try {
    const response = await axios.get(`${apiBaseUrl}/api/workspace/files/`, {
      params: { path: props.currentWorkspace }
    })
    
    // 转换为相对路径格式
    workspaceFiles.value = response.data.files.map(file => ({
      path: file.path,
      relativePath: file.path.replace(props.currentWorkspace, '').replace(/^[/\\]/, '')
    }))
  } catch (error) {
    console.error('加载文件列表失败:', error)
    ElMessage.error('加载文件列表失败')
    workspaceFiles.value = []
  }
}

function toggleFileSelection(filePath) {
  const index = selectedFiles.value.indexOf(filePath)
  if (index > -1) {
    selectedFiles.value.splice(index, 1)
  } else {
    selectedFiles.value.push(filePath)
  }
}

function confirmFileSelection() {
  if (selectedFiles.value.length === 0) return
  
  // 将选中的文件添加到输入框
  selectedFiles.value.forEach(filePath => {
    const file = workspaceFiles.value.find(f => f.path === filePath)
    if (file && chatInputRef.value) {
      chatInputRef.value.addAttachedFile({
        path: filePath,
        name: file.relativePath
      })
    }
  })
  
  showFileSelectorDialog.value = false
  ElMessage.success(`已添加 ${selectedFiles.value.length} 个文件`)
}

// 暴露方法
defineExpose({
  sendMessage,
  clearMessages
})
</script>

<style scoped>
.ai-chat {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: #1e1e1e;
  border-left: 1px solid #333;
  overflow: hidden;
}

.chat-body {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  min-height: 0;
  padding: 0;
}

.history-dialog :deep(.el-dialog__body) {
  padding: 0;
}

.history-list {
  max-height: 400px;
  overflow-y: auto;
  padding: 8px;
}

.history-item {
  display: flex;
  align-items: center;
  padding: 12px;
  margin-bottom: 8px;
  background: #2d2d2d;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.2s;
}

.history-item:hover {
  background: #363636;
}

.history-item.active {
  background: rgba(64, 158, 255, 0.2);
  border: 1px solid #409eff;
}

.history-info {
  flex: 1;
  min-width: 0;
}

.history-title {
  display: block;
  font-size: 14px;
  color: #ccc;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.history-time {
  display: block;
  font-size: 12px;
  color: #888;
  margin-top: 4px;
}

.history-meta {
  font-size: 12px;
  color: #666;
  margin-right: 8px;
}

.empty-history {
  text-align: center;
  padding: 40px;
  color: #888;
}

.file-selector-dialog :deep(.el-dialog__body) {
  padding: 0;
}

.file-selector-content {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 16px;
}

.file-search {
  --el-input-bg-color: #2d2d2d;
  --el-input-border-color: #444;
  --el-input-text-color: #ccc;
}

.file-list {
  max-height: 400px;
  overflow-y: auto;
  border: 1px solid #333;
  border-radius: 6px;
  background: #2d2d2d;
}

.file-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  cursor: pointer;
  transition: background 0.2s;
  border-bottom: 1px solid #333;
}

.file-item:last-child {
  border-bottom: none;
}

.file-item:hover {
  background: #363636;
}

.file-item.selected {
  background: rgba(64, 158, 255, 0.15);
  border-left: 3px solid #409eff;
}

.file-item .el-icon {
  font-size: 16px;
  color: #888;
  flex-shrink: 0;
}

.file-path {
  flex: 1;
  font-size: 13px;
  color: #ccc;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.file-item.selected .file-path {
  color: #409eff;
}

.check-icon {
  color: #409eff !important;
}

.empty-files {
  text-align: center;
  padding: 40px;
  color: #888;
  font-size: 14px;
}
</style>
