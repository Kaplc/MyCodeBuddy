<template>
  <div class="history-sidebar" :style="{ width: width + 'px' }">
    <div class="history-section-title">
      <span>历史方案</span>
      <div class="history-actions">
        <el-button size="small" text @click="handleNewPlan" title="新建方案">
          <el-icon><Plus /></el-icon>
        </el-button>
        <el-button size="small" text @click="loadSessions" title="刷新">
          <el-icon><Refresh /></el-icon>
        </el-button>
      </div>
    </div>
    <div v-if="loading" class="loading-tip">加载中...</div>
    <div v-else-if="sessions.length === 0" class="empty-tip">暂无历史方案</div>
    <div v-else class="history-list">
      <div
        v-for="session in sessions"
        :key="session.session_id"
        class="history-item"
        :class="{ 'is-selected': currentId === session.session_id }"
        @click="handleSelect(session)"
        @contextmenu.prevent="handleContextMenu(session, $event)"
      >
        <div class="history-goal">{{ session.goal }}</div>
        <div class="history-meta">
          <el-tag size="small" :type="getStatusType(session.status)">{{ getStatusText(session.status) }}</el-tag>
          <span class="history-time">{{ formatTime(session.updated_at) }}</span>
        </div>
      </div>
    </div>
  </div>

  <div
    v-show="contextMenuVisible"
    class="context-menu"
    :style="{ left: contextMenuX + 'px', top: contextMenuY + 'px' }"
    @click.stop
  >
    <div class="context-menu-item" @click="emitDelete">
      <span class="menu-icon">🗑️</span>
      <span>删除</span>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'
import { Plus, Refresh } from '@element-plus/icons-vue'
import axios from 'axios'
import { ElMessage } from 'element-plus'

const props = defineProps({
  sessions: {
    type: Array,
    default: () => [],
  },
  loading: {
    type: Boolean,
    default: false,
  },
  currentId: {
    type: String,
    default: '',
  },
  width: {
    type: Number,
    default: 240,
  },
  logs: {
    type: Array,
    default: () => [],
  },
})

const emit = defineEmits(['select', 'refresh', 'create', 'request-delete', 'sessions-updated'])

function addLog(level, msg) {
  const now = new Date()
  const time = `${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}:${String(now.getSeconds()).padStart(2, '0')}`
  props.logs.push({ level, msg, time })
}

async function loadSessions() {
  emit('refresh')
}

async function loadSessionDetail(sessionId) {
  try {
    const { data } = await axios.get('/api/collaboration/sessions/get/', {
      params: { session_id: sessionId },
    })
    if (data.success) {
      return data
    }
    addLog('error', `获取历史方案详情失败: ${data.error}`)
    return null
  } catch (error) {
    addLog('error', `获取历史方案详情失败: ${error.message}`)
    return null
  }
}

async function handleSelect(session) {
  addLog('info', `加载历史方案: ${session.goal}`)
  const detail = await loadSessionDetail(session.session_id)
  if (detail && detail.session) {
    emit('select', { session, detail })
  }
}

async function handleNewPlan() {
  emit('create')
}

async function handleRequestDelete(session) {
  emit('request-delete', session)
}

const contextMenuVisible = ref(false)
const contextMenuX = ref(0)
const contextMenuY = ref(0)
let selectedContextSession = null

function handleContextMenu(session, event) {
  event.preventDefault()
  selectedContextSession = session
  contextMenuX.value = event.clientX
  contextMenuY.value = event.clientY
  contextMenuVisible.value = true
}

function emitDelete() {
  if (!selectedContextSession) {
    return
  }
  emit('request-delete', selectedContextSession)
  contextMenuVisible.value = false
}

function closeContextMenu() {
  contextMenuVisible.value = false
}

function getStatusType(status) {
  const typeMap = {
    draft: 'info',
    planning: 'warning',
    refining: 'warning',
    reviewing: 'warning',
    building: 'warning',
    ready: 'primary',
    running: 'primary',
    completed: 'success',
    failed: 'danger',
    cancelled: 'info',
  }
  return typeMap[status] || 'info'
}

function getStatusText(status) {
  const textMap = {
    draft: '草稿',
    planning: '规划中',
    refining: '细化中',
    reviewing: '审查中',
    building: '构建中',
    ready: '就绪',
    running: '运行中',
    completed: '已完成',
    failed: '失败',
    cancelled: '已取消',
  }
  return textMap[status] || status
}

function formatTime(isoString) {
  if (!isoString) return ''
  const date = new Date(isoString)
  const now = new Date()
  const diff = now - date
  const minutes = Math.floor(diff / 60000)
  const hours = Math.floor(diff / 3600000)
  const days = Math.floor(diff / 86400000)

  if (minutes < 1) return '刚刚'
  if (minutes < 60) return `${minutes}分钟前`
  if (hours < 24) return `${hours}小时前`
  if (days < 7) return `${days}天前`
  return date.toLocaleDateString()
}

function handleDocumentClick(event) {
  if (!contextMenuVisible.value) {
    return
  }
  const target = event.target
  if (target && typeof target.closest === 'function') {
    if (target.closest('.context-menu')) {
      return
    }
  }
  closeContextMenu()
}

onMounted(() => {
  document.addEventListener('click', handleDocumentClick)
})

onBeforeUnmount(() => {
  document.removeEventListener('click', handleDocumentClick)
})
</script>

<style scoped>
.history-sidebar {
  min-width: 120px;
  max-width: 480px;
  flex-shrink: 0;
  border-right: 1px solid #333;
  background: #252526;
  display: flex;
  flex-direction: column;
  overflow-y: auto;
}

.history-section-title {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 12px 6px;
  font-size: 12px;
  font-weight: 600;
  color: #888;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  flex-shrink: 0;
}

.history-actions {
  display: flex;
  gap: 4px;
}

.loading-tip,
.empty-tip {
  padding: 16px 20px;
  text-align: center;
  color: #555;
  font-size: 12px;
}

.history-list {
  padding: 0 12px 4px;
  display: flex;
  flex-direction: column;
  gap: 6px;
  flex: 1;
  overflow-y: auto;
}

.history-item {
  padding: 10px;
  border-radius: 6px;
  background: #1e1e1e;
  border: 1px solid #333;
  cursor: pointer;
  transition: all 0.2s;
  min-height: auto;
  width: 100%;
  box-sizing: border-box;
}

.history-item:hover {
  border-color: #555;
  background: #2a2a2b;
}

.history-item.is-selected {
  border-color: #409eff;
  background: rgba(64, 158, 255, 0.1);
}

.history-goal {
  font-size: 13px;
  color: #fff;
  margin-bottom: 8px;
  line-height: 1.4;
  word-wrap: break-word;
  word-break: break-word;
  white-space: normal;
  overflow-wrap: break-word;
}

.history-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 11px;
}

.history-time {
  color: #888;
}

.context-menu {
  position: fixed;
  background: #252526;
  border: 1px solid #3e3e42;
  border-radius: 4px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.15);
  z-index: 1000;
  min-width: 120px;
  padding: 4px 0;
}

.context-menu-item {
  padding: 8px 12px;
  font-size: 12px;
  color: #ccc;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;
  transition: background 0.15s;
}

.context-menu-item:hover {
  background: #3e3e42;
  color: #fff;
}

.menu-icon {
  font-size: 14px;
}
</style>
