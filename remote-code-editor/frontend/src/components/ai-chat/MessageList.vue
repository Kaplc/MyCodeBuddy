<template>
  <div class="message-list-wrapper">
    <div ref="containerRef" class="messages-container">
    <!-- 空状态 -->
    <!-- 空状态 -->
    <div v-if="messages.length === 0" class="empty-state">
      <el-icon><ChatLineRound /></el-icon>
      <p>开始与AI助手对话</p>
      <p class="hint">你可以询问代码问题、请求代码优化或解释</p>
    </div>
    
    <!-- 消息列表 -->
    <div
      v-for="(msg, index) in messages"
      :key="index"
      class="message"
      :class="msg.role"
    >
      <div class="message-header">
        <span class="role-name">{{ msg.role === 'user' ? '你' : modelName }}</span>
        <span class="time">{{ formatTime(msg.timestamp) }}</span>
      </div>
      <div class="message-content">
        <!-- 解析消息内容，分离思考过程和回答 -->
        <template v-if="msg.role === 'assistant'">
          <!-- 有思考过程的显示 -->
          <div v-if="msg.hasReasoning" class="thinking-section" :class="{ collapsed: expandedThinking[index] !== true }">
            <div class="thinking-header" @click="toggleThinking(index)">
              <span class="thinking-icon">{{ expandedThinking[index] === true ? '▼' : '▶' }}</span>
              <span>思考过程</span>
            </div>
            <div class="thinking-content" v-show="expandedThinking[index] === true">
              <pre v-html="formatMessage(msg.reasoningContent)"></pre>
            </div>
          </div>
          <!-- 工具执行记录 -->
          <div v-if="msg.toolExecutions && msg.toolExecutions.length > 0" class="tool-executions-section">
            <div class="tool-executions-header" @click="toggleToolExecutions(index)">
              <span class="tool-icon">🔧</span>
              <span>工具执行 ({{ msg.toolExecutions.length }})</span>
              <span class="expand-icon">{{ expandedToolExecutions[index] === true ? '▼' : '▶' }}</span>
            </div>
            <div v-show="expandedToolExecutions[index] === true" class="tool-executions-list">
              <div 
                v-for="(tool, toolIndex) in msg.toolExecutions" 
                :key="toolIndex"
                class="tool-execution-item"
                :class="tool.status"
              >
                <div class="tool-execution-header">
                  <span class="tool-status-icon">
                    {{ tool.status === 'success' ? '✅' : tool.status === 'error' ? '❌' : '⏳' }}
                  </span>
                  <span class="tool-name">{{ getToolDisplayName(tool.name) }}</span>
                </div>
                <div class="tool-execution-args">
                  <code>{{ JSON.stringify(tool.arguments) }}</code>
                </div>
                <div v-if="tool.result" class="tool-execution-result">
                  <pre>{{ formatToolResult(tool.result) }}</pre>
                </div>
              </div>
            </div>
          </div>
          <div class="content-section">
            <pre v-html="formatMessage(msg.content)"></pre>
          </div>
        </template>
        <template v-else>
          <!-- 引用的文件和消息内容在同一行 -->
          <span v-if="msg.attachedFiles && msg.attachedFiles.length > 0" class="inline-attachments">
            <span
              v-for="(file, fIndex) in msg.attachedFiles"
              :key="fIndex"
              class="attachment-tag"
            >
              <el-icon v-if="file.is_dir"><Folder /></el-icon>
              <el-icon v-else><Document /></el-icon>
              <span>{{ file.name }}</span>
            </span>
          </span>
          <pre>{{ msg.content }}</pre>
        </template>
      </div>
      <!-- AI消息操作按钮 -->
      <div v-if="msg.role === 'assistant'" class="message-actions">
        <el-button size="small" text @click="handleInsertCode(msg.content)">
          <el-icon><DocumentCopy /></el-icon>
          插入代码
        </el-button>
        <el-button size="small" text @click="handleCopy(msg.content)">
          <el-icon><CopyDocument /></el-icon>
          复制
        </el-button>
      </div>
    </div>

    <!-- 流式响应中 - 只有在有内容时才显示 -->
    <div v-if="isStreaming && (displayContent || displayReasoning || (toolExecutions && toolExecutions.length > 0))" class="message assistant streaming">
      <div class="message-header">
        <span class="role-name">{{ modelName }}</span>
        <span class="time">
          <template v-if="agentStatus === 'executing'">执行工具中...</template>
          <template v-else-if="agentStatus === 'thinking'">思考中...</template>
          <template v-else>正在回答...</template>
        </span>
      </div>
      <div class="message-content">
        <!-- Agent 工具执行状态 -->
        <div v-if="toolExecutions && toolExecutions.length > 0" class="tool-executions-section streaming">
          <div class="tool-executions-header">
            <span class="tool-icon">🔧</span>
            <span>工具执行中 ({{ toolExecutions.length }})</span>
          </div>
          <div class="tool-executions-list">
            <div 
              v-for="(tool, toolIndex) in toolExecutions" 
              :key="toolIndex"
              class="tool-execution-item"
              :class="tool.status"
            >
              <div class="tool-execution-header">
                <span class="tool-status-icon">
                  <template v-if="tool.status === 'running'">
                    <span class="loading-spinner">⏳</span>
                  </template>
                  <template v-else>
                    {{ tool.status === 'success' ? '✅' : '❌' }}
                  </template>
                </span>
                <span class="tool-name">{{ getToolDisplayName(tool.name) }}</span>
              </div>
              <div class="tool-execution-args">
                <code>{{ JSON.stringify(tool.arguments) }}</code>
              </div>
              <div v-if="tool.result" class="tool-execution-result">
                <pre>{{ formatToolResult(tool.result) }}</pre>
              </div>
            </div>
          </div>
        </div>
        <!-- 思考内容 - 打字机效果 -->
        <div v-if="displayReasoning" class="thinking-section streaming">
          <div class="thinking-header">
            <span class="thinking-icon">🧠</span>
            思考
          </div>
          <pre v-html="formatMessage(displayReasoning)"></pre>
        </div>
        <!-- 回答内容 - 打字机效果 -->
        <div v-if="displayContent" class="content-section">
          <pre v-html="formatMessage(displayContent)"></pre>
        </div>
        <!-- 打字光标 - 根据当前状态显示 -->
        <span v-if="isTypingReasoning" class="typing-cursor"></span>
      </div>
    </div>
    </div>
    
    <!-- 滚动到底部按钮 -->
    <transition name="fade">
      <div v-if="showScrollToBottom" class="scroll-to-bottom" @click="scrollToBottom(true)" title="滚动到底部 (Ctrl+End)">
        <el-icon><ArrowDown /></el-icon>
      </div>
    </transition>
  </div>
</template>

<script setup>
import { ref, watch, nextTick, onMounted, computed, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import { ChatLineRound, DocumentCopy, CopyDocument, ArrowDown, Folder, Document } from '@element-plus/icons-vue'
import hljs from 'highlight.js/lib/core'
import javascript from 'highlight.js/lib/languages/javascript'
import python from 'highlight.js/lib/languages/python'
import xml from 'highlight.js/lib/languages/xml'
import css from 'highlight.js/lib/languages/css'
import json from 'highlight.js/lib/languages/json'
import typescript from 'highlight.js/lib/languages/typescript'
import bash from 'highlight.js/lib/languages/bash'
import sql from 'highlight.js/lib/languages/sql'
import 'highlight.js/styles/atom-one-dark.css'

// 注册语言
hljs.registerLanguage('javascript', javascript)
hljs.registerLanguage('js', javascript)
hljs.registerLanguage('python', python)
hljs.registerLanguage('html', xml)
hljs.registerLanguage('xml', xml)
hljs.registerLanguage('css', css)
hljs.registerLanguage('json', json)
hljs.registerLanguage('typescript', typescript)
hljs.registerLanguage('ts', typescript)
hljs.registerLanguage('bash', bash)
hljs.registerLanguage('shell', bash)
hljs.registerLanguage('sql', sql)

// Props
const props = defineProps({
  messages: {
    type: Array,
    default: () => []
  },
  isStreaming: {
    type: Boolean,
    default: false
  },
  streamingContent: {
    type: String,
    default: ''
  },
  streamingReasoning: {
    type: String,
    default: ''
  },
  fontSize: {
    type: Number,
    default: 13
  },
  modelName: {
    type: String,
    default: 'AI'
  },
  agentStatus: {
    type: String,
    default: null
  },
  toolExecutions: {
    type: Array,
    default: () => []
  }
})

// Emits
const emit = defineEmits(['insert-code', 'copy'])

// 容器引用
const containerRef = ref(null)

// 思考过程展开/折叠状态
const expandedThinking = ref({})
const expandedToolExecutions = ref({})

// 智能滚动控制
const isUserScrolling = ref(false)
const showScrollToBottom = ref(false)

// 工具名称映射
const toolDisplayNames = {
  'read_file': '📖 读取文件',
  'write_file': '📝 写入文件',
  'list_directory': '📁 列出目录',
  'search_content': '🔍 搜索内容',
  'execute_command': '💻 执行命令',
  'create_directory': '📂 创建目录',
  'delete_file': '🗑️ 删除文件'
}

// 获取工具显示名称
function getToolDisplayName(name) {
  return toolDisplayNames[name] || name
}

// 格式化工具结果
function formatToolResult(result) {
  if (!result) return ''
  
  // 对于文件内容，截断显示
  if (result.content && result.content.length > 500) {
    return JSON.stringify({
      ...result,
      content: result.content.substring(0, 500) + '\n... (内容已截断)'
    }, null, 2)
  }
  
  return JSON.stringify(result, null, 2)
}

// 切换思考过程展开/折叠
function toggleThinking(index) {
  const current = expandedThinking.value[index]
  // 默认是折叠状态(undefined/false)，点击后切换
  expandedThinking.value[index] = current === true ? false : true
}

// 切换工具执行展开/折叠
function toggleToolExecutions(index) {
  const current = expandedToolExecutions.value[index]
  expandedToolExecutions.value[index] = current === true ? false : true
}

// 打字机效果状态
const displayReasoning = ref('')
const displayContent = ref('')
const currentReasoningIndex = ref(0)
const currentContentIndex = ref(0)
let typingTimer = null
const TYPING_SPEED = 15 // 毫秒，每个字符的间隔

// 监听流式内容变化，实现流式打字机效果
watch(() => props.streamingReasoning, (newVal) => {
  if (newVal) {
    // 新字符到达，增加显示长度
    const targetLength = newVal.length
    if (currentReasoningIndex.value < targetLength) {
      startIncrementalTyping(newVal, 'reasoning', targetLength)
    }
  }
}, { immediate: true })

watch(() => props.streamingContent, (newVal) => {
  if (newVal) {
    // 新字符到达，增加显示长度
    const targetLength = newVal.length
    if (currentContentIndex.value < targetLength) {
      startIncrementalTyping(newVal, 'content', targetLength)
    }
  }
}, { immediate: true })

// 流式打字机效果函数（增量更新）
function startIncrementalTyping(fullText, type, targetLength) {
  const targetRef = type === 'reasoning' ? displayReasoning : displayContent
  const indexRef = type === 'reasoning' ? currentReasoningIndex : currentContentIndex

  // 如果是短文本且首次到达，直接显示
  if (targetLength < 30 && indexRef.value === 0) {
    targetRef.value = fullText
    indexRef.value = targetLength
    return
  }

  // 使用定时器逐步增加显示的字符数
  if (!typingTimer) {
    typingTimer = setInterval(() => {
      const reasoningTarget = props.streamingReasoning.length
      const contentTarget = props.streamingContent.length

      // 更新思考过程
      if (currentReasoningIndex.value < reasoningTarget) {
        currentReasoningIndex.value++
        displayReasoning.value = props.streamingReasoning.substring(0, currentReasoningIndex.value)
      }

      // 更新回答内容
      if (currentContentIndex.value < contentTarget) {
        currentContentIndex.value++
        displayContent.value = props.streamingContent.substring(0, currentContentIndex.value)
      }

      // 如果两者都完成了，清除定时器
      if (currentReasoningIndex.value >= reasoningTarget && 
          currentContentIndex.value >= contentTarget) {
        clearInterval(typingTimer)
        typingTimer = null
      }
    }, TYPING_SPEED)
  }
}

// 重置打字机状态
function resetTypewriter() {
  if (typingTimer) {
    clearInterval(typingTimer)
    typingTimer = null
  }
  displayReasoning.value = ''
  displayContent.value = ''
  currentReasoningIndex.value = 0
  currentContentIndex.value = 0
}

// 监听流式结束，重置状态
watch(() => props.isStreaming, (newVal, oldVal) => {
  if (newVal) {
    // 新的流式响应开始，重置打字机状态
    resetTypewriter()
  } else {
    // 用户中断时，streamingContent 可能已被清空
    // 此时应保持当前已显示的内容，而不是用空字符串覆盖
    if (props.streamingReasoning) {
      displayReasoning.value = props.streamingReasoning
    }
    if (props.streamingContent) {
      displayContent.value = props.streamingContent
    }
    // 停止打字机定时器，但保留当前显示的内容
    if (typingTimer) {
      clearInterval(typingTimer)
      typingTimer = null
    }
  }
})

// 计算属性：判断当前是否正在打字机显示思考内容
const isTypingReasoning = computed(() => {
  return props.isStreaming && 
         currentReasoningIndex.value < props.streamingReasoning.length
})

// 监听消息变化，智能滚动到底部
watch(() => [props.messages.length, props.streamingContent, props.streamingReasoning, props.toolExecutions.length], () => {
  // 只有在用户没有手动滚动时才自动滚动
  if (!isUserScrolling.value) {
    scrollToBottom()
  }
}, { deep: true })

onMounted(() => {
  scrollToBottom()
  // 监听滚动事件
  if (containerRef.value) {
    containerRef.value.addEventListener('scroll', handleScroll)
  }
  // 监听快捷键
  window.addEventListener('keydown', handleKeydown)
})

onUnmounted(() => {
  // 清理事件监听
  if (containerRef.value) {
    containerRef.value.removeEventListener('scroll', handleScroll)
  }
  window.removeEventListener('keydown', handleKeydown)
})

// 处理快捷键
function handleKeydown(event) {
  // Ctrl+End 滚动到底部
  if (event.ctrlKey && event.key === 'End') {
    event.preventDefault()
    scrollToBottom(true)
  }
}

// 处理滚动事件
function handleScroll() {
  if (!containerRef.value) return
  
  const { scrollTop, scrollHeight, clientHeight } = containerRef.value
  const distanceFromBottom = scrollHeight - scrollTop - clientHeight
  
  // 如果距离底部超过100px，认为用户在向上滚动，立即打断自动滚动
  if (distanceFromBottom > 100) {
    isUserScrolling.value = true
    showScrollToBottom.value = true
  } else {
    // 如果已经在底部，隐藏按钮但不改变滚动状态
    // 这样可以避免用户手动滚动到底部时立即恢复自动滚动
    showScrollToBottom.value = false
  }
}

// 滚动到底部
function scrollToBottom(smooth = false) {
  nextTick(() => {
    if (containerRef.value) {
      if (smooth) {
        containerRef.value.scrollTo({
          top: containerRef.value.scrollHeight,
          behavior: 'smooth'
        })
      } else {
        containerRef.value.scrollTop = containerRef.value.scrollHeight
      }
      // 点击按钮或按快捷键后，立即恢复自动跟踪
      isUserScrolling.value = false
      showScrollToBottom.value = false
    }
  })
}

// 格式化消息（带代码高亮）
function formatMessage(content) {
  if (!content) return ''
  
  // 转义HTML
  let html = content
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
  
  // 处理思考过程标签（用于历史消息）
  html = html.replace(/\[思考过程\]/g, '<div class="thinking-label">🧠 思考</div>')
  
  // 将思考标签后的内容包装在思考容器中
  html = html.replace(
    /(<div class="thinking-label">🧠 思考<\/div>)([\s\S]*?)(?=<div class="thinking-label">|$)/g,
    '$1<div class="thinking-content">$2</div>'
  )
  
  // 代码块高亮
  html = html.replace(/```(\w*)\n([\s\S]*?)```/g, (match, lang, code) => {
    let highlighted = code
    const language = lang || 'plaintext'
    try {
      if (hljs.getLanguage(language)) {
        highlighted = hljs.highlight(code, { language }).value
      } else {
        highlighted = hljs.highlightAuto(code).value
      }
    } catch (e) {
      console.warn('Highlight failed:', e)
    }
    return `<pre class="code-block"><code class="hljs language-${language}">${highlighted}</code></pre>`
  })
  
  // 行内代码
  html = html.replace(/`([^`]+)`/g, '<code class="inline-code">$1</code>')
  
  // 粗体
  html = html.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
  
  // 斜体
  html = html.replace(/\*([^*]+)\*/g, '<em>$1</em>')
  
  // 换行
  html = html.replace(/\n/g, '<br>')
  
  return html
}

// 格式化时间
function formatTime(date) {
  if (!date) return ''
  const d = new Date(date)
  return d.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
}

// 插入代码
function handleInsertCode(content) {
  emit('insert-code', content)
}

// 复制
async function handleCopy(content) {
  try {
    await navigator.clipboard.writeText(content)
    ElMessage.success('已复制到剪贴板')
  } catch (error) {
    ElMessage.error('复制失败')
  }
}
</script>

<style scoped>
.message-list-wrapper {
  flex: 1;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  min-height: 0;
  position: relative;
}

.messages-container {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  min-height: 0;
  background: #1e1e1e;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 200px;
  color: #666;
  text-align: center;
}

.empty-state .el-icon {
  font-size: 48px;
  margin-bottom: 12px;
}

.empty-state .hint {
  font-size: 12px;
  color: #555;
  margin-top: 8px;
}

.message {
  margin-bottom: 16px;
  padding: 12px;
  border-radius: 12px;
  background: #2d2d2d;
}

.message.user {
  background: #2b4a6b;
  margin-left: 40px;
}

.message-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
  font-size: 12px;
  color: #888;
}

.role-name {
  font-weight: 500;
  color: #aaa;
}

.message-content {
  color: #ddd;
  font-size: var(--chat-font-size, 13px);
  line-height: 1.6;
}

.message-content pre {
  margin: 0;
  white-space: pre-wrap;
  word-wrap: break-word;
  font-family: inherit;
}

/* 消息中的引用文件样式 - 与文本同行 */
.inline-attachments {
  display: inline;
}

.inline-attachments .attachment-tag {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 1px 6px;
  margin-right: 6px;
  background: rgba(64, 158, 255, 0.15);
  border: 1px solid rgba(64, 158, 255, 0.3);
  border-radius: 4px;
  font-size: 12px;
  color: #409eff;
  vertical-align: middle;
}

.inline-attachments .attachment-tag .el-icon {
  font-size: 12px;
}

.message-actions {
  display: flex;
  gap: 8px;
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px solid #3d3d3d;
}

.message-content :deep(.code-block) {
  background: #1a1a1a;
  padding: 12px;
  border-radius: 8px;
  margin: 8px 0;
  overflow-x: auto;
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 12px;
  border: none;
}

.message-content :deep(.code-block)::-webkit-scrollbar {
  height: 6px;
}

.message-content :deep(.code-block)::-webkit-scrollbar-track {
  background: #1a1a1a;
}

.message-content :deep(.code-block)::-webkit-scrollbar-thumb {
  background: #444;
  border-radius: 3px;
}

.message-content :deep(.code-block)::-webkit-scrollbar-thumb:hover {
  background: #555;
}

.message-content :deep(.code-block .hljs-comment) {
  font-style: normal;
}

.message-content :deep(.code-block .hljs-emphasis),
.message-content :deep(.code-block em),
.message-content :deep(.code-block i) {
  font-style: normal;
}

.message-content :deep(.inline-code) {
  background: #2a2a2a;
  padding: 2px 6px;
  border-radius: 4px;
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 12px;
  border: none;
}

/* 思考过程部分样式 - 折叠状态 */
.thinking-section {
  margin-bottom: 12px;
  padding: 10px;
  background: #1e1e1e;
  border-left: 3px solid #888;
  border-radius: 0 6px 6px 0;
}

/* 流式思考过程 - 始终灰色 */
.thinking-section.streaming {
  border-left-color: #888;
}

.thinking-section.streaming pre {
  color: #888 !important;
}

.thinking-section.collapsed {
  padding: 6px 10px;
}

.thinking-section.collapsed .thinking-content {
  display: none;
}

.thinking-header {
  font-size: 12px;
  font-weight: 600;
  color: #888;
  display: flex;
  align-items: center;
  gap: 6px;
  cursor: pointer;
  user-select: none;
}

.thinking-header:hover {
  color: #aaa;
}

.thinking-icon {
  font-size: 12px;
  color: #888;
}

.thinking-content {
  margin-top: 8px;
}

.thinking-content pre {
  margin: 0;
  color: #888 !important;
  font-size: 12px;
  line-height: 1.5;
}

/* 回答内容区域 - 始终保持白色 */
.content-section {
  margin-top: 4px;
}

/* 正式回答内容始终是白色 */
.content-section pre,
.content-section * {
  color: #fff !important;
}

/* 打字光标 */
.typing-cursor {
  display: inline-block;
  width: 2px;
  height: 1.2em;
  background: #fff;
  vertical-align: text-bottom;
  margin-left: 2px;
  animation: blink 0.8s ease-in-out infinite;
}

@keyframes blink {
  0%, 100% { 
    opacity: 1; 
  }
  50% { 
    opacity: 0.2; 
  }
}

.message-content :deep(.thinking-label) {
  font-size: 13px;
  font-weight: 600;
  color: #9c27b0;
  margin: 12px 0 8px 0;
  display: flex;
  align-items: center;
  gap: 6px;
}

/* 只对思考内容容器应用灰色样式 */
.message-content :deep(.thinking-content) {
  color: #666 !important;
}

.message-content :deep(.thinking-content) * {
  color: #666 !important;
}

/* 滚动条样式 */
.messages-container::-webkit-scrollbar {
  width: 8px;
}

.messages-container::-webkit-scrollbar-track {
  background: #1e1e1e;
}

.messages-container::-webkit-scrollbar-thumb {
  background: #444;
  border-radius: 4px;
}

.messages-container::-webkit-scrollbar-thumb:hover {
  background: #555;
}

/* ==================== 工具执行区域样式 ==================== */
.tool-executions-section {
  margin-bottom: 12px;
  padding: 10px;
  background: #1e1e1e;
  border-left: 3px solid #888;
  border-radius: 0 6px 6px 0;
}

.tool-executions-section.streaming {
  border-left-color: #888;
  background: #1e1e1e;
}

.tool-executions-header {
  font-size: 12px;
  font-weight: 600;
  color: #888;
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  user-select: none;
}

.tool-executions-header:hover {
  color: #aaa;
}

.tool-executions-section.streaming .tool-executions-header {
  color: #888;
}

.tool-icon {
  font-size: 14px;
}

.expand-icon {
  font-size: 10px;
  margin-left: auto;
}

.tool-executions-list {
  margin-top: 10px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.tool-execution-item {
  padding: 8px 10px;
  background: #252525;
  border-radius: 6px;
  border-left: 2px solid #666;
}

.tool-execution-item.success {
  border-left-color: #666;
}

.tool-execution-item.error {
  border-left-color: #666;
}

.tool-execution-item.running {
  border-left-color: #888;
}

.tool-execution-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
}

.tool-status-icon {
  font-size: 14px;
}

.loading-spinner {
  display: inline-block;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.tool-name {
  font-size: 12px;
  font-weight: 500;
  color: #888;
}

.tool-execution-args {
  margin-bottom: 4px;
}

.tool-execution-args code {
  font-size: 11px;
  color: #666;
  background: #1a1a1a;
  padding: 2px 6px;
  border-radius: 3px;
  display: inline-block;
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.tool-execution-result {
  margin-top: 6px;
  max-height: 150px;
  overflow-y: auto;
}

.tool-execution-result pre {
  font-size: 11px;
  color: #888;
  background: #1a1a1a;
  padding: 8px;
  border-radius: 4px;
  margin: 0;
  white-space: pre-wrap;
  word-break: break-all;
}

.tool-execution-result::-webkit-scrollbar {
  width: 4px;
}

.tool-execution-result::-webkit-scrollbar-thumb {
  background: #444;
  border-radius: 2px;
}

/* 滚动到底部按钮 */
.scroll-to-bottom {
  position: absolute;
  bottom: 24px;
  right: 24px;
  width: 40px;
  height: 40px;
  background: #409eff;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  box-shadow: 0 2px 12px rgba(64, 158, 255, 0.4);
  transition: all 0.3s ease;
  z-index: 10;
}

.scroll-to-bottom:hover {
  background: #66b1ff;
  transform: translateY(-2px);
  box-shadow: 0 4px 16px rgba(64, 158, 255, 0.6);
}

.scroll-to-bottom:active {
  transform: translateY(0);
}

.scroll-to-bottom .el-icon {
  font-size: 20px;
  color: #fff;
}

/* 淡入淡出动画 */
.fade-enter-active, .fade-leave-active {
  transition: opacity 0.3s ease, transform 0.3s ease;
}

.fade-enter-from, .fade-leave-to {
  opacity: 0;
  transform: translateY(10px);
}
</style>
