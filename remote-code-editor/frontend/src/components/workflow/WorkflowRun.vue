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
    <el-input v-model="inputValue" type="textarea" :rows="6" placeholder="输入内容或 JSON" />
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
      <!-- 执行结果 -->
      <div v-if="resultHtml" class="message assistant">
        <div class="message-header">
          <span class="role-name">工作流</span>
          <span v-if="execTime" class="execution-time">{{ execTime }}</span>
        </div>
        <div class="message-content">
          <div v-html="resultHtml"></div>
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
      <div v-if="!resultHtml && !errorMsg && !isRunning" class="empty-result">
        执行结果将显示在这里
      </div>
    </div>
  </aside>
</template>

<script setup>
import { ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import hljs from 'highlight.js'
import 'highlight.js/styles/tokyo-night-dark.css'

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

const emit = defineEmits(['run'])

// 双向绑定数据
const inputValue = ref('')
const resultHtml = ref('')
const errorMsg = ref('')
const execTime = ref('')
const isRunning = ref(false)

// 监听父组件传入的值变化
watch(() => props.graphJson, () => {
  // 可选：清空结果当图数据变化时
})

// 暴露方法给父组件调用更新状态
function setRunning(running) {
  isRunning.value = running
}

function setResult(html, time) {
  resultHtml.value = html
  execTime.value = time
  errorMsg.value = ''
}

function setError(msg) {
  errorMsg.value = msg
  resultHtml.value = ''
  execTime.value = ''
}

function clearResult() {
  resultHtml.value = ''
  errorMsg.value = ''
  execTime.value = ''
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
function formatAndSetResult(result, executionTimeMs) {
  const resultText = typeof result === 'string'
    ? result
    : JSON.stringify(result, null, 2)
  resultHtml.value = formatMessage(resultText)

  if (executionTimeMs) {
    execTime.value = `${executionTimeMs}ms`
  }
}

// 暴露方法和状态给父组件
defineExpose({
  inputValue,
  resultHtml,
  errorMsg,
  execTime,
  isRunning,
  setRunning,
  setResult,
  setError,
  clearResult,
  formatAndSetResult
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
  max-height: 400px;
}

.workflow-result-running {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
  color: #9aa0a6;
}

.workflow-result-running .result-header {
  display: flex;
  align-items: center;
  gap: 8px;
}

.workflow-result-running .status-icon {
  animation: spin 1s linear infinite;
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
</style>
