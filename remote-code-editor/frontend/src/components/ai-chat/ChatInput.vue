<template>
  <div class="input-container">
    <!-- 生成中状态指示器 -->
    <div v-if="isStreaming" class="streaming-indicator">
      <span class="streaming-dot"></span>
      <span>生成中...</span>
    </div>
    
    <!-- 文件引用显示 -->
    <div v-if="attachedFiles.length > 0" class="attached-files">
      <div v-for="(file, index) in attachedFiles" :key="index" class="file-tag">
        <el-icon><Document /></el-icon>
        <span class="file-name">{{ file.name }}</span>
        <el-icon class="remove-icon" @click="removeFile(index)"><Close /></el-icon>
      </div>
    </div>
    
    <el-input
      v-model="localInputMessage"
      type="textarea"
      :rows="3"
      placeholder="输入消息，按Enter发送，Shift+Enter换行..."
      @keydown.enter.exact="handleSend"
    />
    <div class="input-footer">
      <div class="select-group">
        <!-- 文件引用按钮 -->
        <el-button
          size="small"
          @click="handleAttachFile"
          :disabled="isStreaming"
          class="attach-button"
          title="引用文件"
        >
          <el-icon><Paperclip /></el-icon>
        </el-button>
        
        <!-- AI模式选择 -->
        <el-select v-model="localAiMode" placeholder="Mode" size="small" style="width: 100px">
          <template #prefix>
            <el-icon v-if="localAiMode === 'ask'"><ChatDotRound /></el-icon>
            <el-icon v-else-if="localAiMode === 'agent'"><Setting /></el-icon>
          </template>
          <el-option label="Ask" value="ask">
            <el-icon><ChatDotRound /></el-icon>
            <span>Ask</span>
          </el-option>
          <el-option label="Agent" value="agent">
            <el-icon><Setting /></el-icon>
            <span>Agent</span>
          </el-option>
        </el-select>
        
        <!-- 模型选择 -->
        <el-select v-model="localSelectedModel" placeholder="选择模型" size="small" style="width: 150px">
          <template #prefix>
            <img :src="GlmIcon" class="model-icon" />
          </template>
          <el-option label="GLM-4.7-Flash" value="glm-4-flash">
            <img :src="GlmIcon" class="option-icon" />
            <span>GLM-4.7-Flash</span>
          </el-option>
          <el-option label="GLM-4.6-Flash" value="glm-4v-flash">
            <img :src="GlmIcon" class="option-icon" />
            <span>GLM-4.6-Flash</span>
          </el-option>
        </el-select>
      </div>
      <el-button
        v-if="!isStreaming"
        type="primary"
        :disabled="!localInputMessage.trim() || aiStatus === 'disconnected'"
        @click="handleSendClick"
        class="send-button"
        :class="{ disconnected: aiStatus === 'disconnected' }"
        :title="aiStatus === 'disconnected' ? '网络已断开' : '发送消息'"
      >
        <el-icon v-if="aiStatus === 'disconnected'"><Warning /></el-icon>
        <el-icon v-else><Promotion /></el-icon>
      </el-button>
      <el-button
        v-else
        type="danger"
        @click="handleStop"
        class="stop-button"
      >
        <el-icon><VideoPause /></el-icon>
      </el-button>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { ChatDotRound, Setting, Loading, VideoPause, Promotion, Warning, Paperclip, Document, Close } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
const GlmIcon = 'https://www.zhipuai.cn/favicon.png'

// Props
const props = defineProps({
  modelValue: {
    type: String,
    default: ''
  },
  isStreaming: {
    type: Boolean,
    default: false
  },
  selectedModel: {
    type: String,
    default: 'glm-4-flash'
  },
  aiMode: {
    type: String,
    default: 'ask'
  },
  aiStatus: {
    type: String,
    default: 'disconnected'
  },
  currentWorkspace: {
    type: String,
    default: ''
  }
})

// Emits
const emit = defineEmits(['update:modelValue', 'send', 'stop', 'update:selectedModel', 'update:aiMode', 'attach-files'])

// 本地状态
const localInputMessage = ref(props.modelValue)
const localSelectedModel = ref(props.selectedModel)
const localAiMode = ref(props.aiMode)
const attachedFiles = ref([])

// 监听 props 变化
watch(() => props.modelValue, (val) => {
  localInputMessage.value = val
})

watch(() => props.selectedModel, (val) => {
  localSelectedModel.value = val
})

watch(() => props.aiMode, (val) => {
  localAiMode.value = val
})

// 同步 v-model
watch(localInputMessage, (val) => {
  emit('update:modelValue', val)
})

watch(localSelectedModel, (val) => {
  emit('update:selectedModel', val)
})

watch(localAiMode, (val) => {
  emit('update:aiMode', val)
})

// 发送消息
function handleSend(event) {
  // Shift+Enter 换行，不发送
  if (event.shiftKey) {
    return
  }
  
  event.preventDefault()
  handleSendClick()
}

function handleSendClick() {
  if (!localInputMessage.value.trim() || props.isStreaming) return

  emit('send', localInputMessage.value, attachedFiles.value)
  localInputMessage.value = ''
  attachedFiles.value = []
}

// 停止生成
function handleStop() {
  emit('stop')
}

// 文件引用相关
function handleAttachFile() {
  if (!props.currentWorkspace) {
    ElMessage.warning('请先选择工作区')
    return
  }
  emit('attach-files')
}

function removeFile(index) {
  attachedFiles.value.splice(index, 1)
}

// 暴露方法供父组件调用
defineExpose({
  addAttachedFile: (file) => {
    // 检查是否已经添加
    if (!attachedFiles.value.find(f => f.path === file.path)) {
      attachedFiles.value.push(file)
    }
  },
  clearAttachedFiles: () => {
    attachedFiles.value = []
  }
})
</script>

<style>
/* 下拉菜单暗色主题 - 全局样式 */
.el-select-dropdown {
  background: #1e1e1e !important;
  border: none !important;
}

.el-select-dropdown__item {
  color: #ccc !important;
  background: #1e1e1e !important;
  position: relative;
}

.el-select-dropdown__item.hover,
.el-select-dropdown__item:hover {
  background: #2d2d2d !important;
}

.el-select-dropdown__item.selected,
.el-select-dropdown__item.is-selected {
  color: #409eff !important;
  background: rgba(64, 158, 255, 0.15) !important;
  font-weight: 500;
}

.el-select-dropdown__item.selected::before,
.el-select-dropdown__item.is-selected::before {
  content: '';
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 3px;
  background: #409eff;
  border-radius: 0;
}

.el-select__popper {
  background: #1e1e1e !important;
  border: none !important;
}

.el-select__popper .el-popper__arrow::before {
  background: #1e1e1e !important;
  border-color: transparent !important;
}
</style>

<style scoped>
.input-container {
  padding: 16px;
  border-top: 1px solid #333;
  display: flex;
  flex-direction: column;
  gap: 12px;
  flex-shrink: 0;
  background: #1e1e1e;
}

.attached-files {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  padding: 8px;
  background: #2d2d2d;
  border-radius: 6px;
}

.file-tag {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px 8px;
  background: rgba(64, 158, 255, 0.15);
  border: 1px solid rgba(64, 158, 255, 0.3);
  border-radius: 4px;
  font-size: 12px;
  color: #409eff;
  cursor: default;
}

.file-tag .el-icon {
  font-size: 14px;
}

.file-name {
  max-width: 200px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.remove-icon {
  cursor: pointer;
  opacity: 0.7;
  transition: opacity 0.2s;
}

.remove-icon:hover {
  opacity: 1;
}

.streaming-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: rgba(64, 158, 255, 0.1);
  border-radius: 6px;
  font-size: 13px;
  color: #409eff;
}

.streaming-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #409eff;
  animation: pulse 1.5s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
    transform: scale(1);
  }
  50% {
    opacity: 0.5;
    transform: scale(0.8);
  }
}

.input-container .el-textarea {
  --el-input-bg-color: #2d2d2d;
  --el-input-border-color: #444;
  --el-input-text-color: #ccc;
  --el-input-focus-border-color: #888;
}

.input-container .el-textarea .el-input__wrapper {
  background-color: #2d2d2d !important;
  box-shadow: 0 0 0 1px #444 inset !important;
}

.input-container .el-textarea .el-input__wrapper:hover {
  box-shadow: 0 0 0 1px #888 inset !important;
}

.input-container .el-textarea.is-focus .el-input__wrapper {
  box-shadow: 0 0 0 1px #888 inset !important;
}

.input-container .el-textarea .el-textarea__inner {
  min-height: 72px !important;
  resize: none;
}

.input-container .el-textarea.is-disabled {
  --el-input-bg-color: #2d2d2d;
  --el-input-border-color: #333;
  --el-input-text-color: #888;
}

.input-container .el-textarea.is-disabled .el-textarea__inner {
  background-color: #2d2d2d !important;
  color: #888 !important;
}

/* 修复输入框发送后变色的样式 */
.input-container .el-textarea .el-textarea__inner {
  background-color: #2d2d2d !important;
  color: #ccc !important;
}

.input-container .el-textarea:focus-within .el-textarea__inner {
  background-color: #2d2d2d !important;
  color: #ccc !important;
}

/* 确保所有状态的 textarea 都是深色 */
.input-container .el-textarea__inner {
  background-color: #2d2d2d !important;
  color: #ccc !important;
}

.input-container .el-textarea.is-focus .el-textarea__inner {
  background-color: #2d2d2d !important;
  color: #ccc !important;
}

.input-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  min-height: 32px;
}

.select-group {
  display: flex;
  gap: 8px;
  align-items: center;
}

.attach-button {
  min-width: 32px;
  height: 32px;
  padding: 0 8px;
  background: rgba(64, 158, 255, 0.1) !important;
  border: 1px solid rgba(64, 158, 255, 0.3) !important;
}

.attach-button:hover {
  background: rgba(64, 158, 255, 0.2) !important;
  border-color: #409eff !important;
}

.attach-button .el-icon {
  font-size: 16px;
  color: #409eff;
}

.select-group .el-select {
  --el-select-input-focus-border-color: #409eff;
  --el-select-input-height: 32px;
}

.select-group .el-select .el-input__wrapper {
  height: 32px;
  line-height: 32px;
}

.model-icon {
  width: 18px;
  height: 18px;
  border-radius: 3px;
  margin-right: 4px;
}

.option-icon {
  width: 16px;
  height: 16px;
  border-radius: 2px;
  margin-right: 6px;
  vertical-align: middle;
}

/* 下拉选项中的图标和文字对齐 */
:deep(.el-select-dropdown__item) {
  display: flex;
  align-items: center;
}

:deep(.el-select-dropdown__item .el-icon) {
  margin-right: 6px;
  display: flex;
  align-items: center;
}

.input-footer .el-button {
  flex-shrink: 0;
}

.send-button {
  min-width: 32px;
  height: 28px;
  padding: 0 8px;
  background: rgba(64, 158, 255, 0.1) !important;
  border: 1px solid #409eff !important;
}

.send-button:hover {
  background: rgba(64, 158, 255, 0.2) !important;
}

.send-button.disconnected {
  background: rgba(244, 67, 54, 0.1) !important;
  border: 1px solid #f44336 !important;
}

.send-button.disconnected:hover {
  background: rgba(244, 67, 54, 0.2) !important;
}

.send-button.disconnected .el-icon {
  color: #f44336;
}

.send-button .el-icon {
  font-size: 14px;
  color: #409eff;
}

.send-icon {
  width: 20px;
  height: 20px;
}

.stop-button {
  min-width: 40px;
  height: 32px;
  padding: 0 12px;
  background: rgba(245, 108, 108, 0.1) !important;
  border: 1px solid #f56c6c !important;
}

.stop-button:hover {
  background: rgba(245, 108, 108, 0.2) !important;
}

.stop-button .el-icon {
  font-size: 16px;
  color: #f56c6c;
}
</style>
