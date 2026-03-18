<template>
  <aside class="workflow-list">
    <div class="section-title">工作流列表</div>
    <el-table
      :data="workflowList"
      size="small"
      height="100%"
      row-key="id"
      :row-class-name="getRowClassName"
      @row-click="handleSelectWorkflow"
      @row-contextmenu="handleRowContextMenu"
    >
      <el-table-column prop="name" label="名称" />
      <el-table-column prop="version" label="版本" width="70" />
    </el-table>

    <!-- 右键菜单 -->
    <div
      v-show="contextMenuVisible"
      class="context-menu"
      :style="{ left: contextMenuX + 'px', top: contextMenuY + 'px' }"
      @click.stop
    >
      <div class="context-menu-item" @click="handleDeleteWorkflow">
        <span class="menu-icon">🗑️</span>
        <span>删除</span>
      </div>
    </div>
  </aside>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import axios from 'axios'

const emit = defineEmits(['select', 'create', 'delete', 'refresh', 'clear-canvas'])

// 工作流列表数据
const workflowList = ref([])
const currentWorkflowId = ref('')

// 右键菜单相关
const contextMenuVisible = ref(false)
const contextMenuX = ref(0)
const contextMenuY = ref(0)
const contextMenuRow = ref(null)

// 临时/最后工作流ID
const tempWorkflowId = ref(localStorage.getItem('temp_workflow_id') || '')
const lastWorkflowId = ref(localStorage.getItem('last_workflow_id') || '')

// 发送前端日志到后端
async function sendFrontendLog(level, message, extra = {}) {
  try {
    await axios.post('/api/frontend-log/', {
      level,
      message,
      timestamp: new Date().toISOString(),
      url: window.location.href,
      ...extra
    })
  } catch (e) {
    // 静默失败
  }
}

// 保存临时工作流ID到localStorage
function saveTempWorkflowId(id) {
  tempWorkflowId.value = id
  if (id) {
    localStorage.setItem('temp_workflow_id', id)
  } else {
    localStorage.removeItem('temp_workflow_id')
  }
}

// 保存最后打开的工作流ID到localStorage
function saveLastWorkflowId(id) {
  console.log('[前端日志] [INFO] 保存最后打开的工作流ID | id:', id)
  lastWorkflowId.value = id
  if (id) {
    localStorage.setItem('last_workflow_id', id)
  } else {
    localStorage.removeItem('last_workflow_id')
  }
}

// 获取表格行的类名，用于高亮当前选中的工作流
function getRowClassName({ row }) {
  const isCurrent = row.id === currentWorkflowId.value
  console.log('[工作流] 行高亮检查:', row.name, 'ID:', row.id, '当前选中:', currentWorkflowId.value, '是否高亮:', isCurrent)
  return isCurrent ? 'current-workflow-row' : ''
}

// 刷新工作流列表
async function refreshWorkflows() {
  const { data } = await axios.get('/api/workflow/list/', { params: { include_temp: 'true' } })
  workflowList.value = data.workflows || []
  emit('refresh', workflowList.value)
  return workflowList.value
}

// 右键菜单处理
function handleRowContextMenu(row, _column, event) {
  event.preventDefault()
  contextMenuRow.value = row
  contextMenuX.value = event.clientX
  contextMenuY.value = event.clientY
  contextMenuVisible.value = true
}

// 关闭右键菜单
function closeContextMenu() {
  contextMenuVisible.value = false
  contextMenuRow.value = null
}

// 删除工作流
async function handleDeleteWorkflow() {
  if (!contextMenuRow.value) return

  const deleteId = contextMenuRow.value.id
  const deleteName = contextMenuRow.value.name
  console.log('[前端日志] [INFO] 开始删除工作流 | id:', deleteId, 'name:', deleteName)

  try {
    await ElMessageBox.confirm(
      `确定要删除工作流 "${contextMenuRow.value.name}" 吗？此操作不可恢复。`,
      '删除确认',
      {
        confirmButtonText: '删除',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )

    await axios.post('/api/workflow/delete/', { id: deleteId })

    console.log('[前端日志] [INFO] 删除工作流成功 | id:', deleteId, 'name:', deleteName)
    ElMessage.success('工作流已删除')

    // 如果删除的是当前选中的工作流，自动创建新工作流
    if (currentWorkflowId.value === deleteId) {
      ElMessage.info('已自动创建新工作流')
      await handleCreateWorkflow('新工作流')
    } else {
      emit('delete', { id: deleteId, name: deleteName })
    }

    // 清除前端和后端的上次工作流记录
    if (localStorage.getItem('last_workflow_id') === deleteId) {
      localStorage.removeItem('last_workflow_id')
      await clearLastWorkflowIdFromBackend()
    }

    // 刷新列表
    await refreshWorkflows()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('[前端日志] [ERROR] 删除工作流失败 | id:', deleteId, 'error:', error)
      ElMessage.error('删除失败: ' + (error.response?.data?.error || error.message))
    }
  }

  closeContextMenu()
}

// 选择工作流
async function handleSelectWorkflow(row) {
  const { data } = await axios.get('/api/workflow/get/', { params: { id: row.id } })
  console.log('[前端日志] [INFO] 切换工作流 | 收到的数据:', JSON.stringify(data, null, 2))
  const wf = data.workflow
  if (wf) {
    currentWorkflowId.value = wf.id
    saveTempWorkflowId('')
    saveLastWorkflowId(wf.id)
    // 同时更新后端记录
    await setLastWorkflowIdToBackend(wf.id)

    // 解析 graph 数据
    let graphData = wf.graph
    if (typeof graphData === 'string') {
      try {
        graphData = JSON.parse(graphData)
      } catch (e) {
        graphData = {}
      }
    }

    emit('select', {
      id: wf.id,
      name: wf.name,
      graph: graphData,
      last_result: wf.last_result || null
    })

    // 刷新列表以更新高亮状态
    await refreshWorkflows()
  }
}

// 创建工作流
async function handleCreateWorkflow(defaultName) {
  const name = defaultName || '新工作流'

  // 先检查是否已有同名工作流
  const { data: listData } = await axios.get('/api/workflow/list/')
  const existingWorkflow = (listData.workflows || []).find(wf => wf.name === name)
  if (existingWorkflow) {
    console.log('[前端日志] [WARN] 新建工作流失败：同名已存在 | name:', name)
    ElMessage.error(`不能创建，已存在同名工作流: ${name}`)
    return null
  }

  // 初始节点 - 使用 VueFlow 风格的 ID（与拖拽添加的节点一致）
  const inputId = `input-${Date.now()}`
  const agentId = `agent-${Date.now() + 1}`
  const outputId = `output-${Date.now() + 2}`

  const initialNodes = [
    { id: inputId, type: 'input', config: { key: 'input' }, position: { x: 100, y: 200 } },
    { id: agentId, type: 'agent', config: { task: '', model: '' }, position: { x: 400, y: 200 } },
    { id: outputId, type: 'output', config: { format: 'text', template: '{{result}}' }, position: { x: 700, y: 200 } }
  ]

  // 创建边（连接所有相邻节点）
  const initialEdges = []
  if (initialNodes.length >= 2) {
    for (let i = 0; i < initialNodes.length - 1; i++) {
      initialEdges.push({
        id: `e-${initialNodes[i].id}-${initialNodes[i + 1].id}`,
        source: initialNodes[i].id,
        target: initialNodes[i + 1].id,
        sourceHandle: 'output',
        targetHandle: 'input'
      })
    }
  }

  // 直接创建包含完整 graph 的工作流（节点和边）
  const createPayload = {
    name,
    graph: {
      nodes: initialNodes,
      edges: initialEdges
    },
    is_temp: false
  }

  console.log('[前端日志] [INFO] 开始新建工作流 | name:', name)

  // 调用 create API
  let wf = null
  try {
    const response = await axios.post('/api/workflow/create/', createPayload)
    wf = response.data.workflow
    console.log('[前端日志] [INFO] 新建工作流成功 | id:', wf.id, 'name:', wf.name)
  } catch (error) {
    if (error.response?.status === 409) {
      // 已存在同名工作流，提醒用户不能创建
      console.log('[前端日志] [WARN] 新建工作流失败：同名已存在 | name:', name)
      ElMessage.error(`不能创建，已存在同名工作流: ${name}`)
      return null // 直接返回，不创建
    } else {
      console.error('[前端日志] [ERROR] 新建工作流失败 | error:', error)
      throw error
    }
  }

  if (wf) {
    workflowList.value.unshift({ id: wf.id, name: wf.name, version: wf.version })
    currentWorkflowId.value = wf.id
    saveTempWorkflowId('')
    saveLastWorkflowId(wf.id)

    // 解析 graph 返回
    let graphData = wf.graph
    if (typeof graphData === 'string') {
      try {
        graphData = JSON.parse(graphData)
      } catch (e) {
        graphData = {}
      }
    } else if (!graphData) {
      graphData = {
        nodes: initialNodes,
        edges: initialEdges
      }
    }

    emit('create', {
      id: wf.id,
      name: wf.name,
      graph: graphData
    })

    emit('refresh', workflowList.value)

    return wf
  }

  return null
}

// 获取后端存储的上次工作流ID
async function fetchLastWorkflowIdFromBackend() {
  try {
    const { data } = await axios.get('/api/workflow/last/')
    return data.last_workflow_id
  } catch (e) {
    console.warn('[前端日志] [WARN] 获取后端上次工作流ID失败:', e)
    return null
  }
}

// 设置后端存储的上次工作流ID
async function setLastWorkflowIdToBackend(workflowId) {
  try {
    await axios.post('/api/workflow/last/set/', { workflow_id: workflowId })
  } catch (e) {
    console.warn('[前端日志] [WARN] 设置后端上次工作流ID失败:', e)
  }
}

// 清除后端存储的上次工作流ID
async function clearLastWorkflowIdFromBackend() {
  try {
    await axios.post('/api/workflow/last/clear/')
  } catch (e) {
    console.warn('[前端日志] [WARN] 清除后端上次工作流ID失败:', e)
  }
}

// 恢复临时工作流
async function restoreTempWorkflow() {
  const savedTempId = localStorage.getItem('temp_workflow_id')
  if (!savedTempId) {
    console.log('[前端日志] [INFO] localStorage 中无 temp_workflow_id，不恢复')
    return null
  }

  console.log('[前端日志] [INFO] 尝试恢复临时工作流 | id:', savedTempId)

  // 先检查后端是否存在该工作流
  try {
    const { data } = await axios.get('/api/workflow/get/', { params: { id: savedTempId } })
    const wf = data.workflow
    if (!wf) {
      // 后端没有数据，清除 localStorage
      console.log('[前端日志] [INFO] 后端无此临时工作流记录，清除 temp_workflow_id | id:', savedTempId)
      saveTempWorkflowId('')
      return null
    }
    if (!wf.is_temp) {
      // 已不是临时工作流，清除 localStorage
      console.log('[前端日志] [INFO] 工作流已不是临时工作流，清除 temp_workflow_id | id:', savedTempId)
      saveTempWorkflowId('')
      return null
    }

    // 解析 graph 数据
    let graphData = wf.graph
    if (typeof graphData === 'string') {
      try {
        graphData = JSON.parse(graphData)
      } catch (e) {
        graphData = {}
      }
    }

    console.log('[前端日志] [INFO] 已恢复临时工作流 | id:', wf.id, 'name:', wf.name)
    return { type: 'temp', data: { id: wf.id, name: wf.name, graph: graphData, last_result: wf.last_result || null } }
  } catch (e) {
    // 404或其他错误，清除 localStorage
    console.log('[前端日志] [INFO] 恢复临时工作流失败（后端无数据），清除 temp_workflow_id | id:', savedTempId)
    saveTempWorkflowId('')
    return null
  }
}

// 恢复最后打开的工作流
async function restoreLastWorkflow() {
  const savedId = localStorage.getItem('last_workflow_id')
  if (!savedId) {
    console.log('[前端日志] [INFO] localStorage 中无 last_workflow_id，不恢复')
    return null
  }

  console.log('[前端日志] [INFO] 尝试恢复最后打开的工作流 | id:', savedId)

  // 先检查后端是否存在该工作流
  try {
    const { data } = await axios.get('/api/workflow/get/', { params: { id: savedId } })
    const wf = data.workflow
    if (!wf) {
      // 后端没有数据，清除 localStorage
      console.log('[前端日志] [INFO] 后端无此工作流记录，清除 last_workflow_id | id:', savedId)
      saveLastWorkflowId('')
      return null
    }

    // 解析 graph 数据
    let graphData = wf.graph
    if (typeof graphData === 'string') {
      try {
        graphData = JSON.parse(graphData)
      } catch (e) {
        graphData = {}
      }
    }

    // 如果是临时工作流，也更新 tempWorkflowId
    if (wf.is_temp) {
      saveTempWorkflowId(wf.id)
    }

    console.log('[前端日志] [INFO] 已恢复最后打开的工作流 | id:', wf.id, 'name:', wf.name)
    return { type: 'last', data: { id: wf.id, name: wf.name, graph: graphData, last_result: wf.last_result || null } }
  } catch (e) {
    // 404或其他错误，清除 localStorage
    console.log('[前端日志] [INFO] 恢复工作流失败（后端无数据），清除 last_workflow_id | id:', savedId)
    saveLastWorkflowId('')
    return null
  }
}

// 初始化工作流列表
async function init() {
  // 刷新工作流列表
  await refreshWorkflows()

  // 从后端获取上次工作流ID
  const backendLastId = await fetchLastWorkflowIdFromBackend()
  // 同时检查本地存储
  const localLastId = localStorage.getItem('last_workflow_id')
  const tempWorkflowId = localStorage.getItem('temp_workflow_id')
  console.log('[前端日志] [INFO] 检查上次工作流记录 | 后端:', backendLastId || '无', '| 本地:', localLastId || '无', '| temp:', tempWorkflowId || '无')

  // 优先使用后端记录，确保持久化
  if (backendLastId && backendLastId !== localLastId) {
    localStorage.setItem('last_workflow_id', backendLastId)
  }

  // 优先级：最后打开的工作流 > 临时工作流 > 空白画布（不自动创建）
  let restored = await restoreLastWorkflow()

  // 如果没有恢复最后打开的工作流，尝试恢复临时工作流
  if (!restored) {
    restored = await restoreTempWorkflow()
  }

  // 如果都没有恢复，返回 null
  if (!restored) {
    console.log('[前端日志] [INFO] 无历史记录，显示空白画布，等待用户点击新建')
    return null
  }

  // 更新当前工作流ID
  currentWorkflowId.value = restored.data.id

  return restored
}

// 组件挂载时添加点击关闭右键菜单监听
onMounted(() => {
  document.addEventListener('click', closeContextMenu)
})

// 组件卸载时移除监听
onBeforeUnmount(() => {
  document.removeEventListener('click', closeContextMenu)
})

// 暴露方法给父组件
defineExpose({
  init,
  refreshWorkflows,
  handleCreateWorkflow,
  workflowList,
  currentWorkflowId
})
</script>

<style scoped>
.workflow-list {
  background: #1e1e1e;
  border: 1px solid #333;
  border-radius: 12px;
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  position: relative;
  overflow: hidden;
}

.section-title {
  font-weight: 600;
  margin-bottom: 8px;
}

/* 工作流列表表格分隔线暗色主题 */
.workflow-list :deep(.el-table) {
  --el-table-border-color: #333;
  --el-table-header-bg-color: #252526;
  background: #1e1e1e;
}

.workflow-list :deep(.el-table th.el-table__cell) {
  background: #252526;
  color: #e0e0e0;
}

.workflow-list :deep(.el-table td.el-table__cell) {
  border-bottom: 1px solid #333;
}

.workflow-list :deep(.el-table--enable-row-hover .el-table__body tr:hover > td.el-table__cell) {
  background: #2a2a2a;
}

/* 当前选中的工作流行高亮 */
.workflow-list :deep(.current-workflow-row) {
  background-color: rgba(64, 158, 255, 0.2) !important;
}

.workflow-list :deep(.current-workflow-row td) {
  background-color: transparent !important;
}

/* 右键菜单样式 */
.context-menu {
  position: fixed;
  z-index: 9999;
  background: #2a2a2a;
  border: 1px solid #444;
  border-radius: 8px;
  padding: 4px 0;
  min-width: 120px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.4);
}

.context-menu-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  cursor: pointer;
  color: #e0e0e0;
  font-size: 13px;
  transition: background 0.2s;
}

.context-menu-item:hover {
  background: #3a3a3a;
}

.menu-icon {
  font-size: 14px;
}
</style>
