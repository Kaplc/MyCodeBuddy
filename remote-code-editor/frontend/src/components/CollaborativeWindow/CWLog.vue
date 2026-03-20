<template>
  <div class="collab-log">
    <div class="log-header">
      <span>执行日志</span>
      <el-button size="small" text @click="emit('clear')">清空</el-button>
    </div>
    <div ref="logContainerRef" class="log-content">
      <div v-for="(log, idx) in logs" :key="idx" class="log-line" :class="`log-${log.level}`">
        <span class="log-time">{{ log.time }}</span>
        <span class="log-msg">{{ log.msg }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, nextTick } from 'vue'

const props = defineProps({
  logs: {
    type: Array,
    default: () => [],
  },
})

const emit = defineEmits(['clear'])
const logContainerRef = ref(null)

watch(
  () => props.logs.length,
  () => {
    nextTick(() => {
      if (logContainerRef.value) {
        logContainerRef.value.scrollTop = logContainerRef.value.scrollHeight
      }
    })
  }
)

function addLog(level, msg) {
  const now = new Date()
  const time = `${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}:${String(now.getSeconds()).padStart(2, '0')}`
  props.logs.push({ level, msg, time })
  const consoleMsg = `[${time}] [${level.toUpperCase()}] ${msg}`
  if (level === 'error') {
    console.error(consoleMsg)
  } else if (level === 'warn') {
    console.warn(consoleMsg)
  } else {
    console.log(consoleMsg)
  }
}

defineExpose({ addLog })
</script>

<style scoped>
.collab-log {
  border-top: 1px solid #333;
  flex-shrink: 0;
  max-height: 160px;
  display: flex;
  flex-direction: column;
}

.log-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 6px 12px;
  background: #252526;
  border-bottom: 1px solid #333;
  font-size: 11px;
  color: #888;
}

.log-content {
  flex: 1;
  overflow-y: auto;
  padding: 6px 12px;
}

/* 暗色主题滚动条 */
.log-content::-webkit-scrollbar {
  width: 6px;
}

.log-content::-webkit-scrollbar-track {
  background: #1e1e1e;
}

.log-content::-webkit-scrollbar-thumb {
  background: #424242;
  border-radius: 3px;
}

.log-content::-webkit-scrollbar-thumb:hover {
  background: #4f4f4f;
}

.log-line {
  display: flex;
  gap: 8px;
  font-size: 11px;
  line-height: 1.6;
  font-family: 'Consolas', monospace;
}

.log-time {
  color: #555;
  flex-shrink: 0;
}

.log-msg {
  color: #aaa;
}

.log-info .log-msg { color: #409eff; }
.log-success .log-msg { color: #67c23a; }
.log-error .log-msg { color: #f56c6c; }
.log-warn .log-msg { color: #e6a23c; }
</style>
