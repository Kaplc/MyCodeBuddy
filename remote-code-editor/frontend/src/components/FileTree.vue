<template>
  <div class="file-tree">
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
          draggable="true"
          @dragstart="handleDragStart($event, data)"
          @contextmenu.prevent="handleContextMenu($event, node, data)"
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
    <div
      v-show="contextMenuVisible"
      class="context-menu"
      :style="{ left: contextMenuPos.x === 0 ? '0px' : contextMenuPos.x + 'px', top: contextMenuPos.y === 0 ? '0px' : contextMenuPos.y + 'px' }"
      @click.stop
    >
      <div class="context-menu-item" @click="handleCommand('newFile')">
        新建文件
      </div>
      <div class="context-menu-item" @click="handleCommand('newFolder')">
        新建文件夹
      </div>
      <div class="context-menu-divider"></div>
      <div v-if="currentData && !currentData.is_dir" class="context-menu-item" @click="handleCommand('edit')">
        编辑
      </div>
      <div class="context-menu-item" @click="handleCommand('copy')">
        复制
      </div>
      <div class="context-menu-item" @click="handleCommand('paste')">
        粘贴
      </div>
      <div class="context-menu-item" @click="handleCommand('rename')">
        重命名
      </div>
      <div class="context-menu-divider"></div>
      <div class="context-menu-item context-menu-item-danger" @click="handleCommand('delete')">
        删除
      </div>
    </div>
    <!-- 点击其他区域关闭菜单 -->
    <div
      v-if="contextMenuVisible"
      class="context-menu-overlay"
      @click="contextMenuVisible = false"
    ></div>

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
import { ref, onMounted, watch, nextTick } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Document, Folder, FolderAdd, Refresh, FolderOpened, ArrowUp, ArrowRight, ArrowDown, Edit, Delete } from '@element-plus/icons-vue'
import axios from 'axios'
import { API_CONFIG } from '../config/api.js'

// 定义事件
const emit = defineEmits(['file-select'])

// 树引用
const treeRef = ref(null)

// 展开状态缓存 - 存储展开的文件夹路径
const expandedPaths = ref(new Set())

// 树数据
const treeData = ref([])
const treeProps = {
  label: 'name',
  children: 'children',
  isLeaf: (data) => !data.is_dir || data.is_empty === true
}

// 当前右键选中的节点
const currentNode = ref(null)
const currentData = ref(null)

// 右键菜单控制
const contextMenuVisible = ref(false)
const contextMenuPos = ref({ x: 0, y: 0 })

// 复制粘贴
const clipboardData = ref(null) // 存储被复制的文件/文件夹路径

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

    // 恢复展开状态
    await nextTick()
    restoreExpandedState()
  } catch (error) {
    ElMessage.error('加载文件树失败: ' + (error.response?.data?.detail || error.message))
  }
}

// 恢复展开状态
async function restoreExpandedState() {
  if (!treeRef.value) return

  // 遍历所有缓存的展开路径，逐个展开
  for (const path of expandedPaths.value) {
    const node = treeRef.value.getNode(path)
    if (node && !node.expanded) {
      // 如果节点未加载，先加载再展开
      if (!node.loaded && !node.loading) {
        await new Promise(resolve => {
          node.loadData(() => {
            node.expanded = true
            resolve()
          })
        })
      } else {
        node.expanded = true
      }
    }
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
        // 缓存展开状态
        expandedPaths.value.add(data.path)
      })
    } else {
      node.expanded = !node.expanded
      // 更新展开状态缓存
      if (node.expanded) {
        expandedPaths.value.add(data.path)
      } else {
        expandedPaths.value.delete(data.path)
      }
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
  contextMenuPos.value = { x: event.clientX, y: event.clientY }
  contextMenuVisible.value = true
}

// 处理右键菜单显示/隐藏
function handleContextMenuVisible(visible) {
  if (!visible) {
    // 菜单关闭时清除选中状态
    contextMenuVisible.value = false
  }
}

// 处理拖拽开始
function handleDragStart(event, data) {
  // 设置拖拽数据
  event.dataTransfer.setData('text/plain', JSON.stringify({
    name: data.name,
    path: data.path,
    is_dir: data.is_dir
  }))
  event.dataTransfer.effectAllowed = 'copy'
}

// 处理命令
async function handleCommand(command) {
  // 关闭菜单
  contextMenuVisible.value = false

  // 新建文件/文件夹不需要选中节点
  if (command === 'newFile') {
    handleCreateFile()
    return
  } else if (command === 'newFolder') {
    handleCreateFolder()
    return
  }

  // 其他命令需要选中节点
  if (!currentData.value) return

  if (command === 'edit') {
    // 编辑文件：触发文件选择事件
    emit('file-select', currentData.value)
  } else if (command === 'copy') {
    // 复制
    clipboardData.value = {
      path: currentData.value.path,
      name: currentData.value.name,
      is_dir: currentData.value.is_dir
    }
    ElMessage.success('已复制')
  } else if (command === 'paste') {
    // 粘贴
    if (!clipboardData.value) {
      ElMessage.warning('没有可粘贴的内容')
      return
    }
    await handlePaste()
  } else if (command === 'rename') {
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

// 处理粘贴
async function handlePaste() {
  if (!clipboardData.value || !currentData.value) return

  // 只能粘贴到文件夹
  if (!currentData.value.is_dir) {
    ElMessage.warning('只能在文件夹中粘贴')
    return
  }

  const sourcePath = clipboardData.value.path
  const sourceName = clipboardData.value.name
  const targetDir = currentData.value.path
  const targetPath = `${targetDir}/${sourceName}`

  try {
    // 调用复制API
    await axios.post('/api/files/copy/', {
      source_path: sourcePath,
      target_path: targetPath,
      is_dir: clipboardData.value.is_dir
    })
    ElMessage.success('复制成功')
    loadTree()
  } catch (error) {
    ElMessage.error('复制失败: ' + (error.response?.data?.detail || error.message))
  }
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
    const normalizedPath = ws.path.replace(/\\/g, '/').toLowerCase()
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

    // 如果创建的是文件夹，缓存父路径的展开状态
    if (createIsDir.value && createParentPath.value) {
      expandedPaths.value.add(createParentPath.value)
    }

    await loadTree()

    // 如果创建的是文件，自动打开
    if (!createIsDir.value) {
      await nextTick()
      emit('file-select', {
        name: newItemName.value,
        path: path,
        is_dir: false
      })
    }
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
  refreshFiles: loadTree,  // 别名，兼容性
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
  flex: 1;
}

/* .delete-icon {
  margin-left: auto;
  font-size: 14px;
  color: #ff5252;
  opacity: 0.7;
  cursor: pointer;
  transition: all 0.2s ease;
}

.delete-icon:hover {
  opacity: 1;
  color: #ff1744;
  transform: scale(1.2);
} */

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

.context-menu-trigger {
  width: 1px;
  height: 1px;
  opacity: 0;
  position: fixed;
}

/* 自定义右键菜单 */
.context-menu {
  position: fixed;
  background: #1e1e1e;
  border: 1px solid #333;
  border-radius: 6px;
  padding: 4px 0;
  min-width: 120px;
  z-index: 9999;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.4);
}

.context-menu-item {
  padding: 8px 16px;
  cursor: pointer;
  color: #ccc;
  font-size: 13px;
}

.context-menu-item:hover {
  background: rgba(64, 158, 255, 0.2);
  color: #409eff;
}

.context-menu-item-danger:hover {
  background: rgba(255, 82, 82, 0.2);
  color: #ff5252;
}

.context-menu-divider {
  height: 1px;
  background: #333;
  margin: 4px 0;
}

.context-menu-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 9998;
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
