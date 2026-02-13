<template>
  <footer class="status-bar">
    <!-- 左侧：文件信息 -->
    <div class="status-left">
      <span v-if="currentFile" class="status-item">
        <el-icon><Document /></el-icon>
        {{ language }}
      </span>
      <span v-if="currentFile" class="status-item">
        UTF-8
      </span>
      <span v-if="currentFile" class="status-item">
        <el-icon><Position /></el-icon>
        行 {{ cursorPosition?.line || 1 }}, 列 {{ cursorPosition?.column || 1 }}
      </span>
      <span v-if="currentFile" class="status-item">
        共 {{ totalLines || 0 }} 行
      </span>
    </div>
    
    <!-- 右侧：连接状态 + Git -->
    <div class="status-right">
      <div class="status-item branch" title="分支">
        <el-icon><Share /></el-icon>
        <span>main</span>
      </div>
      
      <!-- AI连接状态 -->
      <div 
        ref="aiStatusRef"
        class="status-item connection ai" 
        :class="[aiStatus, { clickable: true }]" 
        :title="aiTitle"
        @click="showAiDetail"
      >
        <span class="status-dot"></span>
        <span>AI</span>
      </div>
      
      <!-- 服务器连接状态 -->
      <div 
        class="status-item connection server" 
        :class="[serverStatus, { clickable: true }]" 
        :title="serverTitle"
        @click="handleServerClick"
      >
        <span class="status-dot"></span>
        <span>Server</span>
        <span v-if="serverStatus === 'connected' && serverLatency > 0" class="latency">{{ serverLatency }}ms</span>
      </div>
    </div>
    
    <!-- AI详细状态弹窗 - 使用虚拟触发 -->
    <el-popover
      :visible="aiDetailVisible"
      :virtual-ref="aiStatusRef"
      virtual-triggering
      placement="top-end"
      :width="280"
      popper-class="ai-detail-popover"
      :show-after="0"
      :hide-after="0"
      @mouseenter="handleMouseEnter"
      @mouseleave="handleMouseLeave"
    >
      <div class="ai-detail">
        <div class="detail-header">AI 服务状态</div>
        <div class="detail-item">
          <span class="detail-label">AI Chat</span>
          <span class="detail-status" :class="aiChatStatus">
            <span class="status-dot-small"></span>
          </span>
        </div>
        <div class="detail-item">
          <span class="detail-label">AI Tab 补全</span>
          <span class="detail-status" :class="aiTabStatus">
            <span v-if="aiTabStatus === 'connected'" class="status-dot-small"></span>
            <span v-else class="detail-offline">未连接</span>
          </span>
        </div>
        <div class="detail-item detail-switch" v-if="aiTabStatus === 'connected'">
          <span class="switch-label">启用 Tab 补全</span>
          <el-switch 
            v-model="localAiTabEnabled" 
            size="small" 
            @change="handleTabEnabledChange" 
          />
        </div>
      </div>
    </el-popover>
  </footer>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { Share, Document, Position } from '@element-plus/icons-vue'

// Props
const props = defineProps({
  currentFile: {
    type: Object,
    default: null
  },
  hasUnsavedChanges: {
    type: Boolean,
    default: false
  },
  cursorPosition: {
    type: Object,
    default: () => ({ line: 1, column: 1 })
  },
  totalLines: {
    type: Number,
    default: 0
  },
  serverStatus: {
    type: String,
    default: 'disconnected'
  },
  serverLatency: {
    type: Number,
    default: 0
  },
  aiStatus: {
    type: String,
    default: 'disconnected'
  },
  aiChatStatus: {
    type: String,
    default: 'disconnected'
  },
  aiTabStatus: {
    type: String,
    default: 'disconnected'
  },
  aiTabEnabled: {
    type: Boolean,
    default: true
  }
})

// Emits
const emit = defineEmits(['test-server', 'test-ai', 'toggle-ai-tab'])

// AI详情弹窗
const aiDetailVisible = ref(false)
const aiStatusRef = ref(null)
const localAiTabEnabled = ref(props.aiTabEnabled)

// 监听 props 变化
watch(() => props.aiTabEnabled, (val) => {
  localAiTabEnabled.value = val
})

// 点击服务器连接测试
function handleServerClick() {
  emit('test-server')
}

// 显示AI详情
let closeTimer = null
let isHovering = false

function showAiDetail() {
  aiDetailVisible.value = !aiDetailVisible.value
  
  // 如果打开弹窗，设置定时器自动关闭（只有不在悬停时才关闭）
  if (aiDetailVisible.value) {
    clearTimeout(closeTimer)
    closeTimer = setTimeout(() => {
      if (!isHovering) {
        aiDetailVisible.value = false
      }
    }, 2000)
  } else {
    clearTimeout(closeTimer)
  }
}

// 鼠标进入弹窗时取消自动关闭
function handleMouseEnter() {
  isHovering = true
  clearTimeout(closeTimer)
}

// 鼠标离开弹窗时设置自动关闭
function handleMouseLeave() {
  isHovering = false
  if (aiDetailVisible.value) {
    closeTimer = setTimeout(() => {
      aiDetailVisible.value = false
    }, 500)
  }
}

// 处理 Tab 补全开关变化
function handleTabEnabledChange(val) {
  emit('toggle-ai-tab', val)
}

// 服务器状态标题
const serverTitle = computed(() => {
  if (props.serverStatus === 'connected') {
    return `服务器已连接 · 延迟 ${props.serverLatency}ms`
  }
  const map = {
    'connecting': '正在连接服务器...',
    'disconnected': '服务器未连接 · 点击重试'
  }
  return map[props.serverStatus] || ''
})

// AI状态标题
const aiTitle = computed(() => {
  const map = {
    'connected': 'AI服务已连接 · 点击查看详情',
    'connecting': '正在连接AI服务...',
    'disconnected': 'AI服务未连接 · 点击查看详情'
  }
  return map[props.aiStatus] || ''
})

// 计算当前语言
const language = computed(() => {
  if (!props.currentFile?.path) return ''
  const ext = props.currentFile.path.split('.').pop()?.toLowerCase()
  const langMap = {
    'js': 'JavaScript',
    'jsx': 'JavaScript',
    'ts': 'TypeScript',
    'tsx': 'TypeScript',
    'vue': 'Vue',
    'html': 'HTML',
    'css': 'CSS',
    'scss': 'SCSS',
    'less': 'Less',
    'json': 'JSON',
    'md': 'Markdown',
    'py': 'Python',
    'java': 'Java',
    'go': 'Go',
    'rs': 'Rust',
    'c': 'C',
    'cpp': 'C++',
    'h': 'C/C++ Header',
    'hpp': 'C++ Header',
    'cs': 'C#',
    'rb': 'Ruby',
    'php': 'PHP',
    'sql': 'SQL',
    'yaml': 'YAML',
    'yml': 'YAML',
    'xml': 'XML',
    'sh': 'Shell',
    'bash': 'Bash',
    'txt': 'Plain Text'
  }
  return langMap[ext] || 'Plain Text'
})
</script>

<style scoped>
.status-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  height: 28px;
  padding: 0 12px;
  background: linear-gradient(180deg, #1a1a1a 0%, #121212 100%);
  color: #999;
  font-size: 12px;
  user-select: none;
  border-top: 1px solid #333;
}

.status-left,
.status-right {
  display: flex;
  align-items: center;
  gap: 8px;
  height: 100%;
}

.status-item {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px 10px;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.08);
  transition: all 0.2s ease;
}

.status-item:hover {
  background: rgba(255, 255, 255, 0.12);
  color: #ccc;
}

.status-item .el-icon {
  font-size: 12px;
}

/* 延迟显示 */
.latency {
  font-size: 11px;
  margin-left: 2px;
  opacity: 0.8;
}

/* 连接状态圆点 */
.status-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  animation: pulse 2s infinite;
}

/* 服务器连接状态 - 绿色/红色 */
.status-item.connection.server.connected .status-dot {
  background: #4caf50;
  box-shadow: 0 0 6px #4caf50;
}

.status-item.connection.server.connecting .status-dot {
  background: #ff9800;
  box-shadow: 0 0 6px #ff9800;
}

.status-item.connection.server.disconnected .status-dot {
  background: #f44336;
  box-shadow: 0 0 6px #f44336;
  animation: none;
}

.status-item.connection.server.connected {
  background: rgba(76, 175, 80, 0.15);
  color: #4caf50;
}

.status-item.connection.server.connecting {
  background: rgba(255, 152, 0, 0.15);
  color: #ff9800;
}

.status-item.connection.server.disconnected {
  background: rgba(244, 67, 54, 0.15);
  color: #f44336;
}

.status-item.connection.server.clickable {
  cursor: pointer;
}

.status-item.connection.server.clickable:hover {
  background: rgba(255, 255, 255, 0.15);
}

/* AI连接状态 - 绿色/红色 */
.status-item.connection.ai.connected .status-dot {
  background: #4caf50;
  box-shadow: 0 0 6px #4caf50;
}

.status-item.connection.ai.connecting .status-dot {
  background: #ff9800;
  box-shadow: 0 0 6px #ff9800;
}

.status-item.connection.ai.disconnected .status-dot {
  background: #f44336;
  box-shadow: 0 0 6px #f44336;
  animation: none;
}

.status-item.connection.ai.connected {
  background: rgba(76, 175, 80, 0.15);
  color: #4caf50;
}

.status-item.connection.ai.connecting {
  background: rgba(255, 152, 0, 0.15);
  color: #ff9800;
}

.status-item.connection.ai.disconnected {
  background: rgba(244, 67, 54, 0.15);
  color: #f44336;
}

.status-item.connection.ai.clickable {
  cursor: pointer;
}

.status-item.connection.ai.clickable:hover {
  background: rgba(76, 175, 80, 0.25);
}

/* 分支 */
.status-item.branch {
  background: rgba(64, 158, 255, 0.15);
  color: #409eff;
}

.status-item.branch:hover {
  background: rgba(64, 158, 255, 0.25);
}

/* AI详情弹窗 */
.ai-detail {
  padding: 4px 0;
}

.detail-header {
  font-weight: 500;
  font-size: 13px;
  padding-bottom: 12px;
  margin-bottom: 4px;
  border-bottom: 1px solid #333;
  color: #e0e0e0;
}

.detail-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
  font-size: 12px;
}

.detail-item + .detail-item {
  border-top: 1px solid #333;
}

.detail-label {
  color: #999;
  flex: 1;
}

.detail-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.detail-switch {
  margin-top: 4px;
}

.switch-label {
  color: #999;
  font-size: 12px;
}

.detail-offline {
  font-size: 12px;
  color: #666;
}

.detail-status {
  display: flex;
  align-items: center;
  gap: 4px;
}

.status-dot-small {
  width: 6px;
  height: 6px;
  border-radius: 50%;
}

.detail-status.connected {
  color: #4caf50;
}

.detail-status.connected .status-dot-small {
  background: #4caf50;
  box-shadow: 0 0 4px #4caf50;
}

.detail-status.disconnected {
  color: #f44336;
}

.detail-status.disconnected .status-dot-small {
  background: #f44336;
  box-shadow: 0 0 4px #f44336;
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.5;
  }
}
</style>

<!-- 全局样式：AI详情弹窗暗色主题 -->
<style>
.ai-detail-popover {
  background: #252526 !important;
  border: 1px solid #333 !important;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3) !important;
}

.ai-detail-popover .el-popper__arrow::before {
  background: #252526 !important;
  border-color: #333 !important;
}

.ai-detail-popover .el-switch__core {
  background-color: #4c4d4f !important;
  border-color: #4c4d4f !important;
}

.ai-detail-popover .el-switch.is-checked .el-switch__core {
  background-color: #409eff !important;
  border-color: #409eff !important;
}
</style>
