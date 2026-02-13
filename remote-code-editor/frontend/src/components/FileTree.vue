<template>
  <div class="file-tree">
    <!-- 拖拽垃圾桶区域 -->
    <div
      v-if="isDragging && draggedData"
      class="trash-drop-zone"
      :class="{ 'is-drag-over': isDragOver }"
      @dragover.prevent="handleDragOver"
      @dragleave="handleDragLeave"
      @drop.prevent="handleDrop"
      @touchmove.prevent="handleTouchMove"
      @touchend.prevent="handleTouchEndDrop"
    >
      <div class="trash-container">
        <el-icon class="trash-icon"><Delete /></el-icon>
        <div class="trash-info">
          <span class="trash-text">拖放到此处删除</span>
          <span class="dragging-file-name">{{ draggedData.name }}</span>
        </div>
      </div>
    </div>

    <!-- 移动端拖拽提示 -->
    <div
      v-if="isDragging && isTouchDevice()"
      class="touch-drag-hint"
    >
      <el-icon><Pointer /></el-icon>
      <span>拖动到下方垃圾桶</span>
    </div>

    <div class="file-tree-header">
      <el-dropdown 
        trigger="click" 
        @command="handleWorkspaceCommand" 
        @visible-change="handleDropdownVisibleChange"
        class="header-dropdown"
      >
        <span class="header-title" :title="currentWorkspace">
          {{ displayWorkspace }}
          <el-icon class="dropdown-icon"><ArrowDown /></el-icon>
        </span>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item 
              v-for="ws in getUniqueWorkspaces()" 
              :key="ws.path" 
              :command="{ type: 'switch', path: ws.path }"
              :class="{ 'is-active': ws.path === currentWorkspace }"
            >
              {{ getWorkspaceDisplayName(ws) }}
            </el-dropdown-item>
            <el-dropdown-item v-if="workspaceList.length === 0" disabled>
              暂无工作区
            </el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>
      <div class="file-tree-actions">
        <el-button size="small" @click="showNewWorkspaceDialog" title="新建工作区">
          <el-icon><FolderAdd /></el-icon>
        </el-button>
        <el-button size="small" @click="handleCreateFile" title="新建文件" :disabled="!currentWorkspace">
          <el-icon><Document /></el-icon>
        </el-button>
        <el-button size="small" @click="handleCreateFolder" title="新建文件夹" :disabled="!currentWorkspace">
          <el-icon><FolderAdd /></el-icon>
        </el-button>
        <el-button size="small" @click="loadTree" title="刷新" :disabled="!currentWorkspace">
          <el-icon><Refresh /></el-icon>
        </el-button>
      </div>
    </div>
    
    <!-- 空状态提示 - 未选择工作区时显示 -->
    <div v-if="!currentWorkspace" class="empty-workspace">
      <el-icon class="empty-icon"><Folder /></el-icon>
      <p class="empty-text">请先选择工作区</p>
      <el-button type="primary" size="small" @click="showNewWorkspaceDialog">
        选择工作区
      </el-button>
    </div>
    
    <!-- 工作区为空时显示 -->
    <div v-else-if="treeData.length === 0" class="empty-workspace">
      <el-icon class="empty-icon"><FolderOpened /></el-icon>
      <p class="empty-text">当前工作区为空</p>
      <div class="empty-actions">
        <el-button size="small" @click="handleCreateFile">
          <el-icon><Document /></el-icon>
          新建文件
        </el-button>
        <el-button size="small" @click="handleCreateFolder">
          <el-icon><FolderAdd /></el-icon>
          新建文件夹
        </el-button>
      </div>
    </div>
    
    <!-- 文件树 - 仅在选择工作区后显示 -->
    <el-tree
      ref="treeRef"
      :data="treeData"
      :props="treeProps"
      node-key="path"
      :highlight-current="true"
      :expand-on-click-node="false"
      :default-expand-all="false"
      @node-click="handleNodeClick"
      lazy
      :load="loadNode"
    >
      <template #default="{ node, data }">
        <div
          class="file-node"
          :class="{ 'is-dragging': isDragging && draggedData?.path === data.path }"
          draggable="true"
          @contextmenu.prevent="handleContextMenu($event, node, data)"
          @mousedown="handleMouseDown($event, node, data)"
          @mouseup="handleMouseUp"
          @mouseleave="handleMouseUp"
          @touchstart="handleTouchStart($event, node, data)"
          @touchend="handleTouchEnd"
          @dragstart="handleDragStart($event, data)"
          @dragend="handleDragEnd"
        >
          <el-icon class="file-icon" :class="{ 'is-folder': data.is_dir }">
            <Folder v-if="data.is_dir" />
            <Document v-else />
          </el-icon>
          <span class="file-name">{{ node.label }}</span>
        </div>
      </template>
    </el-tree>
    
    <!-- 右键菜单 -->
    <el-dropdown
      ref="contextMenuRef"
      trigger="contextmenu"
      :teleported="false"
      @command="handleCommand"
    >
      <span></span>
      <template #dropdown>
        <el-dropdown-menu>
          <el-dropdown-item command="rename">重命名</el-dropdown-item>
          <el-dropdown-item command="delete" divided>删除</el-dropdown-item>
        </el-dropdown-menu>
      </template>
    </el-dropdown>

    <!-- 长按菜单 -->
    <el-dropdown
      ref="longPressMenuRef"
      trigger="click"
      :teleported="false"
      v-model:visible="longPressMenuVisible"
      @command="handleLongPressCommand"
    >
      <div
        ref="longPressMenuTrigger"
        :style="{
          position: 'fixed',
          left: longPressMenuPosition.x + 'px',
          top: longPressMenuPosition.y + 'px',
          zIndex: 9999
        }"
      ></div>
      <template #dropdown>
        <el-dropdown-menu>
          <el-dropdown-item command="createFile">
            <el-icon><Document /></el-icon>
            <span style="margin-left: 8px">创建文件</span>
          </el-dropdown-item>
          <el-dropdown-item command="createFolder">
            <el-icon><FolderAdd /></el-icon>
            <span style="margin-left: 8px">创建文件夹</span>
          </el-dropdown-item>
          <el-dropdown-item command="rename" divided>
            <el-icon><Edit /></el-icon>
            <span style="margin-left: 8px">重命名</span>
          </el-dropdown-item>
          <el-dropdown-item command="delete">
            <el-icon><Delete /></el-icon>
            <span style="margin-left: 8px">删除</span>
          </el-dropdown-item>
        </el-dropdown-menu>
      </template>
    </el-dropdown>
    
    <!-- 新建对话框 -->
    <el-dialog v-model="createDialogVisible" :title="createDialogTitle" width="400px">
      <el-input v-model="newItemName" placeholder="请输入名称" @keyup.enter="confirmCreate" />
      <template #footer>
        <el-button @click="createDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="confirmCreate">确定</el-button>
      </template>
    </el-dialog>
    
    <!-- 工作区选择对话框 -->
    <el-dialog
      v-model="workspaceDialogVisible"
      title="创建新工作区"
      width="400px"
      :close-on-click-modal="false"
    >
      <div class="workspace-dialog">
        <div class="current-path">
          <el-input
            v-model="workspaceName"
            placeholder="请输入工作区名称（例如：我的项目）"
            clearable
          >
            <template #prepend>工作区名称</template>
          </el-input>
        </div>
      </div>

      <template #footer>
        <el-button @click="workspaceDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="confirmWorkspace" :disabled="!workspaceName">
          创建工作区
        </el-button>
      </template>
    </el-dialog>
    
    <!-- 重命名对话框 -->
    <el-dialog v-model="renameDialogVisible" title="重命名" width="400px">
      <el-input v-model="renameValue" placeholder="请输入新名称" @keyup.enter="confirmRename" />
      <template #footer>
        <el-button @click="renameDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="confirmRename">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Document, Folder, FolderAdd, Refresh, FolderOpened, ArrowUp, ArrowRight, ArrowDown, Edit, Delete, Pointer } from '@element-plus/icons-vue'
import axios from 'axios'
import { API_CONFIG } from '../config/api.js'

// 定义事件
const emit = defineEmits(['file-select'])

// 树引用
const treeRef = ref(null)
const contextMenuRef = ref(null)
const longPressMenuRef = ref(null)
const longPressMenuTrigger = ref(null)

// 长按相关
const longPressMenuVisible = ref(false)
const longPressMenuPosition = ref({ x: 0, y: 0 })
const longPressTimer = ref(null)
const longPressNode = ref(null)
const longPressData = ref(null)
const LONG_PRESS_DURATION = 600 // 长按持续时间（毫秒）

// 拖拽删除相关
const isDragging = ref(false)
const isDragOver = ref(false)
const draggedData = ref(null)
const dragStartPosition = ref({ x: 0, y: 0 })

// 树数据
const treeData = ref([])
const treeProps = {
  label: 'name',
  children: 'children',
  isLeaf: (data) => !data.is_dir
}

// 当前右键选中的节点
const currentNode = ref(null)
const currentData = ref(null)

// 当前左键选中的节点
const selectedNode = ref(null)
const selectedData = ref(null)

// 新建对话框
const createDialogVisible = ref(false)
const createDialogTitle = ref('')
const createIsDir = ref(false)
const newItemName = ref('')
const createParentPath = ref('')

// 重命名对话框
const renameDialogVisible = ref(false)
const renameValue = ref('')

// 工作区选择对话框
const workspaceDialogVisible = ref(false)
const workspaceName = ref('')

// 当前工作区路径
const currentWorkspace = ref('')
const displayWorkspace = ref('请选择工作区')

// 工作区列表
const workspaceList = ref([])

// 加载目录树
async function loadTree() {
  if (!currentWorkspace.value) {
    treeData.value = []
    return
  }
  
  try {
    const response = await axios.get('/api/files/tree/', { params: { path: '' } })
    // 空数组也是有效的工作区，正常显示即可
    treeData.value = Array.isArray(response.data) ? response.data : []
  } catch (error) {
    ElMessage.error('加载文件树失败: ' + (error.response?.data?.detail || error.message))
  }
}

// 懒加载子节点
async function loadNode(node, resolve) {
  // 检查工作区是否设置
  if (!currentWorkspace.value) {
    resolve([])
    return
  }
  
  if (node.level === 0) {
    const response = await axios.get('/api/files/tree/', { params: { path: '' } })
    resolve(response.data)
    return
  }

  const path = node.data.path
  try {
    const response = await axios.get('/api/files/tree/', { params: { path } })
    resolve(response.data)
  } catch (error) {
    resolve([])
  }
}

// 处理节点点击
function handleNodeClick(data, node) {
  // 更新选中节点
  selectedNode.value = node
  selectedData.value = data

  if (data.is_dir) {
    // 点击文件夹时切换展开/折叠状态
    if (!node.loaded && !node.loading) {
      // 如果节点未加载，先加载子节点再展开
      node.loadData(() => {
        node.expanded = true
      })
    } else {
      node.expanded = !node.expanded
    }
  } else {
    // 点击文件时发送文件选择事件
    emit('file-select', data)
  }
}

// 处理右键菜单
function handleContextMenu(event, node, data) {
  currentNode.value = node
  currentData.value = data
  // 简化右键菜单，直接使用原生的contextmenu事件
}

// 处理命令
async function handleCommand(command) {
  if (!currentData.value) return

  if (command === 'rename') {
    renameValue.value = currentData.value.name
    renameDialogVisible.value = true
  } else if (command === 'delete') {
    try {
      await ElMessageBox.confirm(
        `确定要删除 "${currentData.value.name}" 吗？`,
        '删除确认',
        { type: 'warning' }
      )
      await deleteItem(currentData.value.path)
    } catch {
      // 用户取消
    }
  }
}

// 处理长按菜单命令
async function handleLongPressCommand(command) {
  if (!longPressData.value) return

  const data = longPressData.value

  if (command === 'createFile') {
    createDialogTitle.value = '新建文件'
    createIsDir.value = false
    if (data.is_dir) {
      createParentPath.value = data.path
    } else {
      const pathParts = data.path.replace(/\\/g, '/').split('/')
      pathParts.pop()
      createParentPath.value = pathParts.join('/')
    }
    newItemName.value = ''
    createDialogVisible.value = true
  } else if (command === 'createFolder') {
    createDialogTitle.value = '新建文件夹'
    createIsDir.value = true
    if (data.is_dir) {
      createParentPath.value = data.path
    } else {
      const pathParts = data.path.replace(/\\/g, '/').split('/')
      pathParts.pop()
      createParentPath.value = pathParts.join('/')
    }
    newItemName.value = ''
    createDialogVisible.value = true
  } else if (command === 'rename') {
    currentNode.value = longPressNode.value
    currentData.value = longPressData.value
    renameValue.value = longPressData.value.name
    renameDialogVisible.value = true
  } else if (command === 'delete') {
    currentNode.value = longPressNode.value
    currentData.value = longPressData.value
    try {
      await ElMessageBox.confirm(
        `确定要删除 "${longPressData.value.name}" 吗？`,
        '删除确认',
        { type: 'warning' }
      )
      await deleteItem(longPressData.value.path)
    } catch {
      // 用户取消
    }
  }

  longPressMenuVisible.value = false
}

// 处理工作区下拉菜单命令
async function handleWorkspaceCommand(command) {
  if (typeof command === 'object' && command.type === 'switch') {
    await switchWorkspace(command.path)
  }
}

// 切换工作区
async function switchWorkspace(path) {
  try {
    const response = await axios.post('/api/workspace/set/', { path })
    currentWorkspace.value = response.data.workspace
    updateDisplayWorkspace()
    ElMessage.success('工作区切换成功')

    // 切换后立即重新加载工作区列表，确保去重
    await loadWorkspaceList()
    updateDisplayWorkspace() // 更新显示名称（考虑重复）
    loadTree()
  } catch (error) {
    ElMessage.error('切换工作区失败: ' + (error.response?.data?.error || error.message))
  }
}

// 加载工作区列表
async function loadWorkspaceList() {
  try {
    const response = await axios.get('/api/workspace/list/')
    workspaceList.value = response.data.workspaces || []
  } catch (error) {
    console.error('获取工作区列表失败:', error)
  }
}

// 前端去重：确保显示的工作区列表没有重复
function getUniqueWorkspaces() {
  const seen = new Set()
  return workspaceList.value.filter(ws => {
    const normalizedPath = ws.path.replace(/\\/g, '/')
    if (seen.has(normalizedPath)) {
      return false
    }
    seen.add(normalizedPath)
    return true
  })
}

// 获取工作区显示名称（处理重复名称）
function getWorkspaceDisplayName(workspace) {
  const nameCounts = {}
  workspaceList.value.forEach(ws => {
    nameCounts[ws.name] = (nameCounts[ws.name] || 0) + 1
  })

  // 如果名称重复，添加路径后缀
  if (nameCounts[workspace.name] > 1) {
    const pathParts = workspace.path.replace(/\\/g, '/').split('/')
    return `${workspace.name} (${pathParts[pathParts.length - 1] || workspace.name})`
  }

  return workspace.name
}

// 获取当前工作区的显示名称
function updateDisplayWorkspace() {
  if (!currentWorkspace.value) {
    displayWorkspace.value = '请选择工作区'
    return
  }

  const currentWorkspaceObj = workspaceList.value.find(ws => ws.path === currentWorkspace.value)
  if (currentWorkspaceObj) {
    displayWorkspace.value = getWorkspaceDisplayName(currentWorkspaceObj)
  } else {
    // 如果工作区列表中找不到，使用路径最后一部分
    const pathParts = currentWorkspace.value.replace(/\\/g, '/').split('/')
    displayWorkspace.value = pathParts[pathParts.length - 1] || currentWorkspace.value
  }
}

// 下拉菜单显示/隐藏时
async function handleDropdownVisibleChange(visible) {
  if (visible) {
    // 打开时重新加载工作区列表，确保只显示服务器上存在的工作区
    await loadWorkspaceList()
  }
}

// 显示新建工作区对话框
function showNewWorkspaceDialog() {
  workspaceDialogVisible.value = true
  workspaceName.value = ''
}

// 新建文件
function handleCreateFile() {
  createDialogTitle.value = '新建文件'
  createIsDir.value = false
  // 如果选中了节点，根据节点类型设置父路径
  if (selectedData.value) {
    if (selectedData.value.is_dir) {
      // 选中文件夹，在该文件夹下创建
      createParentPath.value = selectedData.value.path
    } else {
      // 选中文件，在文件所在文件夹下创建
      const pathParts = selectedData.value.path.replace(/\\/g, '/').split('/')
      pathParts.pop() // 移除文件名
      createParentPath.value = pathParts.join('/')
    }
  } else {
    // 没有选中节点，在根目录创建
    createParentPath.value = ''
  }
  newItemName.value = ''
  createDialogVisible.value = true
}

// 新建文件夹
function handleCreateFolder() {
  createDialogTitle.value = '新建文件夹'
  createIsDir.value = true
  // 如果选中了节点，根据节点类型设置父路径
  if (selectedData.value) {
    if (selectedData.value.is_dir) {
      // 选中文件夹，在该文件夹下创建
      createParentPath.value = selectedData.value.path
    } else {
      // 选中文件，在文件所在文件夹下创建
      const pathParts = selectedData.value.path.replace(/\\/g, '/').split('/')
      pathParts.pop() // 移除文件名
      createParentPath.value = pathParts.join('/')
    }
  } else {
    // 没有选中节点，在根目录创建
    createParentPath.value = ''
  }
  newItemName.value = ''
  createDialogVisible.value = true
}

// 确认创建
async function confirmCreate() {
  if (!newItemName.value.trim()) {
    ElMessage.warning('名称不能为空')
    return
  }
  
  try {
    const path = createParentPath.value 
      ? `${createParentPath.value}/${newItemName.value}`
      : newItemName.value
    
    await axios.post('/api/files/create/', {
      path: path,
      is_dir: createIsDir.value
    })
    
    createDialogVisible.value = false
    ElMessage.success(createIsDir.value ? '文件夹创建成功' : '文件创建成功')
    loadTree()
  } catch (error) {
    ElMessage.error('创建失败: ' + (error.response?.data?.detail || error.message))
  }
}

// 确认重命名
async function confirmRename() {
  if (!renameValue.value.trim()) {
    ElMessage.warning('名称不能为空')
    return
  }
  
  try {
    await axios.post('/api/files/rename/', {
      old_path: currentData.value.path,
      new_name: renameValue.value
    })
    
    renameDialogVisible.value = false
    ElMessage.success('重命名成功')
    loadTree()
  } catch (error) {
    ElMessage.error('重命名失败: ' + (error.response?.data?.detail || error.message))
  }
}

// 删除项目
async function deleteItem(path) {
  try {
    await axios.post('/api/files/delete/', { path })
    ElMessage.success('删除成功')
    loadTree()
  } catch (error) {
    ElMessage.error('删除失败: ' + (error.response?.data?.detail || error.message))
  }
}

// 检测是否为触摸设备
function isTouchDevice() {
  return 'ontouchstart' in window || navigator.maxTouchPoints > 0
}

// 长按检测 - 鼠标事件
function handleMouseDown(event, node, data) {
  // 只有左键才触发长按
  if (event.button !== 0) return

  // 清除之前的定时器
  if (longPressTimer.value) {
    clearTimeout(longPressTimer.value)
  }

  // 启动长按定时器
  longPressTimer.value = setTimeout(() => {
    // 长按触发
    longPressNode.value = node
    longPressData.value = data

    // 对于文件，进入拖拽模式
    if (!data.is_dir) {
      isDragging.value = true
      draggedData.value = data
      // 显示提示而不是菜单
      ElMessage.info('拖动到垃圾桶删除，或点击右上角菜单')
    } else {
      // 文件夹显示菜单
      showLongPressMenu(event)
    }
  }, LONG_PRESS_DURATION)
}

function handleMouseUp() {
  // 清除长按定时器
  if (longPressTimer.value) {
    clearTimeout(longPressTimer.value)
    longPressTimer.value = null
  }
}

// 长按检测 - 触摸事件
function handleTouchStart(event, node, data) {
  // 清除之前的定时器
  if (longPressTimer.value) {
    clearTimeout(longPressTimer.value)
  }

  // 启动长按定时器
  longPressTimer.value = setTimeout(() => {
    // 长按触发
    longPressNode.value = node
    longPressData.value = data

    // 使用第一个触摸点的位置
    const touch = event.touches[0]

    // 对于文件，进入拖拽模式
    if (!data.is_dir) {
      isDragging.value = true
      draggedData.value = data
      ElMessage.info('拖动到垃圾桶删除')
    } else {
      // 文件夹显示菜单
      showLongPressMenu({ clientX: touch.clientX, clientY: touch.clientY })
    }
  }, LONG_PRESS_DURATION)
}

function handleTouchEnd() {
  // 清除长按定时器
  if (longPressTimer.value) {
    clearTimeout(longPressTimer.value)
    longPressTimer.value = null
  }
}

// 显示长按菜单
function showLongPressMenu(event) {
  // 计算菜单位置
  longPressMenuPosition.value = {
    x: event.clientX,
    y: event.clientY
  }

  // 只对文件夹显示完整菜单，对文件只显示创建选项
  const data = longPressData.value
  if (!data.is_dir) {
    // 如果是文件，在父文件夹显示菜单
    const pathParts = data.path.replace(/\\/g, '/').split('/')
    pathParts.pop() // 移除文件名
    const parentPath = pathParts.join('/')

    // 查找父文件夹节点
    const parentNodes = treeRef.value?.store.nodesMap
    let parentNode = null
    if (parentNodes) {
      for (const key in parentNodes) {
        const node = parentNodes[key]
        if (node.data.path === parentPath && node.data.is_dir) {
          parentNode = node
          break
        }
      }
    }

    if (parentNode) {
      longPressNode.value = parentNode
      longPressData.value = parentNode.data
    }
  }

  longPressMenuVisible.value = true
}

// ========== 拖拽删除功能 ==========

// 拖拽开始
function handleDragStart(event, data) {
  isDragging.value = true
  draggedData.value = data
  dragStartPosition.value = { x: event.clientX, y: event.clientY }

  // 设置拖拽数据（兼容移动端）
  if (event.dataTransfer) {
    event.dataTransfer.effectAllowed = 'move'
    event.dataTransfer.setData('text/plain', data.path)
  }

  // 添加拖拽样式
  event.target.classList.add('is-dragging-source')
}

// 拖拽结束
function handleDragEnd(event) {
  isDragging.value = false
  isDragOver.value = false
  draggedData.value = null

  // 移除拖拽样式
  event.target.classList.remove('is-dragging-source')
}

// 拖拽进入垃圾桶区域
function handleDragOver(event) {
  isDragOver.value = true
}

// 拖拽离开垃圾桶区域
function handleDragLeave(event) {
  // 稍微延迟，避免在元素边缘快速切换
  setTimeout(() => {
    isDragOver.value = false
  }, 50)
}

// 放置到垃圾桶
async function handleDrop(event) {
  isDragOver.value = false

  if (!draggedData.value) {
    return
  }

  try {
    await ElMessageBox.confirm(
      `确定要删除 "${draggedData.value.name}" 吗？`,
      '删除确认',
      { type: 'warning' }
    )

    await deleteItem(draggedData.value.path)
    isDragging.value = false
    draggedData.value = null
  } catch {
    // 用户取消
    isDragging.value = false
    draggedData.value = null
  }
}

// 触摸移动（模拟拖拽）
function handleTouchMove(event) {
  if (!isDragging.value || !draggedData.value) {
    return
  }

  event.preventDefault()
  isDragOver.value = true
}

// 触摸结束（模拟放置）
async function handleTouchEndDrop(event) {
  if (!isDragging.value || !draggedData.value) {
    return
  }

  // 只有在垃圾桶区域才触发删除
  if (isDragOver.value) {
    try {
      await ElMessageBox.confirm(
        `确定要删除 "${draggedData.value.name}" 吗？`,
        '删除确认',
        { type: 'warning' }
      )

      await deleteItem(draggedData.value.path)
    } catch {
      // 用户取消
    }
  }

  // 重置状态
  isDragging.value = false
  isDragOver.value = false
  draggedData.value = null
}



// 加载当前工作区
async function loadCurrentWorkspace() {
  try {
    const response = await axios.get('/api/workspace/get/')
    const workspace = response.data.workspace

    // 检查工作区是否有效（非空且不是默认路径）
    if (workspace && workspace.trim() !== '') {
      currentWorkspace.value = workspace
    } else {
      currentWorkspace.value = ''
      displayWorkspace.value = '请选择工作区'
    }
  } catch (error) {
    console.error('获取工作区失败:', error)
    currentWorkspace.value = ''
    displayWorkspace.value = '请选择工作区'
  }
}

// 暴露方法和状态
defineExpose({
  loadTree,
  currentWorkspace  // 暴露当前工作区路径给父组件
})

onMounted(async () => {
  await loadCurrentWorkspace()
  await loadWorkspaceList()
  updateDisplayWorkspace() // 更新显示名称（考虑重复）
  if (currentWorkspace.value) {
    loadTree()
  }
})

onUnmounted(() => {
  // 清理长按定时器
  if (longPressTimer.value) {
    clearTimeout(longPressTimer.value)
  }
})
async function confirmWorkspace() {
  if (!workspaceName.value || !workspaceName.value.trim()) {
    ElMessage.warning('请输入工作区名称')
    return
  }

  try {
    const response = await axios.post(API_CONFIG.API_PATHS.SET_WORKSPACE, { name: workspaceName.value.trim() })
    currentWorkspace.value = response.data.workspace
    updateDisplayWorkspace()
    ElMessage.success('工作区创建成功')
    workspaceDialogVisible.value = false
    workspaceName.value = ''
    await loadWorkspaceList()
    updateDisplayWorkspace() // 更新显示名称（考虑重复）
    loadTree()
  } catch (error) {
    ElMessage.error('创建工作区失败: ' + (error.response?.data?.error || error.message))
  }
}
</script>

<style scoped>
.file-tree {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: #1e1e1e;
  color: #cccccc;
  position: relative;
}

/* 拖拽垃圾桶区域 */
.trash-drop-zone {
  position: absolute;
  bottom: 20px;
  left: 50%;
  transform: translateX(-50%);
  width: 280px;
  min-height: 80px;
  padding: 20px;
  z-index: 9999;
  transition: all 0.3s ease;
  animation: slideUp 0.3s ease-out;
  pointer-events: auto;
}

.trash-container {
  display: flex;
  align-items: center;
  gap: 16px;
  background: rgba(255, 82, 82, 0.95);
  border: 3px dashed #ff5252;
  border-radius: 16px;
  padding: 20px;
  backdrop-filter: blur(10px);
  box-shadow: 0 4px 20px rgba(255, 82, 82, 0.3);
  transition: all 0.3s ease;
}

@keyframes slideUp {
  from {
    opacity: 0;
    transform: translate(-50%, 30px);
  }
  to {
    opacity: 1;
    transform: translate(-50%, 0);
  }
}

.trash-drop-zone.is-drag-over .trash-container {
  background: rgba(255, 23, 68, 0.98);
  border-color: #ff1744;
  box-shadow: 0 0 30px rgba(255, 23, 68, 0.6);
  transform: scale(1.05);
}

.trash-drop-zone.is-drag-over .trash-icon {
  color: #ff1744;
  transform: scale(1.3) rotate(-10deg);
  animation: shake 0.5s ease-in-out infinite;
}

@keyframes shake {
  0%, 100% { transform: scale(1.3) rotate(-10deg); }
  50% { transform: scale(1.3) rotate(10deg); }
}

.trash-icon {
  font-size: 56px;
  color: #ff5252;
  flex-shrink: 0;
  transition: all 0.3s ease;
}

.trash-info {
  display: flex;
  flex-direction: column;
  gap: 6px;
  flex: 1;
}

.trash-text {
  font-size: 15px;
  color: #fff;
  font-weight: 600;
  line-height: 1.3;
}

.dragging-file-name {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.8);
  max-width: 200px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  word-break: break-all;
}

/* 文件节点拖拽样式 */
.file-node.is-dragging {
  opacity: 0.5;
  transform: scale(0.95);
}

.file-node.is-dragging-source {
  cursor: grabbing;
  background: rgba(64, 158, 255, 0.1);
  border-radius: 4px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
}

/* 移动端拖拽提示 */
.touch-drag-hint {
  position: fixed;
  top: 60px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 20px;
  background: rgba(64, 158, 255, 0.9);
  border-radius: 8px;
  font-size: 14px;
  color: #fff;
  z-index: 1001;
  animation: slideDown 0.3s ease-out;
  backdrop-filter: blur(10px);
}

@keyframes slideDown {
  from {
    opacity: 0;
    transform: translate(-50%, -20px);
  }
  to {
    opacity: 1;
    transform: translate(-50%, 0);
  }
}

/* 拖拽中的文件名 */
.dragging-file-name {
  font-size: 13px;
  color: #ff5252;
  margin-top: 4px;
  max-width: 180px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.file-tree-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 12px;
  border-bottom: 1px solid #333;
  font-weight: 500;
}

.header-dropdown {
  cursor: pointer;
}

.header-title {
  display: flex;
  align-items: center;
  gap: 4px;
}

.header-title:hover {
  color: #409eff;
}

.dropdown-icon {
  font-size: 12px;
}

:deep(.el-dropdown-menu__item.is-active) {
  color: #409eff;
  background-color: rgba(64, 158, 255, 0.1);
}

.file-tree-actions {
  display: flex;
  gap: 4px;
}

.file-tree-actions .el-button {
  padding: 4px 8px;
  background: transparent;
  border: none;
  color: #cccccc;
}

.file-tree-actions .el-button:hover {
  color: #409eff;
  background: rgba(64, 158, 255, 0.1);
}

.file-tree-actions .el-icon {
  font-size: 18px;
}

.file-node {
  display: flex;
  align-items: center;
  flex: 1;
  padding-right: 8px;
  cursor: pointer;
  user-select: none;
  -webkit-user-select: none;
  -webkit-touch-callout: none;
}

.file-icon {
  margin-right: 6px;
  font-size: 16px;
}

.file-icon.is-folder {
  color: #dcb67a;
}

.file-name {
  font-size: 13px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 200px;
}

:deep(.el-tree) {
  background: transparent;
  color: #cccccc;
}

:deep(.el-tree-node__content) {
  height: 28px;
}

:deep(.el-tree-node__content:hover) {
  background-color: rgba(255, 255, 255, 0.1);
}

:deep(.el-tree-node.is-current > .el-tree-node__content) {
  background-color: rgba(64, 158, 255, 0.3);
}

.workspace-path {
  display: flex;
  align-items: center;
  padding: 10px 12px;
  border-bottom: 1px solid #333;
  cursor: pointer;
}

.workspace-path:hover {
  background: rgba(255, 255, 255, 0.1);
}

.path-text {
  font-size: 13px;
  margin-left: 6px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 200px;
}

.workspace-dialog {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.current-path {
  width: 100%;
}

.directory-browser {
  display: flex;
  flex-direction: column;
  gap: 10px;
  height: 300px;
  overflow: hidden;
}

.browser-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: 500;
}

.current-location {
  font-size: 13px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 400px;
}

.browser-content {
  display: flex;
  flex-direction: column;
  gap: 4px;
  height: 100%;
  overflow-y: auto;
}

.browser-item {
  display: flex;
  align-items: center;
  padding: 6px 12px;
  cursor: pointer;
  border-radius: 4px;
}

.browser-item:hover {
  background: rgba(255, 255, 255, 0.1);
}

.browser-item.selected {
  background: rgba(64, 158, 255, 0.3);
}

.item-icon {
  margin-right: 6px;
  font-size: 16px;
}

.item-name {
  font-size: 13px;
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.enter-icon {
  font-size: 16px;
}

.empty-tip {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100%;
  font-size: 13px;
  color: #999;
}

.quick-paths {
  display: flex;
  gap: 4px;
  font-size: 13px;
}

.quick-label {
  font-weight: 500;
}

.empty-workspace {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  gap: 16px;
  padding: 40px 20px;
  text-align: center;
}

.empty-icon {
  font-size: 64px;
  color: #666;
  opacity: 0.5;
}

.empty-text {
  font-size: 14px;
  color: #999;
  margin: 0;
}

.empty-actions {
  display: flex;
  gap: 8px;
  margin-top: 8px;
}

.empty-actions .el-button {
  display: flex;
  align-items: center;
  gap: 4px;
}
</style>

<!-- 工作区下拉菜单暗色主题 - 全局样式 -->
<style>
.el-dropdown-menu {
  background: #1e1e1e !important;
  border: none !important;
}

.el-dropdown-menu__item {
  color: #ccc !important;
  background: #1e1e1e !important;
}

.el-dropdown-menu__item:hover {
  background: #2d2d2d !important;
}

.el-dropdown-menu__item .el-icon {
  margin-right: 4px;
}

.el-dropdown-menu__item span {
  flex: 1;
}

.el-dropdown-menu__item.is-active {
  color: #409eff !important;
  background: rgba(64, 158, 255, 0.15) !important;
  font-weight: 500;
}

.el-dropdown__popper {
  background: #1e1e1e !important;
  border: none !important;
}

.el-dropdown__popper .el-popper__arrow::before {
  background: #1e1e1e !important;
  border-color: transparent !important;
}
</style>
