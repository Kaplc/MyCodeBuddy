<template>
  <div class="workflow-node" :class="{ 'is-selected': isSelected }" :style="{ borderColor: accent, boxShadow: glow }">
    <div class="node-header drag-handle" :style="{ background: accent }">
      <span class="node-title">{{ displayName }}</span>
    </div>
    <div class="node-body">
      <!-- Branch 节点: 内置条件输入框 -->
      <template v-if="nodeType === 'branch'">
        <textarea 
          class="condition-input"
          :value="expression"
          @input="onExpressionChange($event)"
          placeholder="输入条件..."
          rows="2"
        />
      </template>
      <!-- ForLoop 节点: 内置循环配置 -->
      <template v-else-if="nodeType === 'for_loop'">
        <div class="forloop-config">
          <span class="loop-label">{{ start }} - {{ end }}</span>
        </div>
      </template>
      <!-- Agent 节点: 任务描述输入框 -->
      <template v-else-if="nodeType === 'agent'">
        <textarea 
          class="condition-input"
          :value="task"
          @input="onTaskChange($event)"
          placeholder="输入任务描述..."
          rows="2"
        />
      </template>
      <!-- Match 节点: 提取字段描述输入框 -->
      <template v-else-if="nodeType === 'match'">
        <textarea 
          class="condition-input"
          :value="matchPattern"
          @input="onMatchChange($event)"
          placeholder="输入要提取的内容描述..."
          rows="2"
        />
      </template>
      <!-- Tool 节点: 显示选中的工具名称 -->
      <template v-else-if="nodeType === 'tool'">
        <span class="node-tool-name">{{ selectedTool }}</span>
      </template>
      <!-- 其他节点 -->
      <template v-else>
        <span class="node-subtitle">{{ subtitle }}</span>
      </template>
    </div>
    <Handle type="target" :position="Position.Left" id="input" class="node-handle" :style="{ background: accent }" />
    
    <!-- 普通节点: 单个输出 -->
    <Handle 
      v-if="!multiOutputNodes.includes(nodeType)"
      type="source" 
      id="output"
      :position="Position.Right" 
      class="node-handle" 
      :style="{ background: accent }" 
    />
    
    <!-- Branch 节点: True/False 分支 -->
    <template v-else-if="nodeType === 'branch'">
      <div class="multi-outputs">
        <div class="output-branch true-branch">
          <span class="branch-label">True</span>
          <Handle 
            type="source" 
            id="true"
            :position="Position.Right" 
            class="node-handle true-handle" 
          />
        </div>
        <div class="output-branch false-branch">
          <Handle 
            type="source" 
            id="false"
            :position="Position.Right" 
            class="node-handle false-handle" 
          />
          <span class="branch-label">False</span>
        </div>
      </div>
    </template>
    
    <!-- ForLoop 节点: Loop/Completed 分支 -->
    <template v-else-if="nodeType === 'for_loop'">
      <div class="multi-outputs">
        <div class="output-branch loop-branch">
          <span class="branch-label">Loop</span>
          <Handle 
            type="source" 
            id="loop"
            :position="Position.Right" 
            class="node-handle loop-handle" 
          />
        </div>
        <div class="output-branch completed-branch">
          <Handle 
            type="source" 
            id="completed"
            :position="Position.Right" 
            class="node-handle completed-handle" 
          />
          <span class="branch-label">Completed</span>
        </div>
      </div>
    </template>
    
    <!-- Tool 节点: 根据输出数量渲染端口 -->
    <template v-else-if="nodeType === 'tool' && toolOutputs > 1">
      <div class="multi-outputs">
        <div 
          v-for="i in toolOutputs" 
          :key="i" 
          class="output-branch tool-branch"
        >
          <Handle 
            type="source" 
            :id="'output-' + (i - 1)"
            :position="Position.Right" 
            class="node-handle tool-handle" 
            :style="{ background: accent }"
          />
          <span class="branch-label">输出{{ i }}</span>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { computed, onMounted, nextTick, watch } from 'vue'
import { Handle, Position } from '@vue-flow/core'

const props = defineProps({
  data: {
    type: Object,
    default: () => ({})
  },
  selected: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['update:data'])

const typeMap = {
  input: 'Input',
  prompt: 'Prompt',
  agent: 'Agent',
  tool: 'Tool',
  output: 'Output',
  // 流程控制节点
  branch: 'Branch',
  for_loop: 'ForLoop',
  // 匹配节点
  match: 'Match'
}

const colorMap = {
  input: '#4cc9f0',
  prompt: '#4895ef',
  agent: '#3a86ff',
  tool: '#43aa8b',
  output: '#9b5de5',
  // 流程控制节点颜色
  branch: '#f4a261',
  for_loop: '#e879f9',
  // 匹配节点颜色
  match: '#06b6d4'
}

const nodeType = computed(() => props.data?.wfType || 'prompt')
const displayName = computed(() => typeMap[nodeType.value] || nodeType.value)
const subtitle = computed(() => props.data?.subtitle || '')
const selectedTool = computed(() => props.data?.config?.tool || '未选择工具')
const accent = computed(() => colorMap[nodeType.value] || '#409eff')
const glow = computed(() => `0 6px 16px rgba(0, 0, 0, 0.35)`)

// Branch 节点条件表达式
const expression = computed(() => props.data?.config?.expression || '')
// ForLoop 节点循环范围
const start = computed(() => props.data?.config?.start ?? 0)
const end = computed(() => props.data?.config?.end ?? 10)
const step = computed(() => props.data?.config?.step ?? 1)
// Agent 节点任务描述
const task = computed(() => props.data?.config?.task || '')
// Match 节点提取模式
const matchPattern = computed(() => props.data?.config?.matchPattern || '')

// 选中状态 - VueFlow的selected属性在props根级别，不在data里
const isSelected = computed(() => props.selected === true)

// 监听选中状态变化
watch(isSelected, (newVal, oldVal) => {
  console.log('[WorkflowNode] 选中状态变化:', newVal, '节点类型:', nodeType.value, '节点ID:', props.id)
})

// 多输出节点类型
const multiOutputNodes = ['branch', 'for_loop']

// Tool 节点输出数量
const toolOutputs = computed(() => {
  if (nodeType.value !== 'tool') return 1
  return props.data?.config?.outputs || 1
})

// 条件变化处理
function onExpressionChange(event) {
  const newValue = event.target.value
  if (props.data) {
    props.data.config = { ...props.data.config, expression: newValue }
    emit('update:data', props.data)
  }
  // 自动调整高度
  autoResize(event.target)
}

// Agent 任务变化处理
function onTaskChange(event) {
  const newValue = event.target.value
  if (props.data) {
    props.data.config = { ...props.data.config, task: newValue }
    emit('update:data', props.data)
  }
  // 自动调整高度
  autoResize(event.target)
}

// Match 节点提取描述变化处理
function onMatchChange(event) {
  const newValue = event.target.value
  if (props.data) {
    props.data.config = { ...props.data.config, pattern: newValue }
    emit('update:data', props.data)
  }
  // 自动调整高度
  autoResize(event.target)
}

// 自动调整textarea高度
function autoResize(textarea) {
  textarea.style.height = 'auto'
  textarea.style.height = textarea.scrollHeight + 'px'
}

// 组件挂载后初始化高度
onMounted(() => {
  nextTick(() => {
    const textareas = document.querySelectorAll('.condition-input')
    textareas.forEach(textarea => {
      autoResize(textarea)
    })
  })
})
</script>

<style scoped>
.workflow-node {
  min-width: 180px;
  border-radius: 14px;
  border: 1px solid #2a2a2a;
  background: linear-gradient(145deg, #0f1115, #141821);
  overflow: hidden;
  color: #e8e8e8;
  box-shadow: 0 10px 26px rgba(0, 0, 0, 0.35);
  transition: border-color 0.2s, box-shadow 0.2s;
}

/* 选中节点高亮 */
:deep(.vue-flow__node--selected) .workflow-node {
  border-color: #ffffff !important;
  box-shadow: 0 0 0 2px rgba(255, 255, 255, 0.6), 0 10px 26px rgba(0, 0, 0, 0.35) !important;
}

.node-header {
  padding: 10px 14px;
  font-weight: 700;
  font-size: 13px;
  color: #0a0a0a;
  letter-spacing: 0.4px;
}

.node-body {
  padding: 12px 14px 14px;
  min-height: 38px;
  display: flex;
  align-items: flex-start;
  background: rgba(255, 255, 255, 0.02);
  border-top: 1px solid rgba(255, 255, 255, 0.04);
}

.node-title {
  letter-spacing: 0.5px;
}

.node-subtitle {
  font-size: 12px;
  color: #c7ced7;
}

.node-tool-name {
  font-size: 12px;
  color: #43aa8b;
  font-weight: 500;
}

.condition-input {
  width: 100%;
  box-sizing: border-box;
  min-height: 24px;
  max-height: 120px;
  padding: 4px 8px;
  background: rgba(0, 0, 0, 0.3);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 4px;
  color: #e0e0e0;
  font-size: 11px;
  font-family: inherit;
  line-height: 1.4;
  outline: none;
  resize: none;
  overflow: hidden;
  display: block;
  word-wrap: break-word;
  word-break: break-all;
}

.condition-input:focus {
  border-color: #f4a261;
}

.condition-input::placeholder {
  color: #666;
}

.forloop-config {
  font-size: 11px;
  color: #a855f7;
}

.loop-label {
  font-weight: 500;
}

.node-handle {
  width: 10px;
  height: 10px;
  border: 2px solid #0c0d11;
  box-shadow: 0 0 0 3px rgba(0, 0, 0, 0.4);
}

.multi-outputs {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-top: 8px;
  padding: 8px 0;
}

.output-branch {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 4px 10px;
  position: relative;
}

.branch-label {
  font-size: 11px;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 4px;
  letter-spacing: 0.5px;
}

.true-branch .branch-label {
  color: #22c55e;
  background: rgba(34, 197, 94, 0.15);
}

.false-branch .branch-label {
  color: #ef4444;
  background: rgba(239, 68, 68, 0.15);
}

.loop-branch .branch-label {
  color: #a855f7;
  background: rgba(168, 85, 247, 0.15);
}

.completed-branch .branch-label {
  color: #64748b;
  background: rgba(100, 116, 139, 0.15);
}

.true-handle {
  background: #22c55e !important;
}

.false-handle {
  background: #ef4444 !important;
}

.loop-handle {
  background: #a855f7 !important;
}

.completed-handle {
  background: #64748b !important;
}

/* 全局选中高亮 */
.vue-flow__node--selected .workflow-node,
:deep(.vue-flow__node--selected) .workflow-node,
.is-selected .workflow-node,
:deep(.node-multi-selected) .workflow-node,
.vue-flow__node.node-multi-selected .workflow-node {
  border-color: #ffffff !important;
  box-shadow: 0 0 0 2px rgba(255, 255, 255, 0.6), 0 10px 26px rgba(0, 0, 0, 0.35) !important;
}
</style>
