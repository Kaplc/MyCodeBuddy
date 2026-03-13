<template>
  <div class="workflow-panel">
    <div class="panel-header">
      <el-button size="small" @click="emit('close')">返回编辑器</el-button>
      <el-input v-model="workflowName" size="small" placeholder="工作流名称" />
      <el-button size="small" type="primary" @click="handleCreateWorkflow">新建</el-button>
      <el-button size="small" @click="refreshWorkflows">刷新</el-button>
      <el-button size="small" :disabled="!currentWorkflowId" @click="handleSaveWorkflow">保存</el-button>
      <el-button size="small" type="success" :disabled="isRunning" @click="handleRunWorkflow">
          {{ isRunning ? '运行中...' : '运行' }}
        </el-button>
      <div style="flex: 1"></div>
      <el-button size="small" type="info" @click="showDebugInfo">Debug</el-button>
    </div>


    <div class="panel-body">
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

      <section class="workflow-editor">
        <div class="section-title">可视化编辑器</div>
        <div class="editor-layout">
          <aside class="node-palette">
            <div class="palette-title">节点库（拖拽到画布）</div>
            <div
              v-for="item in nodeTypes"
              :key="item"
              class="palette-item"
              :style="{ '--node-color': paletteColorMap[item] }"
              draggable="true"
              @dragstart="onDragStart($event, item)"
            >
              {{ paletteTypeMap[item] }}
            </div>

            <div class="palette-title">选中节点</div>
            <el-input v-model="selectedNodeId" size="small" placeholder="节点 ID" disabled />
            
            <!-- Input 节点配置 -->
            <template v-if="selectedNodeType === 'input'">
              <div class="config-section">
                <div class="config-label">输入参数名</div>
                <el-input
                  v-model="inputKey"
                  size="small"
                  placeholder="如: input, query"
                />
              </div>
              <div class="config-section">
                <div class="config-label">默认值</div>
                <el-input
                  v-model="inputDefault"
                  size="small"
                  placeholder="可选"
                />
              </div>
            </template>
            
            <!-- Output 节点配置 -->
            <template v-if="selectedNodeType === 'output'">
              <div class="config-section">
                <div class="config-label">输出格式</div>
                <el-select v-model="outputFormat" size="small" style="width: 100%">
                  <el-option label="文本" value="text" />
                  <el-option label="JSON" value="json" />
                  <el-option label="Markdown" value="markdown" />
                </el-select>
              </div>
              <div class="config-section">
                <div class="config-label">输出模板</div>
                <el-input
                  v-model="outputTemplate"
                  type="textarea"
                  :rows="3"
                  size="small"
                  placeholder="使用 {{result}} 引用结果"
                />
              </div>
            </template>
            
            <!-- Prompt 节点配置 -->
            <template v-if="selectedNodeType === 'prompt'">
              <div class="config-section">
                <div class="config-label">提示词模板</div>
                <el-input
                  v-model="promptTemplate"
                  type="textarea"
                  :rows="6"
                  size="small"
                  placeholder="使用 {{变量名}} 插入变量"
                />
              </div>
            </template>
            
            <!-- Agent 节点配置 -->
            <template v-if="selectedNodeType === 'agent'">
              <div class="config-section">
                <div class="config-label">任务描述</div>
                <el-input
                  v-model="agentTask"
                  type="textarea"
                  :rows="4"
                  size="small"
                  placeholder="描述 Agent 需要完成的任务"
                />
              </div>
              <div class="config-section">
                <div class="config-label">模型</div>
                <el-select v-model="agentModel" size="small" style="width: 100%" placeholder="选择模型">
                  <el-option
                    v-for="model in modelList"
                    :key="model.id"
                    :label="model.name"
                    :value="model.id"
                  >
                    <span>{{ model.name }}</span>
                    <span style="color: #8492a6; font-size: 12px; margin-left: 8px;">{{ model.provider }}</span>
                  </el-option>
                </el-select>
              </div>
            </template>
            
            <!-- Match 节点配置 -->
            <template v-if="selectedNodeType === 'match'">
              <div class="config-section">
                <div class="config-label">匹配模式</div>
                <el-input
                  v-model="matchPattern"
                  size="small"
                  placeholder="正则表达式"
                />
              </div>
              <div class="config-section">
                <div class="config-label">输出字段名</div>
                <el-input
                  v-model="matchOutputField"
                  size="small"
                  placeholder="如: result"
                />
              </div>
            </template>
            
            <!-- Branch 节点的条件输入 -->
            <template v-if="selectedNodeType === 'branch'">
              <div class="config-section">
                <div class="config-label">条件表达式</div>
                <el-input
                  v-model="branchExpression"
                  size="small"
                  placeholder="如: count > 5"
                />
              </div>
            </template>
            
            <!-- ForLoop 节点的配置 -->
            <template v-if="selectedNodeType === 'for_loop'">
              <div class="config-section">
                <div class="config-label">起始索引</div>
                <el-input-number v-model="forLoopStart" size="small" :min="0" />
              </div>
              <div class="config-section">
                <div class="config-label">结束索引</div>
                <el-input-number v-model="forLoopEnd" size="small" :min="1" />
              </div>
              <div class="config-section">
                <div class="config-label">步长</div>
                <el-input-number v-model="forLoopStep" size="small" :min="1" />
              </div>
            </template>

            <!-- Tool 节点的下拉菜单 -->
            <template v-if="selectedNodeType === 'tool'">
              <div class="config-section">
                <div class="config-label">选择工具</div>
                <el-select v-model="selectedToolName" size="small" placeholder="选择工具" style="width: 100%">
                  <el-option
                    v-for="tool in toolList"
                    :key="tool.name"
                    :label="tool.description_cn ? `${tool.name} - ${tool.description_cn}` : tool.name"
                    :value="tool.name"
                  />
                </el-select>
              </div>
              <div class="config-section">
                <div class="config-label">输出端口数量</div>
                <el-input-number v-model="selectedToolOutputs" size="small" :min="1" :max="5" />
              </div>
            </template>
            
            <el-button size="small" @click="applyNodeConfig" style="display: none;">应用配置</el-button>
          </aside>

          <div
            class="flow-canvas"
            @dragover.prevent
            @drop="onDrop"
          >
            <VueFlow
              v-model:nodes="nodes"
              v-model:edges="edges"
              class="vue-flow"
              :fit-view-on-init="true"
              :default-zoom="1"
              :node-types="flowNodeTypes"
              :pan-on-drag="[2]"
              :selection-on-drag="true"
              :selection-mode="SelectionMode.Partial"
              :no-drag-classes="['node-body', 'node-header', 'drag-handle']"
              :is-valid-connection="isValidConnection"
              @connect="onConnect"
              @edges-delete="onEdgesDelete"
              @node-drag-stop="onNodeDragStop"
              @nodes-delete="onNodesDelete"
              @node-click="onNodeClick"
              @pane-click="onPaneClick"
              @node-data-update="onNodeDataUpdate"
              @edge-click="onEdgeClick"
              @selection-change="onSelectionChange"
              @selection-start="onSelectionStart"
              @selection-end="onSelectionEnd"
            >
              <Background :gap="18" :size="2" color="#2b2b2b" />
              <MiniMap :width="200" :height="130" :node-color="getMiniMapColor" />
              <Controls />
            </VueFlow>
          </div>
        </div>

        <!-- 可拖拽分隔条 -->
        <div class="resizer" @mousedown="startResize"></div>

        <div v-show="jsonPanelHeight > 0" class="json-panel" :style="{ height: jsonPanelHeight + 'px', overflow: 'hidden' }">
          <div class="json-header">Graph JSON</div>
          <el-input v-model="graphJson" type="textarea" :rows="8" resize="none" class="json-textarea" />
        </div>
      </section>

      <aside class="workflow-run">
        <div class="section-title">
          运行
          <span v-if="edges.length > 0" class="connection-badge">{{ edges.length }} 条连接</span>
          <span v-else class="connection-warning">未连接</span>
        </div>
        <div v-if="edges.length === 0" class="connection-hint">
          提示：从节点的右侧（输出）拖线到左侧（输入）来连接节点
        </div>
        <el-input v-model="runInput" type="textarea" :rows="6" placeholder="输入内容或 JSON" />
        <el-button size="small" type="success" :disabled="isRunning" @click="handleRunWorkflow">
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
          <div v-if="runInput" class="message user">
            <div class="message-header">
              <span class="role-name">你</span>
            </div>
            <div class="message-content">
              <pre>{{ runInput }}</pre>
            </div>
          </div>
          <!-- 执行结果 -->
          <div v-if="runResultHtml" class="message assistant">
            <div class="message-header">
              <span class="role-name">工作流</span>
              <span v-if="executionTime" class="execution-time">{{ executionTime }}</span>
            </div>
            <div class="message-content">
              <div v-html="runResultHtml"></div>
            </div>
          </div>
          <!-- 错误结果 -->
          <div v-if="runError" class="message error">
            <div class="message-header">
              <span class="role-name">错误</span>
            </div>
            <div class="message-content">
              <pre>{{ runError }}</pre>
            </div>
          </div>
          <!-- 空状态 -->
          <div v-if="!runResultHtml && !runError && !isRunning" class="empty-result">
            执行结果将显示在这里
          </div>
        </div>
      </aside>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, watch, markRaw, nextTick, shallowRef } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import axios from 'axios'
import { VueFlow, useVueFlow, MarkerType, SelectionMode } from '@vue-flow/core'
import { Background } from '@vue-flow/background'
import { Controls } from '@vue-flow/controls'
import { MiniMap } from '@vue-flow/minimap'
import WorkflowNode from './WorkflowNode.vue'
import hljs from 'highlight.js'
import '@vue-flow/core/dist/style.css'
import '@vue-flow/core/dist/theme-default.css'
import '@vue-flow/controls/dist/style.css'
import '@vue-flow/minimap/dist/style.css'
import 'highlight.js/styles/tokyo-night-dark.css'

const emit = defineEmits(['close'])

const workflowList = ref([])
const currentWorkflowId = ref('')
const workflowName = ref('')

// 获取表格行的类名，用于高亮当前选中的工作流
function getRowClassName({ row }) {
  const isCurrent = row.id === currentWorkflowId.value
  console.log('[工作流] 行高亮检查:', row.name, 'ID:', row.id, '当前选中:', currentWorkflowId.value, '是否高亮:', isCurrent)
  return isCurrent ? 'current-workflow-row' : ''
}

// 右键菜单相关
const contextMenuVisible = ref(false)
const contextMenuX = ref(0)
const contextMenuY = ref(0)
const contextMenuRow = ref(null)
const graphJson = ref('')
const runInput = ref('')
const runResultHtml = ref('')
const runError = ref('')
const executionTime = ref('')
const isRunning = ref(false)

// 自动保存相关
let autoSaveTimer = null
const AUTO_SAVE_DELAY = 3000 // 3秒自动保存
const tempWorkflowId = ref(localStorage.getItem('temp_workflow_id') || '') // 临时工作流ID（从localStorage恢复）
const lastWorkflowId = ref(localStorage.getItem('last_workflow_id') || '') // 最后打开的工作流ID
let lastSaveTime = 0

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

const nodeTypes = [
  'input',
  'prompt',
  'agent',
  'tool',
  'output',
  // 流程控制节点
  'branch',
  'for_loop',
  // 匹配节点
  'match'
]

const flowNodeTypes = markRaw({
  workflow: markRaw(WorkflowNode)
})

// 处理节点数据更新
function onNodeDataUpdate(nodeId, newData) {
  nodes.value = nodes.value.map(node => {
    if (node.id === nodeId) {
      return { ...node, data: newData }
    }
    return node
  })
  syncGraphJson()
}


const colorMap = {
  input: '#4cc9f0',
  prompt: '#4895ef',
  agent: '#3a86ff',
  tool: '#43aa8b',
  condition: '#f4a261',
  output: '#9b5de5'
}

// 节点库颜色映射
const paletteColorMap = {
  input: '#4cc9f0',
  prompt: '#4895ef',
  agent: '#3a86ff',
  tool: '#43aa8b',
  output: '#9b5de5',
  branch: '#f4a261',
  for_loop: '#e879f9',
  match: '#06b6d4'
}

// 节点库英文名称映射
const paletteTypeMap = {
  input: 'Input',
  prompt: 'Prompt',
  agent: 'Agent',
  tool: 'Tool',
  output: 'Output',
  branch: 'Branch',
  for_loop: 'ForLoop',
  match: 'Match'
}

const nodes = shallowRef([])
const edges = shallowRef([])

// 撤销历史栈
const historyStack = ref([])
const maxHistorySize = 50 // 最大历史记录数

const selectedNodeId = ref('')
const selectedNodeType = ref('')
const selectedEdgeId = ref('')
const selectedEdgeCondition = ref('')

// Branch/ForLoop 节点配置
const branchExpression = ref('')
const forLoopStart = ref(0)
const forLoopEnd = ref(10)
const forLoopStep = ref(1)

// Tool 节点配置
const toolList = ref([])
const selectedToolName = ref('')
const selectedToolOutputs = ref(1)

// Model 列表（从服务器获取）
const modelList = ref([])

// Input 节点配置
const inputKey = ref('')
const inputDefault = ref('')

// Output 节点配置
const outputFormat = ref('text')
const outputTemplate = ref('')

// Prompt 节点配置
const promptTemplate = ref('')

// Agent 节点配置
const agentTask = ref('')
const agentModel = ref('')

// Match 节点配置
const matchPattern = ref('')
const matchOutputField = ref('')

// 获取工具列表
async function loadToolList() {
  try {
    const { data } = await axios.get('/api/workflow/tools/')
    toolList.value = data.tools || []
  } catch (e) {
    console.error('获取工具列表失败:', e)
  }
}

// 获取模型列表
async function loadModelList() {
  try {
    const { data } = await axios.get('/api/workflow/models/')
    modelList.value = data.models || []
  } catch (e) {
    console.error('获取模型列表失败:', e)
    // 使用默认模型列表作为后备
    modelList.value = [
      { id: '', name: '默认', description: '使用系统默认模型', provider: 'default' },
      { id: 'glm-4-flash', name: 'GLM-4-Flash', description: '智谱 GLM-4-Flash', provider: 'zhipu' },
    ]
  }
}

const { addEdges, project, removeNodes, removeEdges } = useVueFlow()

// 保存当前状态到历史栈
function saveHistory(action = 'unknown', saveToStack = true) {
  // 如果明确指定不保存到栈，直接返回
  if (!saveToStack) {
    console.log(`[历史] 跳过保存（配置为不保存）, 操作: ${action}`)
    return
  }

  const snapshot = {
    nodes: JSON.parse(JSON.stringify(nodes.value)),
    edges: JSON.parse(JSON.stringify(edges.value)),
    action, // 记录操作类型
    timestamp: Date.now()
  }
  
  // 如果当前不在栈顶，删除当前位置之后的历史
  if (historyStack.value.length > 0) {
    // 检查是否与最新状态相同，避免重复保存
    const lastSnapshot = historyStack.value[historyStack.value.length - 1]
    if (JSON.stringify(lastSnapshot.nodes) === JSON.stringify(snapshot.nodes) &&
        JSON.stringify(lastSnapshot.edges) === JSON.stringify(snapshot.edges)) {
      console.log(`[历史] 跳过重复快照, 操作: ${action}`)
      return
    }
  }
  
  historyStack.value.push(snapshot)
  
  // 限制历史记录数量
  if (historyStack.value.length > maxHistorySize) {
    historyStack.value.shift()
  }
  
  console.log(`[历史] 入栈操作: ${action}, 节点数: ${snapshot.nodes.length}, 边数: ${snapshot.edges.length}, 历史栈大小: ${historyStack.value.length}`)
}

// 撤销操作
function undo() {
  console.log('[前端日志] [INFO] Ctrl+Z 撤销操作触发 | 历史栈大小:', historyStack.value.length)
  
  if (historyStack.value.length <= 1) {
    console.log('[前端日志] [WARN] 没有可撤销的操作 | 历史栈大小:', historyStack.value.length)
    ElMessage.warning('没有可撤销的操作')
    return
  }
  
  // 移除当前状态
  historyStack.value.pop()
  
  // 获取上一个状态
  const previousSnapshot = historyStack.value[historyStack.value.length - 1]
  
  console.log('[前端日志] [INFO] 准备恢复状态 | 节点数:', previousSnapshot.nodes.length, '| 边数:', previousSnapshot.edges.length)
  
  // 恢复状态
  nodes.value = previousSnapshot.nodes
  edges.value = previousSnapshot.edges

  // 清空选中状态
  selectedNodeId.value = ''
  selectedNodeType.value = ''
  currentSelectedNodeId.value = null
  multiSelectedNodeIds.value = new Set()

  // 清除所有节点的选中状态和自定义类
  nodes.value = nodes.value.map(n => ({
    ...n,
    selected: false,
    class: ''
  }))
  
  syncGraphJson()
  
  console.log('[前端日志] [INFO] 即将显示"已撤销"提示')
  ElMessage.success('已撤销')
  console.log('[历史] 撤销完成, 剩余历史栈大小:', historyStack.value.length)
}

// 清空历史栈（用于加载新工作流）
function clearHistory() {
  historyStack.value = []
}

function onDragStart(event, nodeType) {
  event.dataTransfer.setData('application/vueflow', nodeType)
  event.dataTransfer.effectAllowed = 'move'
}

function onDrop(event) {
  const type = event.dataTransfer.getData('application/vueflow')
  if (!type) return

  // 限制只能有一个入口节点
  if (type === 'input') {
    const hasInput = nodes.value.some(n => n.data?.wfType === 'input')
    if (hasInput) {
      ElMessage.warning('只能有一个入口节点')
      return
    }
  }

  const position = project({
    x: event.offsetX,
    y: event.offsetY
  })

  const id = `${type}-${Date.now()}`
  
  // 保存历史
  saveHistory(`添加节点:${type}`)
  
  nodes.value = [
    ...nodes.value,
    {
      id,
      type: 'workflow',
      position,
      dragHandle: '.drag-handle',
      data: {
        wfType: type,
        config: {}
      }
    }
  ]

  syncGraphJson()
}

function onConnect(params) {
  console.log('[工作流] 连接节点:', params)
  
  // 检查端口是否已被占用
  const sourceHasConnection = edges.value.some(
    e => e.source === params.source && e.sourceHandle === params.sourceHandle
  )
  const targetHasConnection = edges.value.some(
    e => e.target === params.target && e.targetHandle === params.targetHandle
  )
  
  if (sourceHasConnection || targetHasConnection) {
    ElMessage.warning('该端口已有连接')
    return
  }
  
  // 保存历史
  saveHistory(`连接节点:${params.source}->${params.target}`)
  
  // 获取源节点判断是否为条件节点
  const sourceNode = nodes.value.find(n => n.id === params.source)
  const isConditionNode = sourceNode?.data?.wfType === 'condition'
  
  // 如果是条件节点,根据 sourceHandle 设置 condition
  const condition = isConditionNode ? (params.sourceHandle || 'true') : ''
  
  const newEdge = {
    ...params,
    id: `e-${params.source}-${params.target}-${Date.now()}`,
    markerEnd: { type: MarkerType.ArrowClosed },
    label: isConditionNode ? condition : '',
    style: { stroke: '#ffffff', strokeWidth: 2 },
    data: { condition }
  }
  
  // 使用 addEdges 添加边
  addEdges([newEdge])
  
  console.log('[工作流] 添加边后的 edges:', edges.value)
  
  // 延迟一点同步，确保 VueFlow 完成更新
  setTimeout(() => {
    syncGraphJson()
  }, 50)
}

// 删除边时同步更新 JSON
function onEdgesDelete(event) {
  console.log('[工作流] 删除边:', event.edges)
  // 保存历史
  saveHistory(`删除边:${event.edges?.length || 1}条`)
  nextTick(() => {
    syncGraphJson()
  })
}

// 节点拖动结束时同步更新 JSON
function onNodeDragStop(event) {
  console.log('[工作流] 节点拖动结束:', event)
  
  // 等待 VueFlow 更新完成后再保存历史
  nextTick(() => {
    // 确保保存最新的节点位置
    saveHistory('移动节点')
    syncGraphJson()
    console.log('[工作流] 拖动历史已保存, nodes:', nodes.value.map(n => ({ id: n.id, pos: n.position })))
  })
}

// 删除节点时同步更新 JSON
function onNodesDelete(event) {
  console.log('[工作流] 删除节点:', event.nodes)
  nextTick(() => {
    syncGraphJson()
  })
}

// 验证连接是否有效（限制每个端口只能有一个连接）
function isValidConnection(connection) {
  const sourceHasConnection = edges.value.some(
    e => e.source === connection.source && e.sourceHandle === connection.sourceHandle
  )
  const targetHasConnection = edges.value.some(
    e => e.target === connection.target && e.targetHandle === connection.targetHandle
  )
  return !sourceHasConnection && !targetHasConnection
}

// 当前选中的节点ID
const currentSelectedNodeId = ref(null)
// 多选节点集合
const multiSelectedNodeIds = ref(new Set())

function onNodeClick(event) {
  console.log('[工作流] 点击节点:', event.node, 'Ctrl键:', event.ctrlKey || event.metaKey)
  const node = event.node
  if (!node) return

  const isMultiSelect = event.ctrlKey || event.metaKey // Ctrl或Command键

  if (isMultiSelect) {
    // Ctrl多选模式：切换节点选中状态
    const newSelectedIds = new Set(multiSelectedNodeIds.value)

    if (newSelectedIds.has(node.id)) {
      // 如果已选中，取消选中
      newSelectedIds.delete(node.id)
      console.log('[工作流] 多选取消节点:', node.id)
    } else {
      // 如果未选中，添加到选中集合
      newSelectedIds.add(node.id)
      console.log('[工作流] 多选添加节点:', node.id)
    }

    multiSelectedNodeIds.value = newSelectedIds
    console.log('[工作流] 多选节点ID集合:', Array.from(newSelectedIds))

    // 更新所有节点的选中状态
    nodes.value = nodes.value.map(n => {
      const isNowSelected = newSelectedIds.has(n.id)
      console.log(`[工作流] 节点 ${n.id} 选中状态: ${isNowSelected}`)
      return {
        ...n,
        selected: isNowSelected,
        class: isNowSelected ? 'node-multi-selected' : '' // 添加自定义类
      }
    })

    // 强制触发 VueFlow 更新
    nextTick(() => {
      console.log('[工作流] nextTick 后的节点状态:', nodes.value.map(n => ({ id: n.id, selected: n.selected, class: n.class })))
    })

    // 更新选中信息
    if (newSelectedIds.size === 0) {
      currentSelectedNodeId.value = null
      selectedNodeId.value = ''
      selectedNodeType.value = ''
    } else if (newSelectedIds.size === 1) {
      const singleNodeId = Array.from(newSelectedIds)[0]
      const singleNode = nodes.value.find(n => n.id === singleNodeId)
      if (singleNode) {
        currentSelectedNodeId.value = singleNodeId
        selectedNodeId.value = singleNodeId
        selectedNodeType.value = singleNode.data?.wfType || ''
        loadNodeConfig(singleNode)
      }
    } else {
      currentSelectedNodeId.value = Array.from(newSelectedIds)[0]
      selectedNodeId.value = `${newSelectedIds.size} 个节点`
      selectedNodeType.value = ''
    }
  } else {
    // 单选模式：清除之前选中状态，只选中当前节点
    multiSelectedNodeIds.value = new Set([node.id])

    nodes.value = nodes.value.map(n => ({
      ...n,
      selected: n.id === node.id,
      class: n.id === node.id ? 'node-multi-selected' : ''
    }))

    // 检查高亮是否设置成功
    const targetNode = nodes.value.find(n => n.id === node.id)
    console.log('[工作流] 设置高亮结果:', targetNode?.selected, '节点ID:', node.id)

    currentSelectedNodeId.value = node.id
    selectedNodeId.value = node.id
    selectedNodeType.value = node.data?.wfType || ''
    loadNodeConfig(node)
  }
}

// 加载节点配置
function loadNodeConfig(node) {
  const config = node.data?.config || {}
  
  // 根据节点类型加载配置
  switch (selectedNodeType.value) {
    case 'input':
      inputKey.value = config.key || ''
      inputDefault.value = config.default || ''
      break
    case 'output':
      outputFormat.value = config.format || 'text'
      outputTemplate.value = config.template || ''
      break
    case 'prompt':
      promptTemplate.value = config.template || ''
      break
    case 'agent':
      agentTask.value = config.task || ''
      agentModel.value = config.model || ''
      break
    case 'match':
      matchPattern.value = config.pattern || ''
      matchOutputField.value = config.output_field || ''
      break
    case 'branch':
      branchExpression.value = config.expression || ''
      break
    case 'for_loop':
      forLoopStart.value = config.start ?? 0
      forLoopEnd.value = config.end ?? 10
      forLoopStep.value = config.step ?? 1
      break
    case 'tool':
      selectedToolName.value = config.tool || config.name || ''
      selectedToolOutputs.value = config.outputs || 1
      break
  }
}

// 点击空白处取消选中
function onPaneClick() {
  console.log('[工作流] 点击空白处，取消选中节点')
  nodes.value = nodes.value.map(n => ({
    ...n,
    selected: false,
    class: ''
  }))
  currentSelectedNodeId.value = null
  selectedNodeId.value = ''
  selectedNodeType.value = ''
  multiSelectedNodeIds.value = new Set()
}

// 框选节点处理
function onSelectionChange({ nodes: selectedNodes }) {
  console.log('[工作流] 框选节点:', selectedNodes)

  // 更新所有节点的选中状态
  const selectedIds = new Set(selectedNodes.map(n => n.id))
  nodes.value = nodes.value.map(node => {
    const isNowSelected = selectedIds.has(node.id)
    return {
      ...node,
      selected: isNowSelected,
      class: isNowSelected ? 'node-multi-selected' : ''
    }
  })

  // 更新多选集合
  multiSelectedNodeIds.value = selectedIds

  // 如果只选中了一个节点，更新配置面板
  if (selectedNodes.length === 1) {
    const node = selectedNodes[0]
    currentSelectedNodeId.value = node.id
    selectedNodeId.value = node.id
    selectedNodeType.value = node.data?.wfType || ''
    loadNodeConfig(node)
  } else if (selectedNodes.length === 0) {
    currentSelectedNodeId.value = null
    selectedNodeId.value = ''
    selectedNodeType.value = ''
  } else {
    // 多选时清空配置面板
    currentSelectedNodeId.value = Array.from(selectedIds)[0]
    selectedNodeId.value = `${selectedNodes.length} 个节点`
    selectedNodeType.value = ''
  }
}

// 框选开始
function onSelectionStart() {
  console.log('[工作流] 开始框选')
  ElMessage.info('按住鼠标左键拖拽可框选多个节点')
}

// 框选结束
function onSelectionEnd() {
  console.log('[工作流] 框选结束')
}

function onEdgeClick(event) {
  const edge = event.edge
  if (!edge) return
  selectedEdgeId.value = edge.id
  selectedEdgeCondition.value = edge.data?.condition || edge.label || ''
}

function applyNodeConfig(showMessage = false) {
  console.log('[工作流] 应用节点配置, 节点ID:', selectedNodeId.value, '类型:', selectedNodeType.value)
  if (!selectedNodeId.value) {
    if (showMessage) {
      ElMessage.warning('请先选择节点')
    }
    return
  }

  let config = {}

  // 根据节点类型构建配置
  switch (selectedNodeType.value) {
    case 'input':
      config = {
        key: inputKey.value || 'input',
        default: inputDefault.value
      }
      break
    case 'output':
      config = {
        format: outputFormat.value,
        template: outputTemplate.value
      }
      break
    case 'prompt':
      config = {
        template: promptTemplate.value
      }
      break
    case 'agent':
      config = {
        task: agentTask.value,
        model: agentModel.value
      }
      break
    case 'match':
      config = {
        pattern: matchPattern.value,
        output_field: matchOutputField.value
      }
      break
    case 'branch':
      config = { expression: branchExpression.value }
      break
    case 'for_loop':
      config = {
        start: forLoopStart.value,
        end: forLoopEnd.value,
        step: forLoopStep.value
      }
      break
    case 'tool':
      config = {
        tool: selectedToolName.value,
        outputs: selectedToolOutputs.value
      }
      break
    default:
      config = {}
  }

  // 保存历史
  saveHistory(`更新节点配置:${selectedNodeId.value}`)

  nodes.value = nodes.value.map(node => {
    if (node.id === selectedNodeId.value) {
      return {
        ...node,
        data: {
          ...node.data,
          config
        }
      }
    }
    return node
  })
  syncGraphJson()
  if (showMessage) {
    ElMessage.success('配置已应用')
  }
}

function buildGraphJson() {
  // 构建节点映射，用于边引用验证
  const nodeMap = new Map(nodes.value.map(n => [n.id, n]))

  return {
    version: '2.0',  // 数据版本号，便于后端兼容处理
    metadata: {
      created_at: new Date().toISOString(),
      node_count: nodes.value.length,
      edge_count: edges.value.length
    },
    nodes: nodes.value.map(node => {
      const wfType = node.data?.wfType || 'prompt'
      const config = node.data?.config || {}

      // 构建增强的节点数据
      const nodeData = {
        id: String(node.id),
        type: wfType,
        label: node.data?.label || getDefaultLabel(wfType, config),
        position: node.position,
        config: config,
        // 节点元数据
        metadata: {
          description: getNodeDescription(wfType, config),
          outputs: config.outputs || (wfType === 'tool' ? 1 : undefined),
          // 工具节点额外信息
          ...(wfType === 'tool' ? {
            tool_info: {
              name: config.tool,
              description_cn: getToolDescriptionCN(config.tool),
              arguments_schema: getToolArgumentsSchema(config.tool)
            }
          } : {}),
          // Agent 节点额外信息
          ...(wfType === 'agent' ? {
            agent_info: {
              name: config.name || 'general_agent',
              task: config.task
            }
          } : {})
        }
      }

      return nodeData
    }),
    edges: edges.value.map(edge => {
      const sourceNode = nodeMap.get(edge.source)
      const sourceType = sourceNode?.data?.wfType || 'prompt'

      return {
        id: edge.id,
        source: String(edge.source),
        target: String(edge.target),
        source_handle: edge.sourceHandle,  // 输出端口 ID (true/false/output-0 等)
        target_handle: edge.targetHandle, // 输入端口 ID
        // 边的元数据
        metadata: {
          // 条件分支信息
          condition: edge.data?.condition || edge.label || undefined,
          // 源节点类型（便于后端快速判断）
          source_type: sourceType,
          // 是否为条件分支边
          is_conditional: ['branch', 'for_loop', 'condition'].includes(sourceType)
        }
      }
    }),
    // 入口点信息
    entry: nodes.value.length > 0 ? String(nodes.value[0].id) : undefined
  }
}

// 获取节点默认标签
function getDefaultLabel(type, config) {
  const labels = {
    input: '输入',
    output: '输出',
    prompt: '提示词',
    agent: 'Agent',
    tool: '工具',
    branch: '分支',
    for_loop: '循环',
    match: '匹配'
  }
  if (type === 'tool' && config.tool) {
    return config.tool
  }
  return labels[type] || type
}

// 获取节点描述
function getNodeDescription(type, config) {
  const descriptions = {
    input: '接收用户输入',
    output: '输出结果',
    prompt: '处理提示词模板',
    agent: '执行 Agent 任务',
    tool: `执行工具: ${config.tool || '未选择'}`,
    branch: '条件分支判断',
    for_loop: '循环执行',
    match: '模式匹配提取'
  }
  return descriptions[type] || ''
}

// 获取工具的中文描述
function getToolDescriptionCN(toolName) {
  const toolDescriptions = {
    read_file: '读取指定文件的内容',
    write_file: '创建或修改文件',
    list_directory: '列出目录结构',
    search_content: '搜索文件内容',
    execute_command: '执行终端命令',
    create_directory: '创建目录',
    delete_file: '删除文件',
    generate_tests: '生成测试用例',
    run_tests: '运行测试',
    search_symbol: '搜索代码符号',
    get_code_references: '获取代码引用',
    run_verification_pipeline: '运行验证流水线',
    index_workspace: '索引工作区',
    get_call_graph: '获取调用图',
    get_file_outline: '获取文件大纲',
    verify_with_z3: 'Z3 形式化验证'
  }
  return toolDescriptions[toolName] || ''
}

// 获取工具参数 schema
function getToolArgumentsSchema(toolName) {
  const schemas = {
    read_file: {
      path: { type: 'string', description: '文件路径' }
    },
    write_file: {
      path: { type: 'string', description: '文件路径' },
      content: { type: 'string', description: '文件内容' }
    },
    search_content: {
      pattern: { type: 'string', description: '搜索模式' },
      path: { type: 'string', description: '搜索路径' }
    },
    execute_command: {
      command: { type: 'string', description: '命令内容' }
    }
  }
  return schemas[toolName] || {}
}

function decorateGraph(data) {
  // 处理各种可能的数据格式
  if (!data) {
    data = {}
  }
  // 如果传入的是字符串（JSON），先解析为对象
  if (typeof data === 'string') {
    try {
      data = JSON.parse(data)
    } catch (e) {
      console.error('[前端日志] [ERROR] 解析 graph JSON 失败:', e, '原始数据:', data)
      // 如果解析失败，尝试作为空对象处理
      data = {}
    }
  }
  // 确保 data 是对象
  if (typeof data !== 'object' || data === null) {
    data = {}
  }
  
  nodes.value = (data.nodes || []).map((node, index) => ({
    id: String(node.id),
    type: 'workflow',
    dragHandle: '.drag-handle',
    position: node.position || { x: 120 + index * 80, y: 80 + index * 60 },
    data: {
      wfType: node.type,
      config: node.config || {}
    }
  }))

  // 构建节点 ID 集合，用于验证边的有效性
  const nodeIdSet = new Set(nodes.value.map(n => String(n.id)))

  // 过滤掉 source 或 target 无效的边
  const validEdges = (data.edges || []).filter(
    edge => edge.source && edge.target && nodeIdSet.has(String(edge.source)) && nodeIdSet.has(String(edge.target))
  )

  edges.value = validEdges.map((edge, index) => ({
    id: edge.id || `e-${edge.source}-${edge.target}-${index}`,
    source: String(edge.source),
    sourceHandle: edge.sourceHandle || undefined,
    target: String(edge.target),
    label: edge.condition || '',
    markerEnd: { type: MarkerType.ArrowClosed },
    style: { stroke: '#ffffff', strokeWidth: 2 },
    data: { condition: edge.condition || '' }
  }))

  if (validEdges.length < (data.edges || []).length) {
    console.warn(`[工作流] 过滤了 ${(data.edges || []).length - validEdges.length} 条无效边`)
  }
}

function syncGraphJson() {
  graphJson.value = JSON.stringify(buildGraphJson(), null, 2)
}

function applyGraphJson() {
  try {
    const parsed = JSON.parse(graphJson.value || '{}')
    // 保存历史
    saveHistory('应用JSON配置')
    decorateGraph(parsed)
    ElMessage.success('JSON 已应用')
  } catch (error) {
    ElMessage.error('JSON 解析失败')
  }
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

    await axios.post('/api/workflow/delete/', { id: contextMenuRow.value.id })

    ElMessage.success('工作流已删除')

    // 如果删除的是当前选中的工作流，清空选中状态
    if (currentWorkflowId.value === contextMenuRow.value.id) {
      currentWorkflowId.value = ''
      workflowName.value = ''
      nodes.value = []
      edges.value = []
      syncGraphJson()
    }

    // 刷新列表
    await refreshWorkflows()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除工作流失败:', error)
      ElMessage.error('删除失败: ' + (error.response?.data?.error || error.message))
    }
  }

  closeContextMenu()
}

async function refreshWorkflows() {
  const { data } = await axios.get('/api/workflow/list/', { params: { include_temp: 'true' } })
  workflowList.value = data.workflows || []
}

async function handleCreateWorkflow() {
  const name = workflowName.value || '新工作流'
  // 第一步：先创建只有节点的图
  const createPayload = {
    name,
    graph: {
      nodes: [
        { id: '1', type: 'input', config: { key: 'input' }, position: { x: 100, y: 200 } },
        { id: '2', type: 'agent', config: { task: '', model: '' }, position: { x: 400, y: 200 } },
        { id: '3', type: 'output', config: { format: 'text', template: '{{result}}' }, position: { x: 700, y: 200 } }
      ],
      edges: []
    },
    is_temp: false
  }
  
  // 调用 create API
  const { data } = await axios.post('/api/workflow/create/', createPayload)
  const wf = data.workflow
  
  if (wf) {
    console.log('[DEBUG] ========== create API 返回的完整数据 ==========')
    console.log('[DEBUG] wf:', JSON.stringify(wf, null, 2))
    console.log('[DEBUG] wf.graph:', JSON.stringify(wf.graph, null, 2))
    console.log('[DEBUG] wf.graph 类型:', typeof wf.graph)
    console.log('[DEBUG] ===============================================')
    
    // 从 create API 返回的 graph 中获取节点
    let existingNodes = []
    if (wf.graph) {
      if (typeof wf.graph === 'object' && wf.graph.nodes) {
        existingNodes = wf.graph.nodes
      } else if (typeof wf.graph === 'string') {
        try {
          const parsed = JSON.parse(wf.graph)
          existingNodes = parsed.nodes || []
        } catch (e) {
          console.error('[DEBUG] 解析 wf.graph 失败:', e)
        }
      }
    }
    
    // 第二步：调用 update API 添加边连接节点
    const graphWithEdges = {
      nodes: existingNodes.length > 0 ? existingNodes : [
        { id: '1', type: 'input', config: { key: 'input' }, position: { x: 100, y: 200 } },
        { id: '2', type: 'agent', config: { task: '', model: '' }, position: { x: 400, y: 200 } },
        { id: '3', type: 'output', config: { format: 'text', template: '{{result}}' }, position: { x: 700, y: 200 } }
      ],
      edges: [
        { id: 'e-1-2', source: '1', target: '2', sourceHandle: 'output', targetHandle: 'input' },
        { id: 'e-2-3', source: '2', target: '3', sourceHandle: 'output', targetHandle: 'input' }
      ]
    }
    await axios.post('/api/workflow/update/', {
      id: wf.id,
      name: wf.name,
      graph: graphWithEdges
    })
    
    // 第三步：从服务器获取更新后的工作流数据
    const { data: refreshData } = await axios.get('/api/workflow/get/', { params: { id: wf.id } })
    const updatedWf = refreshData.workflow
    console.log('[DEBUG] get API 返回的 updatedWf.graph:', updatedWf.graph)
    
    workflowList.value.unshift({ id: updatedWf.id, name: updatedWf.name, version: updatedWf.version })
    currentWorkflowId.value = updatedWf.id
    workflowName.value = updatedWf.name
    saveTempWorkflowId('')
    saveLastWorkflowId(updatedWf.id)
    clearHistory()
    decorateGraph(updatedWf.graph)
    syncGraphJson()
    saveHistory(`新建工作流:${name}`, false)
  }
}

async function handleSelectWorkflow(row) {
  const { data } = await axios.get('/api/workflow/get/', { params: { id: row.id } })
  const wf = data.workflow
  if (wf) {
    currentWorkflowId.value = wf.id
    workflowName.value = wf.name
    // 清除临时工作流ID（因为现在选择了正式的工作流）
    saveTempWorkflowId('')
    // 保存最后打开的工作流ID
    saveLastWorkflowId(wf.id)
    // 清空历史并重新初始化
    clearHistory()
    decorateGraph(wf.graph)
    syncGraphJson()
    // 保存初始状态但不加入撤销栈
    saveHistory(`加载工作流:${wf.name}`, false)
  }
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

async function handleSaveWorkflow() {
  if (!currentWorkflowId.value) {
    ElMessage.warning('请先选择工作流')
    return
  }
  const payload = {
    id: currentWorkflowId.value,
    name: workflowName.value || '未命名工作流',
    graph: buildGraphJson()
  }
  console.log('[工作流保存] 开始保存:', currentWorkflowId.value, payload.name)
  sendFrontendLog('info', `[工作流保存] 开始保存: ${currentWorkflowId.value}, ${payload.name}`)
  const { data } = await axios.post('/api/workflow/update/', payload)
  if (data.workflow) {
    ElMessage.success('保存成功')
    console.log('[工作流保存] 保存成功:', currentWorkflowId.value, data.workflow.version)
    sendFrontendLog('info', `[工作流保存] 保存成功: ${currentWorkflowId.value}, 版本 ${data.workflow.version}`)
    // 如果是临时工作流转为正式保存，清除临时工作流记录
    if (tempWorkflowId.value === currentWorkflowId.value) {
      saveTempWorkflowId('')
    }
    await refreshWorkflows()
  }
}

async function handleRunWorkflow() {
  if (isRunning.value) return
  
  let inputValue = runInput.value
  try {
    inputValue = JSON.parse(runInput.value)
  } catch (error) {
    // 使用文本输入
  }

  const graph = buildGraphJson()
  
  // 前端验证：检查是否有可执行的节点
  if (!currentWorkflowId.value && (!graph.nodes || graph.nodes.length === 0)) {
    ElMessage.warning('请先在工作流编辑器中添加节点，或选择一个已保存的工作流')
    return
  }

  const payload = currentWorkflowId.value
    ? { workflow_id: currentWorkflowId.value, input: inputValue }
    : {
        graph: graph,
        input: inputValue
      }

  // 开始运行，禁用按钮
  isRunning.value = true
  runResultHtml.value = ''
  runError.value = ''
  executionTime.value = ''

  try {
    const { data } = await axios.post('/api/workflow/run/', payload)
    if (data.success && data.result) {
      // 格式化结果
      const resultText = typeof data.result === 'string'
        ? data.result
        : JSON.stringify(data.result, null, 2)
      runResultHtml.value = formatMessage(resultText)

      // 添加执行时间
      if (data.execution_info?.execution_time_ms) {
        executionTime.value = `${data.execution_info.execution_time_ms}ms`
      }
      ElMessage.success('工作流执行成功')
    } else if (data.error) {
      runError.value = data.error
      ElMessage.error('执行失败: ' + data.error)
    }
  } catch (error) {
    console.error('工作流执行失败:', error)
    const errorMsg = error.response?.data?.error || error.message || '未知错误'
    runError.value = '执行失败: ' + errorMsg
    ElMessage.error('工作流执行失败: ' + errorMsg)
  } finally {
    // 运行结束，启用按钮
    isRunning.value = false
  }
}

function getMiniMapColor(node) {
  return colorMap[node?.data?.wfType] || '#4a4a4a'
}

watch([nodes, edges], () => {
  syncGraphJson()
  triggerAutoSave()
}, { deep: true })

// 防抖函数 - 避免频繁触发应用配置
let debounceTimer = null
function debouncedApplyNodeConfig() {
  if (debounceTimer) {
    clearTimeout(debounceTimer)
  }
  debounceTimer = setTimeout(() => {
    if (selectedNodeId.value) {
      applyNodeConfig()
    }
  }, 500) // 500ms 延迟
}

// 自动保存函数（防抖）
function triggerAutoSave() {
  const now = Date.now()
  // 避免过于频繁的保存（至少间隔2秒）
  if (now - lastSaveTime < 2000) {
    return
  }

  if (autoSaveTimer) {
    clearTimeout(autoSaveTimer)
  }

  autoSaveTimer = setTimeout(async () => {
    await autoSaveWorkflow()
  }, AUTO_SAVE_DELAY)
}

// 自动保存工作流
async function autoSaveWorkflow() {
  try {
    const graph = buildGraphJson()

    // 检查是否有有效的工作流数据（至少需要一个节点）
    if (!graph.nodes || graph.nodes.length === 0) {
      console.log('[工作流自动保存] 跳过：工作流为空（无节点）')
      return
    }

    // 如果没有选中工作流，创建或更新临时工作流
    if (!currentWorkflowId.value) {
      // 如果没有临时工作流ID，创建新的临时工作流
      if (!tempWorkflowId.value) {
        const name = workflowName.value || 'temp'
        const payload = {
          name,
          graph,
          is_temp: true  // 标记为临时工作流
        }
        const { data } = await axios.post('/api/workflow/create/', payload)
        if (data.workflow) {
          saveTempWorkflowId(data.workflow.id)
          currentWorkflowId.value = data.workflow.id
          workflowName.value = data.workflow.name
          console.log('[工作流自动保存] 创建临时工作流:', data.workflow.id, data.workflow.name)
          sendFrontendLog('info', `[工作流自动保存] 创建临时工作流: ${data.workflow.id}, ${data.workflow.name}`)
        }
      } else {
        // 更新临时工作流
        const name = workflowName.value || 'temp'
        const payload = {
          id: tempWorkflowId.value,
          name,
          graph
        }
        const { data: updateData } = await axios.post('/api/workflow/update/', payload)
        // 更新工作流列表中的版本信息
        if (updateData.workflow) {
          const wf = workflowList.value.find(w => w.id === tempWorkflowId.value)
          if (wf) {
            wf.version = updateData.workflow.version
          }
        }
        console.log('[工作流自动保存] 更新临时工作流:', tempWorkflowId.value, name)
        sendFrontendLog('info', `[工作流自动保存] 更新临时工作流: ${tempWorkflowId.value}, ${name}`)
      }
    } else {
      // 已有选中工作流，直接更新
      const name = workflowName.value || 'temp'
      const payload = {
        id: currentWorkflowId.value,
        name,
        graph
      }
      const { data: updateData } = await axios.post('/api/workflow/update/', payload)
      // 更新工作流列表中的版本信息
      if (updateData.workflow) {
        const wf = workflowList.value.find(w => w.id === currentWorkflowId.value)
        if (wf) {
          wf.version = updateData.workflow.version
        }
      }
      console.log('[工作流自动保存] 更新工作流:', currentWorkflowId.value, name)
      sendFrontendLog('info', `[工作流自动保存] 更新工作流: ${currentWorkflowId.value}, ${name}`)
    }

    lastSaveTime = Date.now()
  } catch (error) {
    console.error('[工作流自动保存] 失败:', error)
    sendFrontendLog('error', `[工作流自动保存] 失败: ${error.message || error}`)
  }
}

// 监听节点配置变量变化，自动应用配置
watch([
  inputKey,
  inputDefault,
  outputFormat,
  outputTemplate,
  promptTemplate,
  agentTask,
  agentModel,
  matchPattern,
  matchOutputField,
  branchExpression,
  forLoopStart,
  forLoopEnd,
  forLoopStep,
  selectedToolName,
  selectedToolOutputs
], () => {
  debouncedApplyNodeConfig()
}, { deep: true })

// 删除选中的节点
async function deleteSelectedNode() {
  // 检查是否有多选节点
  if (multiSelectedNodeIds.value.size > 1) {
    // 删除多个节点
    await deleteMultipleNodes()
    return
  }

  if (!selectedNodeId.value) return

  const nodeId = selectedNodeId.value
  const nodeIdStr = String(nodeId)

  console.log('[删除节点] 开始删除, nodeId:', nodeIdStr)
  console.log('[删除节点] 删除前 edges:', edges.value.map(e => e.id))

  // 找到需要删除的边（连接到被删除节点的边）
  const edgesToRemove = edges.value.filter(edge =>
    String(edge.source) === nodeIdStr || String(edge.target) === nodeIdStr
  )

  console.log('[删除节点] 需要删除的边:', edgesToRemove.map(e => e.id))

  // 找到需要删除的节点
  const nodeToRemove = nodes.value.find(node => String(node.id) === nodeIdStr)

  if (nodeToRemove) {
    // 保存历史
    saveHistory(`删除节点:${nodeId}`)
    
    // 先删除边，再删除节点（使用 Vue Flow API）
    if (edgesToRemove.length > 0) {
      removeEdges(edgesToRemove)
    }
    removeNodes([nodeToRemove])

    console.log('[删除节点] 使用 Vue Flow API 删除完成')
  }

  selectedNodeId.value = ''
  selectedNodeType.value = ''
  multiSelectedNodeIds.value = new Set()
  syncGraphJson()
  ElMessage.success('节点已删除')
}

// 删除多个节点
async function deleteMultipleNodes() {
  const nodeIds = Array.from(multiSelectedNodeIds.value)
  const nodeIdsStr = nodeIds.map(id => String(id))

  console.log('[删除节点] 开始删除多个节点, nodeIds:', nodeIdsStr)

  // 找到需要删除的边（连接到被删除节点的边）
  const edgesToRemove = edges.value.filter(edge =>
    nodeIdsStr.includes(String(edge.source)) || nodeIdsStr.includes(String(edge.target))
  )

  console.log('[删除节点] 需要删除的边:', edgesToRemove.map(e => e.id))

  // 找到需要删除的节点
  const nodesToRemove = nodes.value.filter(node => nodeIdsStr.includes(String(node.id)))

  if (nodesToRemove.length > 0) {
    // 保存历史
    saveHistory(`删除${nodesToRemove.length}个节点`)
    
    // 先删除边，再删除节点（使用 Vue Flow API）
    if (edgesToRemove.length > 0) {
      removeEdges(edgesToRemove)
    }
    removeNodes(nodesToRemove)

    console.log('[删除节点] 使用 Vue Flow API 删除多个节点完成')
  }

  selectedNodeId.value = ''
  selectedNodeType.value = ''
  multiSelectedNodeIds.value = new Set()
  syncGraphJson()
  ElMessage.success(`已删除 ${nodesToRemove.length} 个节点`)
}

// Debug: 显示当前节点和边的状态
function showDebugInfo() {
  const nodeCount = nodes.value.length
  const edgeCount = edges.value.length

  // 统计每个节点的连接数
  const connectionInfo = nodes.value.map(node => {
    const nodeId = String(node.id)
    const sourceCount = edges.value.filter(e => String(e.source) === nodeId).length
    const targetCount = edges.value.filter(e => String(e.target) === nodeId).length
    return {
      id: nodeId,
      type: node.data?.wfType || 'unknown',
      sourceCount,
      targetCount,
      total: sourceCount + targetCount
    }
  })

  // 边的详情
  const edgeDetails = edges.value.map(edge => ({
    id: edge.id,
    source: edge.source,
    target: edge.target,
    sourceHandle: edge.sourceHandle,
    targetHandle: edge.targetHandle
  }))

  const debugInfo = {
    summary: {
      nodeCount,
      edgeCount,
      selectedNodeId: selectedNodeId.value || '无'
    },
    nodes: connectionInfo,
    edges: edgeDetails
  }

  console.log('[Debug] 当前工作流状态:', debugInfo)

  // 用弹窗显示
  ElMessage({
    message: `节点: ${nodeCount}, 边: ${edgeCount}, 选中: ${selectedNodeId.value || '无'}`,
    type: 'info',
    duration: 3000
  })

  // 详细日志输出到控制台
  console.table(connectionInfo)
  console.table(edgeDetails)
}

// 注释掉 watch，避免在删除节点时触发 syncGraphJson 导致边被清空
// watch([() => nodes.value, () => edges.value], () => {
//   syncGraphJson()
// }, { flush: 'post' })

// 键盘事件
function onKeyDown(event) {
  // Ctrl+Z 撤销
  if (event.ctrlKey && event.key === 'z') {
    console.log('[前端日志] [INFO] 检测到 Ctrl+Z 按键 | 事件时间戳:', event.timeStamp)
    event.preventDefault()
    undo()
    return
  }
  
  // Delete 删除节点
  if (event.key === 'Delete') {
    if (selectedNodeId.value) {
      event.preventDefault()
      deleteSelectedNode()
    }
  }
}

// 初始化默认工作流（输入 -> Agent -> 输出）
function initDefaultWorkflow() {
  const inputId = 'input-' + Date.now()
  const agentId = 'agent-' + (Date.now() + 1)
  const outputId = 'output-' + Date.now() + 2

  console.log('[工作流] 初始化默认工作流:', { inputId, agentId, outputId })

  // 先设置节点
  const newNodes = [
    {
      id: inputId,
      type: 'workflow',
      dragHandle: '.drag-handle',
      position: { x: 50, y: 200 },
      label: '输入',
      data: { wfType: 'input', config: {} }
    },
    {
      id: agentId,
      type: 'workflow',
      dragHandle: '.drag-handle',
      position: { x: 300, y: 200 },
      label: 'Agent',
      data: { wfType: 'agent', config: { task: '' } }
    },
    {
      id: outputId,
      type: 'workflow',
      dragHandle: '.drag-handle',
      position: { x: 550, y: 200 },
      label: '输出',
      data: { wfType: 'output', config: {} }
    }
  ]

  nodes.value = [...newNodes]

  console.log('[工作流] 节点设置完成, nodes:', nodes.value)

  // 使用 Vue Flow API 添加边（与手动连接风格一致）
  const newEdges = [
    {
      id: `e-${inputId}-${agentId}`,
      source: inputId,
      target: agentId,
      markerEnd: { type: MarkerType.ArrowClosed },
      style: { stroke: '#ffffff', strokeWidth: 2 },
      data: { condition: '' }
    },
    {
      id: `e-${agentId}-${outputId}`,
      source: agentId,
      target: outputId,
      markerEnd: { type: MarkerType.ArrowClosed },
      style: { stroke: '#ffffff', strokeWidth: 2 },
      data: { condition: '' }
    }
  ]

  // 使用 addEdges API 添加边
  nextTick(() => {
    addEdges(newEdges)
    console.log('[工作流] 使用 addEdges API 添加边完成, edges:', edges.value)
    syncGraphJson()
    // 默认工作流不加入 undo 栈，清空历史
    clearHistory()
  })
}

// JSON 面板高度调整
const jsonPanelHeight = ref(280) // 默认高度
const isResizing = ref(false)
const startY = ref(0)
const startHeight = ref(0)

function startResize(event) {
  isResizing.value = true
  startY.value = event.clientY
  startHeight.value = jsonPanelHeight.value
  document.body.style.cursor = 'ns-resize'
  document.body.style.userSelect = 'none'
}

function handleResize(event) {
  if (!isResizing.value) return
  
  const deltaY = startY.value - event.clientY
  const newHeight = Math.max(100, Math.min(500, startHeight.value + deltaY))
  jsonPanelHeight.value = newHeight
}

function stopResize() {
  if (isResizing.value) {
    isResizing.value = false
    document.body.style.cursor = ''
    document.body.style.userSelect = ''
  }
}

// 恢复临时工作流
async function restoreTempWorkflow() {
  const savedTempId = localStorage.getItem('temp_workflow_id')
  console.log('[前端日志] [INFO] 尝试恢复工作流 | savedTempId:', savedTempId)
  if (savedTempId) {
    try {
      console.log('[前端日志] [INFO] 正在获取工作流数据 | id:', savedTempId)
      const { data } = await axios.get('/api/workflow/get/', { params: { id: savedTempId } })
      const wf = data.workflow
      if (wf && wf.is_temp) {
        currentWorkflowId.value = wf.id
        workflowName.value = wf.name
        tempWorkflowId.value = wf.id
        decorateGraph(wf.graph)
        syncGraphJson()
        clearHistory()
        saveHistory(`恢复临时工作流:${wf.name}`, false)
        console.log('[前端日志] [INFO] 已恢复临时工作流 | id:', wf.id, 'name:', wf.name)
        return true
      } else {
        // 临时工作流已不存在，清除 localStorage
        console.log('[前端日志] [WARN] 临时工作流不存在或已不是临时工作流 | id:', savedTempId)
        saveTempWorkflowId('')
      }
    } catch (e) {
      console.warn('[前端日志] [ERROR] 恢复临时工作流失败:', e)
      saveTempWorkflowId('')
    }
  } else {
    console.log('[前端日志] [INFO] localStorage 中无 temp_workflow_id，不恢复')
  }
  return false
}

// 恢复最后打开的工作流
async function restoreLastWorkflow() {
  const savedId = localStorage.getItem('last_workflow_id')
  if (savedId) {
    try {
      const { data } = await axios.get('/api/workflow/get/', { params: { id: savedId } })
      const wf = data.workflow
      if (wf) {
        currentWorkflowId.value = wf.id
        workflowName.value = wf.name
        // 如果是临时工作流，也更新 tempWorkflowId
        if (wf.is_temp) {
          saveTempWorkflowId(wf.id)
        }
        clearHistory()
        decorateGraph(wf.graph)
        syncGraphJson()
        saveHistory(`恢复工作流:${wf.name}`, false)
        console.log('[前端日志] [INFO] 已恢复最后打开的工作流 | id:', wf.id, 'name:', wf.name)
        return true
      } else {
        // 工作流已不存在，清除 localStorage
        console.log('[前端日志] [WARN] 最后打开的工作流不存在 | id:', savedId)
        saveLastWorkflowId('')
      }
    } catch (e) {
      console.warn('[前端日志] [ERROR] 恢复最后打开的工作流失败:', e)
      saveLastWorkflowId('')
    }
  } else {
    console.log('[前端日志] [INFO] localStorage 中无 last_workflow_id，不恢复')
  }
  return false
}

// 创建默认临时工作流
async function createDefaultTempWorkflow() {
  const payload = {
    name: '新工作流',
    graph: {
      nodes: [
        { id: 'input-' + Date.now(), type: 'input', config: { key: 'input' }, position: { x: 120, y: 80 } },
        { id: 'agent-' + (Date.now() + 1), type: 'agent', config: { task: '', model: '' }, position: { x: 120, y: 200 } },
        { id: 'output-' + (Date.now() + 2), type: 'output', config: { format: 'text', template: '{{result}}' }, position: { x: 120, y: 320 } }
      ],
      edges: []
    },
    is_temp: true  // 临时工作流
  }
  try {
    const { data } = await axios.post('/api/workflow/create/', payload)
    const wf = data.workflow
    if (wf) {
      currentWorkflowId.value = wf.id
      workflowName.value = wf.name
      saveTempWorkflowId(wf.id)
      saveLastWorkflowId(wf.id)
      clearHistory()
      decorateGraph(wf.graph)
      syncGraphJson()
      saveHistory(`创建默认临时工作流:${wf.name}`, false)
      console.log('[前端日志] [INFO] 已创建默认临时工作流 | id:', wf.id, 'name:', wf.name)
      return true
    }
  } catch (e) {
    console.error('[前端日志] [ERROR] 创建默认临时工作流失败:', e)
  }
  return false
}

onMounted(async () => {
  refreshWorkflows()
  loadToolList()
  loadModelList()

  // 优先级：最后打开的工作流 > 临时工作流 > 创建默认临时工作流
  let restored = await restoreLastWorkflow()

  // 如果没有恢复最后打开的工作流，尝试恢复临时工作流
  if (!restored) {
    restored = await restoreTempWorkflow()
  }

  // 如果都没有恢复，创建默认临时工作流
  if (!restored) {
    // 延迟创建，确保 Vue Flow 视口已准备好
    nextTick(() => {
      setTimeout(async () => {
        if (nodes.value.length === 0) {
          await createDefaultTempWorkflow()
        }
      }, 100)
    })
  }

  // 添加键盘监听
  console.log('[前端日志] [INFO] WorkflowPanel 挂载 | 添加键盘监听器')
  window.addEventListener('keydown', onKeyDown)
  // 添加分隔条拖拽监听
  document.addEventListener('mousemove', handleResize)
  document.addEventListener('mouseup', stopResize)
  // 点击其他地方关闭右键菜单
  document.addEventListener('click', closeContextMenu)
})

onBeforeUnmount(() => {
  console.log('[前端日志] [INFO] WorkflowPanel 卸载 | 移除键盘监听器')
  // 移除键盘监听
  window.removeEventListener('keydown', onKeyDown)
  // 移除分隔条拖拽监听
  document.removeEventListener('mousemove', handleResize)
  document.removeEventListener('mouseup', stopResize)
  // 移除右键菜单监听
  document.removeEventListener('click', closeContextMenu)
  // 清理自动保存定时器
  if (autoSaveTimer) {
    clearTimeout(autoSaveTimer)
  }
})
</script>

<style scoped>
.workflow-panel {
  display: flex;
  flex-direction: column;
  gap: 12px;
  height: 100%;
  padding: 16px 20px 16px 16px;
  box-sizing: border-box;
}

.panel-header {
  display: flex;
  gap: 8px;
  align-items: center;
}

.panel-body {
  display: grid;
  grid-template-columns: 260px 1fr 280px;
  gap: 12px;
  flex: 1;
  min-height: 0;
}

.section-title {
  font-weight: 600;
  margin-bottom: 8px;
}

/* 当前选中的工作流行高亮 */
:deep(.current-workflow-row) {
  background-color: rgba(64, 158, 255, 0.2) !important;
}

:deep(.current-workflow-row td) {
  background-color: transparent !important;
}

.workflow-list,
.workflow-editor,
.workflow-run {
  background: #1e1e1e;
  border: 1px solid #333;
  border-radius: 12px;
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  position: relative;
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

.workflow-editor {
  gap: 12px;
}

.editor-layout {
  display: grid;
  grid-template-columns: 220px 1fr;
  gap: 12px;
  flex: 1;
  min-height: 0;
}

.node-palette {
  border: 1px solid #333;
  border-radius: 10px;
  padding: 10px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  background: #181818;
}

/* 节点配置文本框暗色主题 */
.node-palette :deep(.el-textarea__inner) {
  background: #1a1a1a;
  color: #e0e0e0;
  border-color: #333;
}

.node-palette :deep(.el-input__wrapper) {
  background: #1a1a1a;
  box-shadow: none !important;
  border-color: #333;
}

.node-palette :deep(.el-input__inner) {
  color: #e0e0e0;
}

.palette-title {
  font-size: 12px;
  color: #9aa0a6;
  margin-top: 4px;
}

.palette-item {
  padding: 10px 12px;
  border-radius: 12px;
  background: #252526;
  cursor: grab;
  text-transform: capitalize;
  color: #d1d5db;
  text-align: center;
  font-weight: 600;
  font-size: 13px;
  border: 2px solid var(--node-color, #555);
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
  position: relative;
  overflow: hidden;
}

.palette-item::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: var(--node-color);
  opacity: 0;
  transition: opacity 0.25s ease;
  z-index: 0;
}

.palette-item:hover {
  transform: translateY(-2px) scale(1.02);
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.35), 0 0 12px var(--node-color, #555);
  border-color: var(--node-color, #555);
}

.palette-item:hover::before {
  opacity: 0.15;
}

.palette-item span,
.palette-item {
  position: relative;
  z-index: 1;
}

.palette-item:active {
  cursor: grabbing;
}

.config-section {
  margin-bottom: 10px;
}

.config-label {
  font-size: 12px;
  color: #9aa0a6;
  margin-bottom: 4px;
}

/* el-input-number 暗色样式 */
.config-section :deep(.el-input-number) {
  width: 100%;
}

.flow-canvas {
  border: 1px solid #333;
  border-radius: 12px;
  min-height: 420px;
  background: #141414;
  overflow: hidden;
}

.vue-flow {
  width: 100%;
  height: 100%;
}

.workflow-run {
  gap: 10px;
}

/* 对话式结果显示样式 */
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

/* 可拖拽分隔条 */
.resizer {
  height: 6px;
  background: #2a2a2a;
  cursor: ns-resize;
  transition: background 0.2s;
  border-radius: 3px;
  margin: 4px 0;
  position: relative;
}

.resizer:hover {
  background: #3a3a3a;
}

.resizer::after {
  content: '';
  position: absolute;
  left: 50%;
  top: 50%;
  transform: translate(-50%, -50%);
  width: 30px;
  height: 2px;
  background: #555;
  border-radius: 1px;
}

.resizer:hover::after {
  background: #666;
}

/* JSON 面板样式 */
.json-panel {
  display: flex;
  flex-direction: column;
  border: 1px solid #333;
  border-radius: 8px;
  background: #1a1a1a;
  overflow: hidden;
}

.json-header {
  padding: 12px;
  background: #1a1a1a;
  color: #e0e0e0;
  font-size: 14px;
  font-weight: 600;
  border-bottom: 1px solid #333;
}

.json-panel :deep(.json-textarea) {
  flex: 1;
  min-height: 0;
}

.json-panel :deep(.json-textarea .el-textarea__inner) {
  border: none;
  border-radius: 0;
  background: #141414;
  color: #e0e0e0;
  resize: none;
  height: 100%;
}

.workflow-editor :deep(.el-textarea__inner) {
  background: #141414;
  color: #e0e0e0;
  border: 1px solid #333;
  border-radius: 6px;
}

.workflow-editor :deep(.el-textarea__inner:focus) {
  border-color: #4a90e2;
}

/* JSON textarea 滚动条暗色主题 */
.workflow-editor :deep(.el-textarea__inner)::-webkit-scrollbar {
  width: 10px;
  height: 10px;
}

.workflow-editor :deep(.el-textarea__inner)::-webkit-scrollbar-track {
  background: #1a1a1a;
  border-radius: 5px;
}

.workflow-editor :deep(.el-textarea__inner)::-webkit-scrollbar-thumb {
  background: #3a3a3a;
  border-radius: 5px;
  border: 2px solid #1a1a1a;
}

.workflow-editor :deep(.el-textarea__inner)::-webkit-scrollbar-thumb:hover {
  background: #4a4a4a;
}

.workflow-editor :deep(.el-textarea__inner)::-webkit-scrollbar-corner {
  background: #1a1a1a;
}

/* MiniMap 暗色主题 */
:deep(.vue-flow__minimap) {
  background: #141414 !important;
  border-radius: 8px;
  border: 1px solid #333;
}

:deep(.vue-flow__minimap_mask) {
  fill: rgba(20, 20, 20, 0.8);
}

:deep(.vue-flow__minimap_node) {
  fill: #3a86ff;
}

/* Controls 暗色主题 */
:deep(.vue-flow__controls) {
  background: #1e1e1e !important;
  border: 1px solid #333;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
}

:deep(.vue-flow__controls-button) {
  background: #1e1e1e !important;
  border-bottom: 1px solid #333;
  color: #e0e0e0;
  fill: #e0e0e0;
  width: 28px;
  height: 28px;
}

:deep(.vue-flow__controls-button:hover) {
  background: #2a2a2a !important;
  color: #4fc3f7;
  fill: #4fc3f7;
}

:deep(.vue-flow__controls-button:last-child) {
  border-bottom: none;
}

:deep(.vue-flow__controls-button svg) {
  fill: currentColor;
}

/* 框选框样式 */
:deep(.vue-flow__selection) {
  background: rgba(59, 130, 246, 0.15);
  border: 1px dashed rgba(59, 130, 246, 0.8);
  border-radius: 4px;
}

/* 框选框增强样式 - 更明显的视觉效果 */
::deep(.vue-flow__selection:active) {
  background: rgba(59, 130, 246, 0.25);
  border-color: rgba(59, 130, 246, 1);
  box-shadow: 0 0 15px rgba(59, 130, 246, 0.5);
  border-width: 2px;
  border-style: solid;
}

</style>
