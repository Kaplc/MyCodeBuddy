<template>
  <aside class="workflow-run">
    <div class="section-title">
      运行
      <span v-if="edges.length > 0" class="connection-badge">{{ edges.length }} 条连接</span>
      <span v-else class="connection-warning">未连接</span>
    </div>
    <div v-if="edges.length === 0" class="connection-hint">
      提示：从节点的右侧（输出）拖线到左侧（输入）来连接节点
    </div>
    <el-input ref="inputRef" v-model="inputValue" type="textarea" :rows="6" placeholder="输入内容或 JSON" />

    <el-button size="small" type="success" :disabled="isRunning" @click="handleRun">
      {{ isRunning ? '运行中...' : '运行工作流' }}
    </el-button>
    <!-- 对话式结果显示 -->
    <div class="workflow-result-display">
      <!-- 运行状态 -->
      <div v-if="isRunning" class="workflow-result-running">
        <div class="result-header">
          <span class="status-icon">⏳</span>
          <span>工作流执行中...</span>
        </div>
        <!-- 执行详情 - 基于最新气泡 -->
        <div class="execution-status">
          <div class="status-row" v-if="currentBubbleStatus.currentNode">
            <span class="status-label">当前节点</span>
            <span class="status-value node-name">
              <span class="node-type-tag">{{ currentBubbleStatus.currentNodeType }}</span>
              {{ currentBubbleStatus.currentNode }}
            </span>
          </div>
          <div class="status-row" v-if="currentBubbleStatus.iteration">
            <span class="status-label">迭代进度</span>
            <span class="status-value">{{ currentBubbleStatus.iteration }}</span>
          </div>
          <div class="status-row" v-if="currentBubbleStatus.currentTool">
            <span class="status-label">当前工具</span>
            <span class="status-value tool-name">{{ currentBubbleStatus.currentTool }}</span>
          </div>
          <div class="status-row" v-if="currentBubbleStatus.toolResult">
            <span class="status-label">工具结果</span>
            <span class="status-value tool-result" :class="{ 'tool-error': !currentBubbleStatus.toolSuccess }">
              {{ currentBubbleStatus.toolResult }}
            </span>
          </div>
          <div class="status-row" v-if="currentBubbleStatus.aiContent">
            <span class="status-label">AI 响应</span>
            <span class="status-value ai-content">{{ currentBubbleStatus.aiContent }}</span>
          </div>
        </div>
      </div>
      <!-- 用户输入 -->
      <div v-if="inputValue" class="message user">
        <div class="message-header">
          <span class="role-name">你</span>
        </div>
        <div class="message-content">
          <pre>{{ inputValue }}</pre>
        </div>
      </div>

      <!-- 迭代过程显示 - 简洁版 -->
      <div v-if="iterations.length > 0" class="iterations-compact">
        <div v-for="iter in iterations" :key="iter.iteration" class="iteration-row">
          <span class="iter-num">{{ iter.iteration }}</span>
          <div class="tool-tags">
            <span v-for="(tool, idx) in iter.tools" :key="idx" 
                  :class="['tool-tag', tool.success ? 'success' : 'error']"
                  :title="getTooltipContent(tool)">
              {{ tool.name }}
            </span>
          </div>
        </div>
      </div>

      <!-- 气泡流显示 - 结论大气泡 -->
      <div v-if="bubbleRecords.length > 0" class="bubble-flow-container" ref="bubbleContainer">
        <ExecutionBubble
          v-for="(bubble, index) in bubbleRecords"
          :key="index"
          :record="bubble"
          :disable-typewriter="bubble._isHistory"
          @typewriter-complete="onBubbleTypewriterComplete(index)"
        />
      </div>

      <!-- 执行结果 - 打字机效果 -->
      <div v-if="typewriterText || resultHtml" class="message assistant">
        <div class="message-header">
          <span class="role-name">工作流</span>
          <span v-if="execTime" class="execution-time">{{ execTime }}</span>
        </div>
        <div class="message-content">
          <div v-if="typewriterText" class="typewriter-result">
            <pre>{{ typewriterText }}<span v-if="isTyping" class="cursor">|</span></pre>
          </div>
          <div v-else-if="resultHtml" v-html="resultHtml"></div>
        </div>
      </div>

      <!-- 错误结果 -->
      <div v-if="errorMsg" class="message error">
        <div class="message-header">
          <span class="role-name">错误</span>
        </div>
        <div class="message-content">
          <pre>{{ errorMsg }}</pre>
        </div>
      </div>
      <!-- 空状态 -->
      <div v-if="!resultHtml && !errorMsg && !isRunning && iterations.length === 0 && !typewriterText" class="empty-result">
        执行结果将显示在这里
      </div>
    </div>
  </aside>
</template>

<script setup>
import { ref, watch, onUnmounted, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import hljs from 'highlight.js'
import 'highlight.js/styles/tokyo-night-dark.css'
import ExecutionBubble from './ExecutionBubble.vue'

const props = defineProps({
  edges: {
    type: Array,
    default: () => []
  },
  currentWorkflowId: {
    type: String,
    default: ''
  },
  graphJson: {
    type: String,
    default: ''
  }
})

const emit = defineEmits(['run', 'bubble-complete'])

// 双向绑定数据
const inputValue = ref('')
const resultHtml = ref('')
const errorMsg = ref('')
const execTime = ref('')
const isRunning = ref(false)
const iterations = ref([])  // 迭代历史
const typewriterText = ref('')  // 打字机文本
const isTyping = ref(false)  // 是否正在打字
const currentNode = ref('')  // 当前执行的节点ID
const executionDetails = ref(null)  // 执行详情（迭代次数、状态消息等）
const bubbleRecords = ref([])  // 气泡流记录
const bubbleContainer = ref(null)  // 气泡容器DOM引用
const inputRef = ref(null)  // 输入框DOM引用

// 聚焦输入框
function focusInput() {
  inputRef.value?.focus()
}

// 当前气泡状态 - 用于右侧状态面板显示
const currentBubbleStatus = ref({
  currentNode: '',
  currentNodeType: '',
  iteration: '',
  iterationNum: 0,
  maxIterations: 0,
  currentTool: '',
  toolArgs: '',
  toolResult: '',
  toolSuccess: true,
  toolTime: 0,
  aiContent: '',
  isCompleted: false,
  conclusion: ''
})

// 打字机相关
let typewriterTimer = null
let typewriterQueue = []  // 待显示的文本队列
let currentCharIndex = 0

// 监听父组件传入的值变化
watch(() => props.graphJson, () => {
  // 可选：清空结果当图数据变化时
})

// 暴露方法给父组件调用更新状态
function setRunning(running) {
  isRunning.value = running
  if (running) {
    // 开始运行时清空
    typewriterText.value = ''
    isTyping.value = false
  }
}

function setResult(html, time) {
  resultHtml.value = html
  execTime.value = time
  errorMsg.value = ''
}

function setExecutionTime(time) {
  execTime.value = time
}

function setError(msg) {
  errorMsg.value = msg
  resultHtml.value = ''
  execTime.value = ''
  iterations.value = []
  stopTypewriter()
}

function clearResult() {
  resultHtml.value = ''
  errorMsg.value = ''
  execTime.value = ''
  iterations.value = []
  stopTypewriter()
}

// 设置迭代历史（供父组件调用）
function setIterations(iterationHistory) {
  iterations.value = iterationHistory || []
}

// 设置当前执行节点（供父组件调用）
function setCurrentNode(nodeId) {
  currentNode.value = nodeId || ''
}

// 设置执行详情（供父组件调用）
function setExecutionDetails(details) {
  executionDetails.value = details
}

// 滚动到气泡容器底部
function scrollToBottom() {
  nextTick(() => {
    if (bubbleContainer.value) {
      bubbleContainer.value.scrollTop = bubbleContainer.value.scrollHeight
    }
  })
}

// 气泡打字机效果完成回调
function onBubbleTypewriterComplete(index) {
  // 只有最后一个气泡完成才通知父组件
  if (index === bubbleRecords.value.length - 1) {
    emit('bubble-complete')
  }
}

// 添加单个气泡记录（供父组件调用，实时添加）
function addBubbleRecord(record) {
  if (record) {
    bubbleRecords.value.push(record)
    scrollToBottom()

    // 根据气泡类型更新右侧状态面板
    updateStatusFromBubble(record)
  }
}

// 根据气泡更新状态面板
function updateStatusFromBubble(record) {
  if (!record) return

  const type = record.type

  // Agent节点气泡 - 更新当前节点
  if (type === 'agent_node') {
    currentBubbleStatus.value = {
      ...currentBubbleStatus.value,
      currentNode: record.label,
      currentNodeType: record.node_type,
      // 重置工具和AI状态
      currentTool: '',
      toolResult: '',
      aiContent: ''
    }
  }

  // 迭代气泡 - 更新迭代进度
  if (type === 'iteration') {
    const match = record.label?.match(/(\d+)\s*\/\s*(\d+)/)
    if (match) {
      currentBubbleStatus.value = {
        ...currentBubbleStatus.value,
        iteration: `${match[1]} / ${match[2]}`,
        iterationNum: parseInt(match[1]),
        maxIterations: parseInt(match[2])
      }
    }
  }

  // AI内容气泡 - 更新AI响应
  if (type === 'ai_content') {
    currentBubbleStatus.value = {
      ...currentBubbleStatus.value,
      aiContent: record.content,
      currentTool: '', // 清空工具显示
      toolResult: ''
    }
  }

  // 工具开始气泡 - 更新当前工具
  if (type === 'tool_start') {
    currentBubbleStatus.value = {
      ...currentBubbleStatus.value,
      currentTool: record.tool_name || record.label,
      toolArgs: record.content,
      toolResult: '' // 清空之前的结果
    }
  }

  // 工具结果气泡 - 更新工具结果
  if (type === 'tool_result') {
    currentBubbleStatus.value = {
      ...currentBubbleStatus.value,
      toolResult: record.content || record.result_summary,
      toolSuccess: record.success,
      toolTime: record.execution_time_s
    }
  }

  // 结论气泡 - 标记完成
  if (type === 'conclusion') {
    currentBubbleStatus.value = {
      ...currentBubbleStatus.value,
      isCompleted: true,
      conclusion: record.content
    }
  }
}

// 设置气泡记录（供父组件调用，批量设置历史记录）
function setBubbleRecords(records) {
  // 为历史气泡添加标记，禁用打字机效果
  bubbleRecords.value = (records || []).map(record => ({
    ...record,
    _isHistory: true  // 标记为历史气泡
  }))
  scrollToBottom()
}

// 格式化工具结果
function formatToolResult(resultStr) {
  try {
    const result = JSON.parse(resultStr)
    if (result.success) {
      return result.message || result.path || JSON.stringify(result)
    }
    return result.error || resultStr
  } catch {
    return resultStr
  }
}

// 停止打字机
function stopTypewriter() {
  if (typewriterTimer) {
    clearInterval(typewriterTimer)
    typewriterTimer = null
  }
  isTyping.value = false
  typewriterQueue = []
  currentCharIndex = 0
}

// 打字机效果显示文本
function startTypewriter(text) {
  if (!text) {
    typewriterText.value = ''
    return
  }
  
  // 停止之前的打字机
  stopTypewriter()
  
  typewriterText.value = ''
  currentCharIndex = 0
  isTyping.value = true
  
  const chars = text.split('')
  
  typewriterTimer = setInterval(() => {
    if (currentCharIndex < chars.length) {
      typewriterText.value += chars[currentCharIndex]
      currentCharIndex++
    } else {
      stopTypewriter()
    }
  }, 15)  // 15ms 一个字符
}

// 从工具结果中提取关键内容
function extractToolResult(tool) {
  if (!tool || !tool.result) return null
  
  try {
    const parsed = typeof tool.result === 'string' ? JSON.parse(tool.result) : tool.result
    
    // 常见字段提取
    const keyFields = ['content', 'output', 'result', 'message', 'data', 'text']
    for (const key of keyFields) {
      if (parsed[key] && typeof parsed[key] === 'string') {
        return parsed[key]
      }
    }
    
    // 如果是文件操作，返回路径信息
    if (parsed.path) {
      return `文件: ${parsed.path}`
    }
    
    // 如果是列表操作，返回数量
    if (parsed.items && Array.isArray(parsed.items)) {
      return `找到 ${parsed.items.length} 项`
    }
    
    // 如果成功，返回成功标记
    if (parsed.success === true) {
      return '✓ 完成'
    }
    
    return null
  } catch {
    return null
  }
}

// 从参数中提取关键内容
function extractToolArgs(tool) {
  if (!tool || !tool.args) return ''
  
  const args = tool.args
  
  // write_file 的 content
  if (args.content) {
    const content = args.content
    return content.length > 100 ? content.substring(0, 100) + '...' : content
  }
  
  // 其他工具的 path
  if (args.path) {
    return `路径: ${args.path}`
  }
  
  // 搜索查询
  if (args.query) {
    return `查询: ${args.query}`
  }
  
  // 命令
  if (args.command) {
    return `命令: ${args.command}`
  }
  
  return ''
}

// 获取工具提示内容
function getTooltipContent(tool) {
  const args = extractToolArgs(tool)
  const result = extractToolResult(tool)
  let tip = `${tool.name} (${tool.time_ms}ms)`
  if (args) tip += `\n参数: ${args}`
  if (result) tip += `\n结果: ${result}`
  return tip
}

// 格式化消息内容（带代码高亮）
function formatMessage(content) {
  if (!content) return ''

  // 转义HTML
  let html = content
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')

  // 代码块高亮
  html = html.replace(/```(\w*)\n([\s\S]*?)```/g, (match, lang, code) => {
    let highlighted = code
    const language = lang || 'plaintext'
    try {
      if (hljs && hljs.getLanguage(language)) {
        highlighted = hljs.highlight(code, { language }).value
      } else {
        highlighted = hljs ? hljs.highlightAuto(code).value : code
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

// 从工作流返回结果中提取用于展示的文本（优先使用 output）
function extractDisplayText(result) {
  if (result == null) return ''

  if (typeof result === 'string') {
    return result
  }

  // 数组：如果都是原始值，则按行拼接
  if (Array.isArray(result)) {
    if (result.every(item => ['string', 'number', 'boolean'].includes(typeof item))) {
      return result.join('\n')
    }
  }

  const candidateKeys = ['output', 'result', 'message', 'content']
  for (const key of candidateKeys) {
    if (Object.prototype.hasOwnProperty.call(result, key) && result[key] != null) {
      const value = result[key]
      if (typeof value === 'string') {
        return value
      }
      try {
        return JSON.stringify(value, null, 2)
      } catch (e) {
        return String(value)
      }
    }
  }

  try {
    return JSON.stringify(result, null, 2)
  } catch (e) {
    return String(result)
  }
}

// 点击运行按钮
function handleRun() {
  if (isRunning.value) return

  // 验证工作流
  if (!props.currentWorkflowId) {
    try {
      const graph = JSON.parse(props.graphJson || '{}')
      if (!graph.nodes || graph.nodes.length === 0) {
        ElMessage.warning('请先在工作流编辑器中添加节点，或选择一个已保存的工作流')
        return
      }
    } catch (e) {
      ElMessage.warning('请先在工作流编辑器中添加节点，或选择一个已保存的工作流')
      return
    }
  }

  // 解析输入
  let inputValueParsed = inputValue.value
  try {
    inputValueParsed = JSON.parse(inputValue.value)
  } catch (error) {
    // 使用文本输入
  }

  // 清空之前的结果
  iterations.value = []
  resultHtml.value = ''
  typewriterText.value = ''
  errorMsg.value = ''
  bubbleRecords.value = []  // 清理旧的气泡消息

  // 重置气泡状态
  currentBubbleStatus.value = {
    currentNode: '',
    currentNodeType: '',
    iteration: '',
    iterationNum: 0,
    maxIterations: 0,
    currentTool: '',
    toolArgs: '',
    toolResult: '',
    toolSuccess: true,
    toolTime: 0,
    aiContent: '',
    isCompleted: false,
    conclusion: ''
  }

  // 触发运行事件
  emit('run', {
    input: inputValueParsed,
    buildGraph: () => {
      try {
        return JSON.parse(props.graphJson || '{}')
      } catch (e) {
        return {}
      }
    }
  })
}

// 格式化结果并设置（供父组件调用）
function formatAndSetResult(result, executionTimeMs, iterationHistory = []) {
  // 设置迭代历史
  iterations.value = iterationHistory || []
  
  // 提取最终结果显示
  const displayText = extractDisplayText(result)
  
  if (executionTimeMs) {
    execTime.value = `${executionTimeMs}ms`
  } else {
    execTime.value = ''
  }

  // 将最终结论显示为一个突出的大气泡
  if (displayText && typeof displayText === 'string' && displayText.trim()) {
    const conclusionBubble = {
      type: 'conclusion',
      tool_name: 'workflow_result',
      label: '工作流执行结果',
      content: displayText,
      execution_time_s: (executionTimeMs || 0) / 1000.0,
      success: true,
      timestamp: new Date().toISOString()
    }
    bubbleRecords.value.push(conclusionBubble)
    scrollToBottom()
  }
}

// 组件卸载时清理
onUnmounted(() => {
  stopTypewriter()
})

// 暴露方法和状态给父组件
defineExpose({
  inputValue,
  resultHtml,
  errorMsg,
  execTime,
  isRunning,
  iterations,
  currentNode,
  executionDetails,
  bubbleRecords,
  bubbleContainer,
  setRunning,
  setResult,
  setExecutionTime,
  setError,
  clearResult,
  formatAndSetResult,
  setIterations,
  setCurrentNode,
  setExecutionDetails,
  addBubbleRecord,
  setBubbleRecords,
  scrollToBottom,
  focusInput
})

</script>

<style scoped>
.workflow-run {
  background: #1e1e1e;
  border: 1px solid #333;
  border-radius: 12px;
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.section-title {
  font-weight: 600;
  margin-bottom: 8px;
}

.workflow-result-display {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 8px;
  background: #1a1a1a;
  border-radius: 8px;
  min-height: 200px;
  max-height: 800px;
}

/* 气泡流容器 */
.bubble-flow-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 12px 8px;
  margin-top: 12px;
  overflow-y: auto;
}

.workflow-result-running {
  display: flex;
  flex-direction: column;
  padding: 12px;
  background: #252525;
  border-radius: 8px;
  gap: 12px;
}

.workflow-result-running .result-header {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #409eff;
  font-weight: 500;
}

.workflow-result-running .status-icon {
  animation: spin 1s linear infinite;
}

/* 执行状态详情 */
.execution-status {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 10px;
  background: #1a1a1a;
  border-radius: 6px;
  border-left: 3px solid #409eff;
}

.status-row {
  display: flex;
  align-items: flex-start;
  gap: 12px;
}

.status-label {
  color: #888;
  font-size: 12px;
  min-width: 60px;
}

.status-value {
  color: #e0e0e0;
  font-size: 13px;
}

.status-value.tool-name {
  color: #67c23a;
  font-family: monospace;
  background: rgba(103, 194, 58, 0.1);
  padding: 2px 6px;
  border-radius: 4px;
}

.status-value.ai-waiting {
  color: #e6a23c;
  animation: pulse 1.5s ease-in-out infinite;
}

.status-value.node-name {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #64b5f6;
  font-weight: 500;
}

.node-type-tag {
  background: rgba(33, 150, 243, 0.2);
  color: #90caf9;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 10px;
  font-weight: 600;
  text-transform: uppercase;
}

.status-value.ai-content {
  color: #a0cfff;
  background: rgba(64, 158, 255, 0.1);
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  line-height: 1.5;
  white-space: pre-wrap;
  word-break: break-word;
}

.status-value.tool-result {
  color: #67c23a;
  background: rgba(103, 194, 58, 0.1);
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-family: monospace;
  line-height: 1.5;
  white-space: pre-wrap;
  word-break: break-word;
}

.status-value.tool-error {
  color: #f56c6c;
  background: rgba(245, 108, 108, 0.1);
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.message {
  padding: 10px;
  border-radius: 8px;
  background: #252525;
}

.message.user {
  background: #2a3a4a;
}

.message.assistant {
  background: #252525;
  border-left: 3px solid #4caf50;
}

.message.error {
  background: #3a2525;
  border-left: 3px solid #f44336;
}

.message-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
  font-size: 12px;
}

.role-name {
  font-weight: 600;
  color: #4fc3f7;
}

.message.user .role-name {
  color: #81c784;
}

.message.error .role-name {
  color: #e57373;
}

.execution-time {
  color: #888;
  font-size: 11px;
}

.message-content {
  font-size: 13px;
  line-height: 1.5;
  color: #e0e0e0;
  word-break: break-word;
}

.message-content pre {
  margin: 0;
  white-space: pre-wrap;
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 12px;
}

.message-content :deep(.code-block) {
  background: #1e1e1e;
  border: 1px solid #333;
  border-radius: 6px;
  padding: 10px;
  margin: 8px 0;
  overflow-x: auto;
}

.message-content :deep(.inline-code) {
  background: #2d2d2d;
  padding: 2px 6px;
  border-radius: 4px;
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 12px;
}

.empty-result {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #666;
  font-size: 13px;
}

.connection-badge {
  font-size: 12px;
  background: #4caf50;
  color: white;
  padding: 2px 8px;
  border-radius: 10px;
  margin-left: 8px;
  font-weight: normal;
}

.connection-warning {
  font-size: 12px;
  background: #ff9800;
  color: white;
  padding: 2px 8px;
  border-radius: 10px;
  margin-left: 8px;
  font-weight: normal;
}

.connection-hint {
  font-size: 12px;
  color: #888;
  padding: 8px;
  background: #2a2a2a;
  border-radius: 6px;
  margin-bottom: 8px;
}

/* 简洁迭代样式 */
.iterations-compact {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 8px;
  background: #1e1e1e;
  border-radius: 6px;
}

.iteration-row {
  display: flex;
  align-items: center;
  gap: 10px;
}

.iter-num {
  width: 20px;
  height: 20px;
  background: #333;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 11px;
  color: #888;
  flex-shrink: 0;
}

.tool-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.tool-tag {
  padding: 3px 10px;
  border-radius: 12px;
  font-size: 11px;
  font-family: 'Consolas', 'Monaco', monospace;
  cursor: default;
  white-space: nowrap;
}

.tool-tag.success {
  background: #1b5e20;
  color: #81c784;
}

.tool-tag.error {
  background: #b71c1c;
  color: #ef9a9a;
}

/* 打字机效果 */
.typewriter-result pre {
  margin: 0;
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 13px;
  white-space: pre-wrap;
  word-break: break-word;
}

.cursor {
  animation: blink 0.8s infinite;
  color: #4fc3f7;
}

@keyframes blink {
  0%, 50% { opacity: 1; }
  51%, 100% { opacity: 0; }
}

/* 暗色风格滚动条 */
.workflow-result-display::-webkit-scrollbar,
.bubble-flow-container::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

.workflow-result-display::-webkit-scrollbar-track,
.bubble-flow-container::-webkit-scrollbar-track {
  background: #1a1a1a;
  border-radius: 4px;
}

.workflow-result-display::-webkit-scrollbar-thumb,
.bubble-flow-container::-webkit-scrollbar-thumb {
  background: #3a3a3a;
  border-radius: 4px;
  transition: background 0.2s ease;
}

.workflow-result-display::-webkit-scrollbar-thumb:hover,
.bubble-flow-container::-webkit-scrollbar-thumb:hover {
  background: #4a4a4a;
}

/* Firefox 滚动条样式 */
.workflow-result-display,
.bubble-flow-container {
  scrollbar-width: thin;
  scrollbar-color: #3a3a3a #1a1a1a;
}
</style>
