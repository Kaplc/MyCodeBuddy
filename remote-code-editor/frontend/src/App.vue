<template>
  <div class="app-container">
    <!-- 顶部栏 -->
    <AppHeader 
      :ui-font-size="uiFontSize"
      @command="handleHeaderCommand"
    />
    
    <!-- 主内容区 -->
    <main class="app-main" ref="mainRef">
      <!-- 左侧：垂直导航栏 -->
      <aside class="vertical-nav">
        <el-tooltip :content="showFileTree ? '收起文件树' : '展开文件树'" placement="right">
          <div class="nav-item" :class="{ active: showFileTree }" @click="toggleFileTree">
            <el-icon><FolderOpened /></el-icon>
          </div>
        </el-tooltip>
        <el-tooltip :content="showSearchPanel ? '关闭搜索' : '在文件中搜索'" placement="right">
          <div class="nav-item" :class="{ active: showSearchPanel }" @click="toggleSearch">
            <el-icon><Search /></el-icon>
          </div>
        </el-tooltip>
        <el-tooltip :content="showAiPanel ? '收起AI助手' : '展开AI助手'" placement="right">
          <div class="nav-item" :class="{ active: showAiPanel }" @click="showAiPanel = !showAiPanel">
            <el-icon><ChatDotRound /></el-icon>
          </div>
        </el-tooltip>
      </aside>

      <!-- 左侧：文件树 -->
      <aside v-show="showFileTree" class="sidebar" :style="{ width: sidebarWidth + 'px' }">
        <FileTree ref="fileTreeRef" @file-select="handleFileSelect" />
      </aside>

      <!-- 拖拽条1：文件树和编辑器之间 -->
      <div
        v-show="showFileTree"
        class="resize-handle"
        @mousedown="startResize($event, 'left')"
      ></div>

      <!-- 搜索侧边栏 -->
      <aside v-show="showSearchPanel" class="search-sidebar" :style="{ width: searchSidebarWidth + 'px' }">
        <SearchPanel
          v-model="showSearchPanel"
          @select-file="handleSearchSelect"
        />
      </aside>

      <!-- 拖拽条：搜索和编辑器之间 -->
      <div
        v-show="showSearchPanel"
        class="resize-handle"
        @mousedown="startResize($event, 'search')"
      ></div>

      <!-- 中间：代码编辑器 -->
      <section class="editor-section" :style="{ flex: editorFlex }">
        <CodeEditor
          ref="codeEditorRef"
          :file="currentFile"
          :font-size="editorFontSize"
          @selection-change="handleSelectionChange"
          @cursor-change="handleCursorChange"
        />
      </section>
      
      <!-- 拖拽条2：编辑器和AI助手之间 -->
      <div
        v-show="showAiPanel"
        class="resize-handle"
        @mousedown="startResize($event, 'right')"
      ></div>

      <!-- 右侧：AI对话 -->
      <aside v-show="showAiPanel" class="ai-sidebar" :style="{ width: aiSidebarWidth + 'px' }">
        <AIChat
          ref="aiChatRef"
          :selected-code="selectedCode"
          :font-size="aiFontSize"
          :current-workspace="currentWorkspace"
          @insert-code="handleInsertCode"
        />
      </aside>
    </main>
    
    <!-- 状态栏 -->
    <StatusBar 
      :current-file="currentFile" 
      :has-unsaved-changes="hasUnsavedChanges"
      :cursor-position="cursorPosition"
      :total-lines="totalLines"
      :server-status="serverStatus"
      :server-latency="serverLatency"
      :ai-status="aiStatus"
      :ai-chat-status="aiChatStatus"
      :ai-tab-status="aiTabStatus"
      :ai-tab-enabled="aiTabEnabled"
      @test-server="handleTestServer"
      @test-ai="handleTestAi"
      @toggle-ai-tab="handleToggleAiTab"
    />

    <!-- 设置对话框 -->
    <el-dialog v-model="showSettings" title="设置" width="400px" :close-on-click-modal="false">
      <div class="settings-content">
        <div class="setting-item">
          <label>编辑器字体大小</label>
          <div class="setting-control">
            <el-slider v-model="editorFontSize" :min="10" :max="24" :step="1" show-stops />
            <span class="setting-value">{{ editorFontSize }}px</span>
          </div>
        </div>
        <div class="setting-item">
          <label>AI聊天字体大小</label>
          <div class="setting-control">
            <el-slider v-model="aiFontSize" :min="12" :max="20" :step="1" show-stops />
            <span class="setting-value">{{ aiFontSize }}px</span>
          </div>
        </div>
      </div>
      <template #footer>
        <el-button @click="resetSettings">重置</el-button>
        <el-button type="primary" @click="saveSettings">确定</el-button>
      </template>
    </el-dialog>

    <!-- 外观设置对话框 -->
    <el-dialog v-model="showAppearanceSettings" title="外观" width="400px" :close-on-click-modal="false">
      <div class="settings-content">
        <div class="setting-item">
          <label style="font-size: 15px;">整体文字大小</label>
          <div class="setting-control">
            <el-slider v-model="tempUiFontSize" :min="14" :max="24" :step="1" show-stops />
            <span class="setting-value" style="font-size: 15px;">{{ tempUiFontSize }}px</span>
          </div>
        </div>
      </div>
      <template #footer>
        <el-button @click="showAppearanceSettings = false">取消</el-button>
        <el-button type="primary" @click="applyAppearanceSettings">确定</el-button>
      </template>
    </el-dialog>

    <!-- 文本编辑器设置对话框 -->
    <el-dialog v-model="showEditorSettings" title="文本编辑器" width="400px" :close-on-click-modal="false">
      <div class="settings-content">
        <div class="setting-item">
          <label style="font-size: 15px;">字体大小</label>
          <div class="setting-control">
            <el-slider v-model="tempEditorFontSize" :min="12" :max="30" :step="1" show-stops />
            <span class="setting-value" style="font-size: 15px;">{{ tempEditorFontSize }}px</span>
          </div>
        </div>
      </div>
      <template #footer>
        <el-button @click="showEditorSettings = false">取消</el-button>
        <el-button type="primary" @click="applyEditorSettings">确定</el-button>
      </template>
    </el-dialog>

    <!-- Git对话框 -->
    <el-dialog 
      v-model="showGitDialog" 
      title="Git 版本管理" 
      width="420px" 
      :close-on-click-modal="false"
      class="git-dialog"
    >
      <GitPanel />
    </el-dialog>

  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { Search, Switch, ChatDotRound, FolderOpened } from '@element-plus/icons-vue'
import SearchPanel from './components/SearchPanel.vue'
import 'highlight.js/styles/atom-one-dark.css'
import FileTree from './components/FileTree.vue'
import CodeEditor from './components/CodeEditor.vue'
import AIChat from './components/AIChat.vue'
import GitPanel from './components/GitPanel.vue'
import AppHeader from './components/AppHeader.vue'
import StatusBar from './components/StatusBar.vue'

// 组件引用
const fileTreeRef = ref(null)
const codeEditorRef = ref(null)
const aiChatRef = ref(null)

// 状态
const currentFile = ref(null)
const selectedCode = ref('')
const hasUnsavedChanges = ref(false)
const cursorPosition = ref({ line: 1, column: 1 })
const totalLines = ref(0)
const serverStatus = ref('disconnected')
const serverLatency = ref(0)
const aiStatus = ref('disconnected')
const aiChatStatus = ref('disconnected')
const aiTabStatus = ref('disconnected')
const aiTabEnabled = ref(true)

// 当前工作区（从 FileTree 组件获取）
const currentWorkspace = computed(() => {
  return fileTreeRef.value?.currentWorkspace || ''
})

// 面板宽度控制
const mainRef = ref(null)
const sidebarWidth = ref(400)
const searchSidebarWidth = ref(400)
const aiSidebarWidth = ref(350)
const editorFlex = ref(1)

// 面板展开/折叠（从 localStorage 读取状态）
const showFileTree = ref(localStorage.getItem('showFileTree') !== 'false')
const showAiPanel = ref(true)

// 设置
const showSettings = ref(false)
const showAppearanceSettings = ref(false)
const showEditorSettings = ref(false)
const showGitDialog = ref(false)
const showSearchPanel = ref(false)
const editorFontSize = ref(14)
const aiFontSize = ref(13)
const uiFontSize = ref(14)
const tempEditorFontSize = ref(14)
const tempAiFontSize = ref(13)
const tempUiFontSize = ref(14)

// 处理顶部菜单命令
function handleHeaderCommand(command) {
  if (command === 'appearance') {
    tempUiFontSize.value = uiFontSize.value
    showAppearanceSettings.value = true
  } else if (command === 'editorSettings') {
    tempEditorFontSize.value = editorFontSize.value
    showEditorSettings.value = true
  } else if (command === 'settings') {
    showSettings.value = true
  } else if (command === 'git') {
    showGitDialog.value = true
  } else if (command === 'find') {
    // 触发编辑器查找
    codeEditorRef.value?.triggerFind()
  } else if (command === 'replace') {
    // 触发编辑器替换
    codeEditorRef.value?.triggerReplace()
  }
}

// 切换文件树（与搜索互斥）
function toggleFileTree() {
  if (showFileTree.value) {
    // 如果文件树已打开，关闭它
    showFileTree.value = false
  } else {
    // 打开文件树时，关闭搜索
    showSearchPanel.value = false
    showFileTree.value = true
  }
  // 保存状态到 localStorage
  localStorage.setItem('showFileTree', showFileTree.value)
}

// 切换搜索面板（与文件树互斥）
function toggleSearch() {
  if (showSearchPanel.value) {
    // 如果搜索已打开，关闭它，打开文件树
    showSearchPanel.value = false
    showFileTree.value = true
    localStorage.setItem('showFileTree', 'true')
  } else {
    // 打开搜索时，关闭文件树
    showFileTree.value = false
    showSearchPanel.value = true
    localStorage.setItem('showFileTree', 'false')
  }
}

// 拖拽状态
let isResizing = false
let resizeType = '' // 'left', 'right' 或 'search'
let startX = 0
let startSidebarWidth = 0
let startSearchSidebarWidth = 0
let startAiSidebarWidth = 0

// 计算属性
const editorFlexStr = computed(() => editorFlex.value.toString())

// 处理文件选择
function handleFileSelect(file) {
  if (hasUnsavedChanges.value) {
    // 提示保存
    if (!confirm('当前文件有未保存的更改，是否继续？')) {
      return
    }
  }
  currentFile.value = file
  hasUnsavedChanges.value = false
}

// 处理选择变化
function handleSelectionChange(code) {
  selectedCode.value = code
}

// 处理光标位置变化
function handleCursorChange({ line, column, lineCount }) {
  cursorPosition.value = { line, column }
  totalLines.value = lineCount
}

// 处理插入代码
function handleInsertCode(code) {
  if (codeEditorRef.value) {
    codeEditorRef.value.insertCode(code)
    ElMessage.success('代码已插入到编辑器')
  }
}

// 检查服务器连接状态
async function checkConnection() {
  try {
    const startTime = Date.now()
    const response = await fetch('/api/health')
    const endTime = Date.now()
    serverLatency.value = endTime - startTime
    if (response.ok) {
      serverStatus.value = 'connected'
    } else {
      serverStatus.value = 'disconnected'
    }
  } catch {
    serverStatus.value = 'disconnected'
    serverLatency.value = 0
  }
}

// 检查AI连接状态
async function checkAiConnection() {
  try {
    // 检查 AI Chat 状态
    const chatResponse = await fetch('/api/ai/health')
    if (chatResponse.ok) {
      aiChatStatus.value = 'connected'
    } else {
      aiChatStatus.value = 'disconnected'
    }
    
    // 检查 AI Tab 补全状态
    const tabResponse = await fetch('/api/ai/tab/health')
    if (tabResponse.ok) {
      const data = await tabResponse.json()
      aiTabStatus.value = 'connected'
      aiTabEnabled.value = data.enabled !== false
    } else {
      aiTabStatus.value = 'disconnected'
    }
    
    // 综合状态
    if (aiChatStatus.value === 'connected' || aiTabStatus.value === 'connected') {
      aiStatus.value = 'connected'
    } else {
      aiStatus.value = 'disconnected'
    }
  } catch {
    aiChatStatus.value = 'disconnected'
    aiTabStatus.value = 'disconnected'
    aiStatus.value = 'disconnected'
  }
}

// 测试服务器连接
async function handleTestServer() {
  serverStatus.value = 'connecting'
  
  try {
    const startTime = Date.now()
    const response = await fetch('/api/health')
    const endTime = Date.now()
    serverLatency.value = endTime - startTime
    
    if (response.ok) {
      serverStatus.value = 'connected'
      ElMessage.success(`服务器连接正常 (${serverLatency.value}ms)`)
    } else {
      serverStatus.value = 'disconnected'
      ElMessage.error('服务器响应异常')
    }
  } catch (error) {
    serverStatus.value = 'disconnected'
    serverLatency.value = 0
    ElMessage.error('服务器连接失败，请检查网络设置')
  }
}

// 测试AI连接
async function handleTestAi() {
  aiStatus.value = 'connecting'
  ElMessage.info('正在测试AI服务连接...')
  
  try {
    const response = await fetch('/api/ai/health')
    if (response.ok) {
      aiStatus.value = 'connected'
      ElMessage.success('AI服务连接正常')
    } else {
      aiStatus.value = 'disconnected'
      ElMessage.error('AI服务响应异常')
    }
  } catch (error) {
    aiStatus.value = 'disconnected'
    ElMessage.error('AI服务连接失败，请检查网络设置')
  }
}

// 切换 AI Tab 补全
async function handleToggleAiTab(enabled) {
  try {
    await fetch('/api/ai/tab/toggle', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ enabled })
    })
    aiTabEnabled.value = enabled
    ElMessage.success(enabled ? 'AI Tab 补全已开启' : 'AI Tab 补全已关闭')
  } catch (error) {
    ElMessage.error('切换失败')
  }
}

// 处理搜索结果选择
function handleSearchSelect({ file, line, column }) {
  currentFile.value = { path: file }
  hasUnsavedChanges.value = false
  // 延迟等待文件加载后跳转到指定行
  setTimeout(() => {
    codeEditorRef.value?.goToLine(line, column)
  }, 100)
}

// 开始调整大小
function startResize(event, type) {
  isResizing = true
  resizeType = type
  startX = event.clientX
  startSidebarWidth = sidebarWidth.value
  startSearchSidebarWidth = searchSidebarWidth.value
  startAiSidebarWidth = aiSidebarWidth.value

  document.addEventListener('mousemove', handleResize)
  document.addEventListener('mouseup', stopResize)
  document.body.style.cursor = 'col-resize'
  document.body.style.userSelect = 'none'
}

// 处理调整大小
function handleResize(event) {
  if (!isResizing) return

  const deltaX = event.clientX - startX

  if (resizeType === 'left') {
    // 调整左侧文件树宽度
    const newWidth = Math.max(400, Math.min(500, startSidebarWidth + deltaX))
    sidebarWidth.value = newWidth
  } else if (resizeType === 'search') {
    // 调整搜索侧边栏宽度
    const newWidth = Math.max(250, Math.min(500, startSearchSidebarWidth + deltaX))
    searchSidebarWidth.value = newWidth
  } else if (resizeType === 'right') {
    // 调整右侧AI助手宽度
    const newWidth = Math.max(250, Math.min(600, startAiSidebarWidth - deltaX))
    aiSidebarWidth.value = newWidth
  }
}

// 停止调整大小
function stopResize() {
  isResizing = false
  resizeType = ''
  document.removeEventListener('mousemove', handleResize)
  document.removeEventListener('mouseup', stopResize)
  document.body.style.cursor = ''
  document.body.style.userSelect = ''
}

// 保存设置
function saveSettings() {
  editorFontSize.value = tempEditorFontSize.value
  aiFontSize.value = tempAiFontSize.value
  showSettings.value = false
  // 保存到localStorage
  localStorage.setItem('editorFontSize', editorFontSize.value)
  localStorage.setItem('aiFontSize', aiFontSize.value)
}

// 重置设置
function resetSettings() {
  tempEditorFontSize.value = 14
  tempAiFontSize.value = 13
}

// 应用外观设置
function applyAppearanceSettings() {
  uiFontSize.value = tempUiFontSize.value
  showAppearanceSettings.value = false
  document.documentElement.style.fontSize = uiFontSize.value + 'px'
  localStorage.setItem('uiFontSize', uiFontSize.value)
}

// 应用编辑器设置
function applyEditorSettings() {
  editorFontSize.value = tempEditorFontSize.value
  showEditorSettings.value = false
  localStorage.setItem('editorFontSize', editorFontSize.value)
}

// 加载保存的设置
function loadSettings() {
  const savedEditorFontSize = localStorage.getItem('editorFontSize')
  const savedAiFontSize = localStorage.getItem('aiFontSize')
  const savedUiFontSize = localStorage.getItem('uiFontSize')
  if (savedEditorFontSize) {
    editorFontSize.value = parseInt(savedEditorFontSize)
    tempEditorFontSize.value = editorFontSize.value
  }
  if (savedAiFontSize) {
    aiFontSize.value = parseInt(savedAiFontSize)
    tempAiFontSize.value = aiFontSize.value
  }
  if (savedUiFontSize) {
    uiFontSize.value = parseInt(savedUiFontSize)
    tempUiFontSize.value = uiFontSize.value
    document.documentElement.style.fontSize = uiFontSize.value + 'px'
  }
}

// 定时检查连接
let connectionCheckInterval = null

onMounted(() => {
  checkConnection()
  checkAiConnection()
  connectionCheckInterval = setInterval(() => {
    checkConnection()
    checkAiConnection()
  }, 10000)
  loadSettings()
})

// 监听设置对话框打开
watch(showSettings, (val) => {
  if (val) {
    tempEditorFontSize.value = editorFontSize.value
    tempAiFontSize.value = aiFontSize.value
  }
})

onUnmounted(() => {
  if (connectionCheckInterval) {
    clearInterval(connectionCheckInterval)
  }
  // 清理可能残留的拖拽事件监听
  document.removeEventListener('mousemove', handleResize)
  document.removeEventListener('mouseup', stopResize)
})
</script>

<style>
/* 全局样式重置 */
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

html, body, #app {
  height: 100%;
  overflow: hidden;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Fira Sans', 'Droid Sans', 'Helvetica Neue', sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

/* Element Plus暗色主题覆盖 */
:root {
  --el-bg-color: #1e1e1e;
  --el-text-color-primary: #cccccc;
  --el-text-color-regular: #999999;
  --el-border-color: #333333;
  --el-fill-color-blank: #2d2d2d;
}
</style>

<style scoped>
.app-container {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: #1e1e1e;
  color: #cccccc;
}

.app-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: #323233;
  border-bottom: 1px solid #333;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.3);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.header-left .el-breadcrumb {
  font-size: 13px;
}

.header-left .el-breadcrumb__item {
  color: #57606a;
}

.header-left .el-breadcrumb__inner {
  color: #24292f !important;
}

.header-left .el-breadcrumb__separator {
  color: #d0d7de;
}

.logo-icon {
  font-size: 24px;
  color: #0969da;
}

.app-title {
  font-size: 16px;
  font-weight: 600;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.header-right .el-tag {
  display: flex;
  align-items: center;
  gap: 4px;
}

/* 垂直导航栏 */
.vertical-nav {
  width: 48px;
  background: #252526;
  border-right: 1px solid #333;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding-top: 8px;
  gap: 4px;
  flex-shrink: 0;
}

.vertical-nav .nav-item {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 6px;
  cursor: pointer;
  color: #999;
  transition: all 0.2s;
}

.vertical-nav .nav-item:hover {
  background: rgba(255, 255, 255, 0.1);
  color: #fff;
}

.vertical-nav .nav-item.active {
  background: rgba(64, 158, 255, 0.2);
  color: #409eff;
}

.vertical-nav .nav-item .el-icon {
  font-size: 18px;
}

.app-main {
  flex: 1;
  display: flex;
  overflow: hidden;
}

.sidebar {
  flex-shrink: 0;
  border-right: 1px solid #333;
  overflow: hidden;
}

.search-sidebar {
  flex-shrink: 0;
  overflow: hidden;
}

.editor-section {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  position: relative;
}

.ai-sidebar {
  flex-shrink: 0;
  overflow: hidden;
}

/* 拖拽条样式 */
.resize-handle {
  width: 4px;
  background: transparent;
  cursor: col-resize;
  transition: background 0.2s;
  flex-shrink: 0;
}

.resize-handle:hover {
  background: #409eff;
}

.resize-handle:active {
  background: #409eff;
}

/* 对话框暗色主题 */
:deep(.el-dialog) {
  background: #1e1e1e;
}

:deep(.el-dialog__header) {
  background: #1e1e1e;
  border-bottom: 1px solid #333;
}

:deep(.el-dialog__title) {
  color: #e0e0e0;
}

:deep(.el-dialog__body) {
  background: #1e1e1e;
  color: #e0e0e0;
}

:deep(.el-dialog__footer) {
  background: #1e1e1e;
  border-top: 1px solid #333;
}

/* 设置对话框样式 */
.settings-content {
  padding: 10px 0;
}

.setting-item {
  margin-bottom: 24px;
}

.setting-item label {
  display: block;
  margin-bottom: 12px;
  font-weight: 500;
  color: #e0e0e0;
  font-size: 14px;
}

.setting-value {
  color: #e0e0e0;
  font-size: 14px;
  min-width: 45px;
  text-align: right;
}

.setting-control {
  display: flex;
  align-items: center;
  gap: 16px;
}

.setting-control .el-slider {
  flex: 1;
}

.setting-value {
  min-width: 45px;
  text-align: right;
  color: #0969da;
  font-weight: 500;
}
</style>
