<template>
  <div class="execution-bubble" :class="bubbleClass">
    <div class="bubble-header">
      <span class="bubble-icon">{{ bubbleIcon }}</span>
      <span class="bubble-label">{{ record.label || record.tool_name }}</span>
      <span v-if="record.execution_time_s" class="exec-time">{{ formatTime(record.execution_time_s) }}</span>
    </div>
    <div class="bubble-content" :class="{ 'code-content': isCodeContent }">
      <!-- 文件路径类型 -->
      <div v-if="record.type === 'file_path'" class="file-path-content">
        <code>{{ displayContent }}</code>
      </div>

      <!-- 代码内容类型 -->
      <div v-else-if="record.type === 'code'" class="code-block-content">
        <div v-if="record.language" class="code-language">{{ record.language }}</div>
        <pre><code>{{ displayContent }}</code></pre>
      </div>

      <!-- 结论类型 - 支持代码块显示 -->
      <div v-else-if="record.type === 'conclusion'" class="conclusion-content">
        <template v-for="(part, index) in parsedContent" :key="index">
          <!-- 文本部分 -->
          <div v-if="part.type === 'text'" class="text-part">
            {{ part.content }}
          </div>
          <!-- 代码块部分 -->
          <div v-else-if="part.type === 'code'" class="code-block-in-conclusion">
            <div v-if="part.language" class="code-language">{{ part.language }}</div>
            <pre><code>{{ part.content }}</code></pre>
          </div>
        </template>
      </div>

      <!-- 错误类型 -->
      <div v-else-if="record.type === 'error'" class="error-content">
        {{ displayContent }}
      </div>

      <!-- 参数摘要类型 -->
      <div v-else-if="record.type === 'args'" class="args-content">
        {{ displayContent }}
      </div>

      <!-- 迭代次数类型 -->
      <div v-else-if="record.type === 'iteration'" class="iteration-content">
        {{ displayContent }}
      </div>

      <!-- AI内容类型 -->
      <div v-else-if="record.type === 'ai_content'" class="ai-content">
        {{ displayContent }}
      </div>

      <!-- 工具开始类型 -->
      <div v-else-if="record.type === 'tool_start'" class="tool-start-content">
        {{ displayContent }}
      </div>

      <!-- 工具结果类型 -->
      <div v-else-if="record.type === 'tool_result'" class="tool-result-content">
        {{ displayContent }}
      </div>

      <!-- Agent节点类型 -->
      <div v-else-if="record.type === 'agent_node'" class="agent-node-content">
        <span class="node-type-badge">{{ record.node_type }}</span>
        {{ displayContent }}
      </div>

      <!-- 默认内容 -->
      <div v-else class="default-content">
        {{ displayContent || record.result_summary }}
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, watch, onUnmounted } from 'vue'

const props = defineProps({
  record: {
    type: Object,
    required: true,
    default: () => ({
      type: 'default',
      tool_name: '',
      label: '',
      content: '',
      execution_time_s: 0,
      success: true,
      timestamp: ''
    })
  },
  // 是否禁用打字机效果（用于历史气泡）
  disableTypewriter: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['typewriter-complete'])

// 打字机效果相关
const displayContent = ref('')
let typewriterTimer = null
let currentCharIndex = 0

// 监听内容变化，启动打字机效果
watch(() => props.record.content, (newContent) => {
  if (newContent) {
    // 如果禁用打字机效果（历史气泡），直接显示完整内容
    if (props.disableTypewriter) {
      displayContent.value = newContent
      emit('typewriter-complete')
    } else {
      startTypewriter(newContent)
    }
  } else {
    displayContent.value = ''
    // 没有内容也触发完成
    emit('typewriter-complete')
  }
}, { immediate: true })

// 启动打字机效果
function startTypewriter(text) {
  // 清理之前的定时器
  stopTypewriter()

  displayContent.value = ''
  currentCharIndex = 0

  // 对于代码块，使用更快的速度
  const isCode = props.record.type === 'code'
  const speed = isCode ? 5 : 15  // 代码块5ms，其他15ms

  const chars = text.split('')

  typewriterTimer = setInterval(() => {
    if (currentCharIndex < chars.length) {
      displayContent.value += chars[currentCharIndex]
      currentCharIndex++
    } else {
      stopTypewriter()
      // 打字机效果完成，发出事件
      emit('typewriter-complete')
    }
  }, speed)
}

// 停止打字机效果
function stopTypewriter() {
  if (typewriterTimer) {
    clearInterval(typewriterTimer)
    typewriterTimer = null
  }
}

// 组件卸载时清理
onUnmounted(() => {
  stopTypewriter()
})

// 气泡类型对应的样式类
const bubbleClass = computed(() => {
  const type = props.record.type || 'default'
  const classes = []
  
  // 根据类型添加样式
  if (type === 'success' || props.record.success) {
    classes.push('success')
  }
  if (type === 'error' || !props.record.success) {
    classes.push('error')
  }
  if (type === 'file_path') {
    classes.push('file-path')
  }
  if (type === 'code') {
    classes.push('code')
  }
  if (type === 'conclusion') {
    classes.push('conclusion')
  }
  if (type === 'args') {
    classes.push('args')
  }
  if (type === 'iteration') {
    classes.push('iteration')
  }
  if (type === 'ai_content') {
    classes.push('ai-content-bubble')
  }
  if (type === 'tool_start') {
    classes.push('tool-start')
  }
  if (type === 'tool_result') {
    classes.push('tool-result')
  }
  if (type === 'agent_node') {
    classes.push('agent-node')
  }

  return classes
})

// 气泡图标
const bubbleIcon = computed(() => {
  const type = props.record.type || 'default'
  
  // 类型图标映射
  const typeIcons = {
    'success': '✅',
    'error': '❌',
    'file_path': '📄',
    'code': '💻',
    'conclusion': '🎯',
    'args': '📝',
    'tool_start': '🚀',
    'tool_result': '📋',
    'iteration': '🔄',
    'ai_content': '🤖',
    'agent_node': '🔷',
    'default': '🔧'
  }
  
  // 工具名称图标映射
  const toolIcons = {
    'write_file': '📝',
    'read_file': '📖',
    'execute_command': '⚡',
    'list_directory': '📁',
    'search_content': '🔍',
    'create_directory': '📂',
    'delete_file': '🗑️',
    'generate_tests': '🧪',
    'run_tests': '▶️',
    'search_symbol': '🔎',
    'get_code_references': '🔗',
    'run_verification_pipeline': '✅',
    'index_workspace': '📊',
    'get_call_graph': '📈',
    'get_file_outline': '📋',
    'verify_with_z3': '🧮'
  }
  
  // 优先使用类型图标
  if (typeIcons[type]) {
    return typeIcons[type]
  }
  
  // 其次使用工具图标
  return toolIcons[props.record.tool_name] || typeIcons['default']
})

// 是否是代码内容
const isCodeContent = computed(() => {
  return props.record.type === 'code'
})

// 解析内容，检测是否包含代码块
const parsedContent = computed(() => {
  const content = displayContent.value
  if (!content) return []

  // 只对结论气泡进行代码块检测
  if (props.record.type !== 'conclusion') {
    return [{ type: 'text', content }]
  }

  // 检测 Markdown 代码块格式：```language\ncode\n```
  const codeBlockRegex = /```(\w*)\n([\s\S]*?)```/g
  const parts = []
  let lastIndex = 0
  let match

  while ((match = codeBlockRegex.exec(content)) !== null) {
    // 添加代码块之前的文本
    if (match.index > lastIndex) {
      const textContent = content.substring(lastIndex, match.index).trim()
      if (textContent) {
        parts.push({ type: 'text', content: textContent })
      }
    }

    // 添加代码块
    const language = match[1] || ''
    const code = match[2].trim()
    if (code) {
      parts.push({ type: 'code', content: code, language })
    }

    lastIndex = match.index + match[0].length
  }

  // 添加最后一个代码块之后的文本
  if (lastIndex < content.length) {
    const textContent = content.substring(lastIndex).trim()
    if (textContent) {
      parts.push({ type: 'text', content: textContent })
    }
  }

  // 如果没有找到代码块，返回普通文本
  if (parts.length === 0) {
    return [{ type: 'text', content }]
  }

  return parts
})

// 格式化时间
function formatTime(seconds) {
  if (!seconds || seconds === 0) return ''
  if (seconds < 1) {
    return `${Math.round(seconds * 1000)}ms`
  }
  return `${seconds.toFixed(2)}s`
}
</script>

<style scoped>
.execution-bubble {
  background: #252525;
  border-radius: 8px;
  padding: 10px 12px;
  margin-bottom: 6px;
  border-left: 3px solid #67c23a;
  transition: all 0.2s ease;
}

.execution-bubble.error {
  border-left-color: #f56c6c;
}

.execution-bubble.success {
  border-left-color: #67c23a;
}

.execution-bubble.file-path {
  border-left-color: #409eff;
  background: rgba(64, 158, 255, 0.05);
}

.execution-bubble.code {
  border-left-color: #9c27b0;
  background: #1a1a2e;
}

/* 结论气泡 - 稍微突出的样式 */
.execution-bubble.conclusion {
  border-left-color: #e6a23c;
  border-left-width: 4px;
  background: rgba(230, 162, 60, 0.08);
  padding: 14px 14px;
  margin-top: 10px;
  margin-bottom: 10px;
}

.execution-bubble.args {
  border-left-color: #909399;
  background: rgba(144, 147, 153, 0.05);
}

.bubble-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
}

.bubble-icon {
  font-size: 14px;
}

.bubble-label {
  color: #e0e0e0;
  font-weight: 500;
  font-size: 13px;
  flex: 1;
}

.exec-time {
  color: #888;
  font-size: 11px;
  background: #333;
  padding: 2px 6px;
  border-radius: 4px;
}

.bubble-content {
  color: #aaa;
  font-size: 12px;
  line-height: 1.5;
}

/* 文件路径样式 */
.file-path-content code {
  background: #1a1a1a;
  padding: 4px 8px;
  border-radius: 4px;
  font-family: 'Consolas', 'Monaco', monospace;
  color: #409eff;
  font-size: 12px;
}

/* 代码块样式 */
.code-block-content {
  background: #1a1a1a;
  border-radius: 6px;
  overflow: hidden;
}

.code-language {
  background: #333;
  color: #aaa;
  font-size: 10px;
  padding: 2px 8px;
  border-bottom: 1px solid #444;
}

.code-block-content pre {
  margin: 0;
  padding: 10px;
  overflow-x: auto;
}

.code-block-content code {
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 12px;
  color: #e0e0e0;
  white-space: pre-wrap;
  word-break: break-word;
}

/* 结论样式 */
.conclusion-content {
  color: #e6a23c;
  font-weight: 500;
  font-size: 13px;
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-word;
}

/* 结论中的文本部分 */
.text-part {
  margin-bottom: 10px;
  color: #f0f0f0;
}

/* 结论中的代码块 */
.code-block-in-conclusion {
  background: #1a1a1a;
  border-radius: 6px;
  overflow: hidden;
  margin-bottom: 10px;
  border: 1px solid #333;
}

.code-block-in-conclusion .code-language {
  background: #333;
  color: #aaa;
  font-size: 10px;
  padding: 2px 8px;
  border-bottom: 1px solid #444;
}

.code-block-in-conclusion pre {
  margin: 0;
  padding: 10px;
  overflow-x: auto;
}

.code-block-in-conclusion code {
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 12px;
  color: #e0e0e0;
  white-space: pre-wrap;
  word-break: break-word;
}

/* 错误样式 */
.error-content {
  color: #f56c6c;
}

/* 参数摘要样式 */
.args-content {
  color: #909399;
  font-style: italic;
}

/* 迭代次数样式 */
.execution-bubble.iteration {
  border-left-color: #409eff;
  background: rgba(64, 158, 255, 0.1);
}

.iteration-content {
  color: #409eff;
  font-weight: 500;
}

/* AI内容样式 */
.execution-bubble.ai-content-bubble {
  border-left-color: #9c27b0;
  background: rgba(156, 39, 176, 0.08);
}

.ai-content {
  color: #ce93d8;
  line-height: 1.6;
}

/* 工具开始样式 */
.execution-bubble.tool-start {
  border-left-color: #ff9800;
  background: rgba(255, 152, 0, 0.08);
}

.tool-start-content {
  color: #ffcc80;
}

/* 工具结果样式 */
.execution-bubble.tool-result {
  border-left-color: #4caf50;
  background: rgba(76, 175, 80, 0.08);
}

.tool-result-content {
  color: #a5d6a7;
}

/* Agent节点样式 */
.execution-bubble.agent-node {
  border-left-color: #2196f3;
  background: rgba(33, 150, 243, 0.1);
  border-left-width: 4px;
  margin-top: 12px;
  margin-bottom: 8px;
}

.agent-node-content {
  color: #64b5f6;
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: 8px;
}

.node-type-badge {
  background: rgba(33, 150, 243, 0.2);
  color: #90caf9;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
}

/* 默认内容样式 */
.default-content {
  color: #9aa0a6;
  word-break: break-word;
}
</style>
