<template>
  <aside class="collab-panel">
    <div class="collab-header">
      <span class="collab-title">交互式需求文档</span>
      <div style="flex:1" />
      <el-button size="small" @click="emit('close')">关闭</el-button>
    </div>

    <div class="collab-body">
      <!-- 左侧：历史会话列表 -->
      <div class="history-sidebar" :style="{ width: historySidebarWidth + 'px' }">
        <div class="history-header">
          <span class="history-title">历史方案</span>
          <div class="history-header-actions">
            <el-button size="small" text type="primary" @click="handleNewPlan" title="新建方案">
              <el-icon><Plus /></el-icon>
            </el-button>
            <el-button size="small" text @click="loadSessions" :loading="loading">
              <el-icon><Refresh /></el-icon>
            </el-button>
          </div>
        </div>

        <div class="history-list" v-if="!loading">
          <div
            v-for="session in sessions"
            :key="session.session_id"
            class="history-item"
            :class="{ 'is-active': currentSessionId === session.session_id }"
            @click="handleSelectSession(session)"
          >
            <div class="history-goal">{{ session.goal || '未命名方案' }}</div>
            <div class="history-meta">
              <el-tag size="small" :type="getStatusType(session.status)">
                {{ getStatusLabel(session.status) }}
              </el-tag>
              <span class="history-time">{{ formatTime(session.updated_at) }}</span>
            </div>
            <div class="history-actions" @click.stop>
              <el-button size="small" text type="danger" @click="handleDeleteSession(session)">
                <el-icon><Delete /></el-icon>
              </el-button>
            </div>
          </div>

          <div v-if="sessions.length === 0" class="history-empty">
            暂无历史方案
          </div>
        </div>

        <div v-else class="history-loading">
          <el-icon class="is-loading"><Loading /></el-icon>
        </div>
      </div>

      <div class="collab-resize-handle" @mousedown="startResize"></div>

      <!-- 右侧：交互式需求文档生成组件 -->
      <div class="main-panel">
        <CWCurrentPlan
          ref="cwCurrentPlanRef"
          :initial-session-id="currentSessionId"
          @session-created="handleSessionCreated"
          @session-updated="handleSessionUpdated"
        />
      </div>
    </div>

    <CWLog ref="cwLogRef" :logs="logs" @clear="logs = []" />
  </aside>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Refresh, Delete, Loading, Plus } from '@element-plus/icons-vue'
import axios from 'axios'
import CWCurrentPlan from './CWCurrentPlan.vue'
import CWLog from './CWLog.vue'

const emit = defineEmits(['close', 'workflow-completed'])

const cwCurrentPlanRef = ref(null)
const cwLogRef = ref(null)

const sessions = ref([])
const loading = ref(false)
const currentSessionId = ref(null)
const logs = ref([])

const historySidebarWidth = ref(280)
let isResizing = false
let resizeStartX = 0
let resizeStartWidth = 0

function startResize(e) {
  isResizing = true
  resizeStartX = e.clientX
  resizeStartWidth = historySidebarWidth.value
  document.addEventListener('mousemove', onResize)
  document.addEventListener('mouseup', stopResize)
}

function onResize(e) {
  if (!isResizing) return
  const delta = e.clientX - resizeStartX
  const newWidth = Math.min(400, Math.max(180, resizeStartWidth + delta))
  historySidebarWidth.value = newWidth
}

function stopResize() {
  isResizing = false
  document.removeEventListener('mousemove', onResize)
  document.removeEventListener('mouseup', stopResize)
}

function addLog(level, msg) {
  const now = new Date()
  const time = `${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}:${String(now.getSeconds()).padStart(2, '0')}`
  logs.value.push({ level, msg, time })
}

function getStatusType(status) {
  const map = {
    'in_progress': 'warning',
    'completed': 'success',
    'failed': 'danger',
  }
  return map[status] || 'info'
}

function getStatusLabel(status) {
  const map = {
    'in_progress': '进行中',
    'completed': '已完成',
    'failed': '失败',
  }
  return map[status] || status
}

function formatTime(isoString) {
  if (!isoString) return ''
  const date = new Date(isoString)
  const now = new Date()
  const diff = now - date

  if (diff < 60000) return '刚刚'
  if (diff < 3600000) return `${Math.floor(diff / 60000)}分钟前`
  if (diff < 86400000) return `${Math.floor(diff / 3600000)}小时前`
  return date.toLocaleDateString()
}

async function loadSessions() {
  loading.value = true
  try {
    const { data } = await axios.get('/api/collaboration/sessions/list/')
    if (data.success) {
      sessions.value = data.sessions || []
    }
  } catch (error) {
    addLog('error', `加载历史方案失败: ${error.message}`)
  } finally {
    loading.value = false
  }
}

function handleSelectSession(session) {
  currentSessionId.value = session.session_id
  cwCurrentPlanRef.value?.loadSession(session.session_id)
}

async function handleDeleteSession(session) {
  try {
    await ElMessageBox.confirm(
      '确定删除该历史方案吗？删除后不可恢复。',
      '删除历史方案',
      {
        confirmButtonText: '删除',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )
  } catch {
    return
  }

  try {
    await axios.post('/api/collaboration/sessions/delete/', {
      session_id: session.session_id,
    })
    sessions.value = sessions.value.filter(s => s.session_id !== session.session_id)
    if (currentSessionId.value === session.session_id) {
      currentSessionId.value = null
    }
    // 如果删除的是最近一次打开的会话，清除缓存
    const lastSessionId = localStorage.getItem('last_collab_session_id')
    if (lastSessionId === session.session_id) {
      localStorage.removeItem('last_collab_session_id')
    }
    ElMessage.success('已删除')
  } catch (error) {
    ElMessage.error('删除失败')
  }
}

function handleSessionCreated(sessionId) {
  currentSessionId.value = sessionId
  loadSessions()
}

function handleSessionUpdated() {
  loadSessions()
}

function handleNewPlan() {
  currentSessionId.value = null
  cwCurrentPlanRef.value?.resetToGoal()
}

async function restoreLastSession() {
  // 从 localStorage 恢复上次会话
  const lastSessionId = localStorage.getItem('last_collab_session_id')
  if (lastSessionId) {
    currentSessionId.value = lastSessionId
    await loadSessions()
    const exists = sessions.value.find(s => s.session_id === lastSessionId)
    if (exists) {
      cwCurrentPlanRef.value?.loadSession(lastSessionId)
    } else {
      // 会话不存在，清除本地记录
      localStorage.removeItem('last_collab_session_id')
    }
  }
}

onMounted(async () => {
  await loadSessions()
  await restoreLastSession()
})

defineExpose({
  restoreLastSession,
  cwCurrentPlanRef,
  cwLogRef,
})
</script>

<style scoped>
.collab-panel {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: #1e1e1e;
  color: #ccc;
  font-size: 13px;
}

.collab-header {
  display: flex;
  align-items: center;
  padding: 10px 12px;
  border-bottom: 1px solid #333;
  background: #252526;
  flex-shrink: 0;
}

.collab-title {
  font-weight: 600;
  font-size: 14px;
  color: #fff;
}

.collab-body {
  flex: 1;
  display: flex;
  flex-direction: row;
  overflow: hidden;
}

.collab-resize-handle {
  width: 4px;
  flex-shrink: 0;
  background: #333;
  cursor: col-resize;
  transition: background 0.15s;
  position: relative;
  z-index: 1;
}

.collab-resize-handle:hover,
.collab-resize-handle:active {
  background: #409eff;
}

/* 历史侧边栏 */
.history-sidebar {
  display: flex;
  flex-direction: column;
  background: #252526;
  border-right: 1px solid #333;
  flex-shrink: 0;
}

.history-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 12px;
  border-bottom: 1px solid #333;
}

.history-header-actions {
  display: flex;
  gap: 4px;
}

.history-title {
  font-size: 12px;
  font-weight: 600;
  color: #888;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.history-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}

.history-item {
  padding: 10px 12px;
  border-radius: 6px;
  cursor: pointer;
  margin-bottom: 6px;
  transition: background 0.2s;
  position: relative;
}

.history-item:hover {
  background: rgba(255, 255, 255, 0.05);
}

.history-item.is-active {
  background: rgba(64, 158, 255, 0.15);
  border-left: 2px solid #409eff;
}

.history-goal {
  font-size: 13px;
  color: #ccc;
  margin-bottom: 6px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.history-meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.history-time {
  font-size: 11px;
  color: #666;
}

.history-actions {
  position: absolute;
  top: 8px;
  right: 8px;
  opacity: 0;
  transition: opacity 0.2s;
}

.history-item:hover .history-actions {
  opacity: 1;
}

.history-empty {
  text-align: center;
  color: #555;
  padding: 40px 0;
  font-size: 12px;
}

.history-loading {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #888;
}

/* 主面板 */
.main-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
</style>
