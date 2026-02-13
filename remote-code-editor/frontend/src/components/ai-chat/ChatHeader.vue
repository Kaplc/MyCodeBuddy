<template>
  <div class="chat-header">
    <div class="header-left">
      <el-icon class="ai-icon"><ChatDotRound /></el-icon>
      <span>AI 助手</span>
      <span 
        class="connection-status" 
        :class="statusClass"
        :title="statusText"
      ></span>
      <!-- 上下文统计 -->
      <span v-if="contextCount > 0" class="context-info" :title="`约 ${contextCount} tokens`">
        {{ formatContextCount }}
      </span>
    </div>
    <div class="header-actions">
      <el-button size="small" text @click="handleNewChat" title="新建对话">
        <el-icon><Plus /></el-icon>
      </el-button>
      <el-button size="small" text @click="handleShowHistory" title="历史对话">
        <el-icon><Clock /></el-icon>
      </el-button>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { ChatDotRound, Clock, Plus } from '@element-plus/icons-vue'

// Props
const props = defineProps({
  connectionStatus: {
    type: String,
    default: 'disconnected'
  },
  contextCount: {
    type: Number,
    default: 0
  },
  messageCount: {
    type: Number,
    default: 0
  }
})

// Emits
const emit = defineEmits(['show-history', 'new-chat'])

// 计算状态样式
const statusClass = computed(() => {
  return {
    'status-connected': props.connectionStatus === 'connected',
    'status-connecting': props.connectionStatus === 'connecting',
    'status-disconnected': props.connectionStatus === 'disconnected'
  }
})

// 计算状态文本
const statusText = computed(() => {
  const texts = {
    connected: 'AI 已连接',
    connecting: 'AI 连接中...',
    disconnected: 'AI 未连接'
  }
  return texts[props.connectionStatus] || 'AI 未连接'
})

// 格式化上下文数量显示
const formatContextCount = computed(() => {
  const count = props.contextCount
  if (count >= 10000) {
    return `${(count / 1000).toFixed(1)}k`
  }
  if (count >= 1000) {
    return `${(count / 1000).toFixed(1)}k`
  }
  return count
})

// 显示历史
function handleShowHistory() {
  emit('show-history')
}

// 新建对话
function handleNewChat() {
  emit('new-chat')
}
</script>

<style scoped>
.chat-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 16px;
  background: #252526;
  border-bottom: 1px solid #333;
  flex-shrink: 0;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #cccccc;
  font-weight: 500;
}

.ai-icon {
  color: #409eff;
  font-size: 18px;
}

.connection-status {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  margin-left: 4px;
}

.status-connected {
  background-color: #4caf50;
  box-shadow: 0 0 4px #4caf50;
}

.status-connecting {
  background-color: #ff9800;
  box-shadow: 0 0 4px #ff9800;
  animation: pulse 1s infinite;
}

.status-disconnected {
  background-color: #f44336;
  box-shadow: 0 0 4px #f44336;
}

.context-info {
  font-size: 11px;
  color: #888;
  margin-left: 8px;
  padding: 2px 6px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 4px;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.header-actions {
  display: flex;
  gap: 4px;
  align-items: center;
}
</style>
