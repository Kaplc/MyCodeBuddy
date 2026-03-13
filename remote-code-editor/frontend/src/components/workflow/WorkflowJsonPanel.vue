<template>
  <div v-show="jsonPanelHeight > 0" class="json-panel" :style="{ height: jsonPanelHeight + 'px', overflow: 'hidden' }">
    <div class="json-header">Graph JSON</div>
    <el-input v-model="graphJson" type="textarea" :rows="8" resize="none" class="json-textarea" />
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'

const props = defineProps({
  modelValue: {
    type: String,
    default: ''
  },
  jsonPanelHeight: {
    type: Number,
    default: 280
  }
})

const emit = defineEmits(['update:modelValue', 'update:jsonPanelHeight', 'resize-start', 'resize-stop'])

// 双向绑定 v-model
const graphJson = ref(props.modelValue)

watch(() => props.modelValue, (newVal) => {
  graphJson.value = newVal
})

watch(graphJson, (newVal) => {
  emit('update:modelValue', newVal)
})

// 重新调整大小
const isResizing = ref(false)
const startY = ref(0)
const startHeight = ref(0)

function startResize(event) {
  isResizing.value = true
  startY.value = event.clientY
  startHeight.value = props.jsonPanelHeight
  document.body.style.cursor = 'ns-resize'
  document.body.style.userSelect = 'none'
  emit('resize-start')
}

function handleResize(event) {
  if (!isResizing.value) return

  const deltaY = startY.value - event.clientY
  const newHeight = Math.max(100, Math.min(500, startHeight.value + deltaY))
  emit('update:jsonPanelHeight', newHeight)
}

function stopResize() {
  if (isResizing.value) {
    isResizing.value = false
    document.body.style.cursor = ''
    document.body.style.userSelect = ''
    emit('resize-stop')
  }
}

// 暴露给父组件
defineExpose({
  startResize,
  handleResize,
  stopResize
})
</script>

<style scoped>
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
</style>
