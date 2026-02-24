<template>
  <div class="git-panel">
    <!-- 未初始化Git仓库时显示GitHub仓库列表 -->
    <div v-if="!isGitRepo" class="repo-list-container">
      <!-- 标题和操作 -->
      <div class="repo-header">
        <h3>
          <el-icon><Platform /></el-icon>
          我的GitHub仓库
        </h3>
        <el-button type="primary" size="small" @click="openCloneDialog">
          <el-icon><Download /></el-icon>
          克隆其他仓库
        </el-button>
      </div>
      
      <!-- 搜索和筛选 -->
      <div class="repo-controls">
        <el-input
          v-model="searchKeyword"
          placeholder="搜索仓库名称..."
          size="small"
          clearable
          class="search-input"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
        <el-select v-model="githubRepoType" size="small" @change="loadGithubRepos" class="filter-select">
          <el-option label="所有仓库" value="all" />
          <el-option label="我的仓库" value="owner" />
          <el-option label="公开仓库" value="public" />
          <el-option label="私有仓库" value="private" />
        </el-select>
      </div>
      
      <!-- 仓库统计 -->
      <div v-if="githubRepos.length > 0" class="repo-stats">
        <span>共 {{ filteredGithubRepos.length }} / {{ githubRepos.length }} 个仓库</span>
        <span v-if="repoStats" class="stats-detail">
          ({{ repoStats.public }} 公开 / {{ repoStats.private }} 私有)
        </span>
      </div>
      
      <!-- 私有仓库提示 -->
      <div v-if="githubRepos.length > 0 && repoStats && repoStats.private === 0" class="repo-warning">
        <el-alert 
          type="info" 
          :closable="false"
          show-icon
        >
          <template #title>
            未检测到私有仓库，请确保GitHub Token有 <strong>repo</strong> 权限
          </template>
        </el-alert>
      </div>
      
      <!-- GitHub仓库列表 -->
      <div class="repo-list" v-loading="loadingGithubRepos" ref="repoListRef">
        <!-- GitHub Token未配置 -->
        <div v-if="!githubTokenConfigured && !loadingGithubRepos" class="empty-repos">
          <el-empty description="未配置GitHub Token" :image-size="80">
            <div style="margin-top: 16px;">
              <p style="color: #999; font-size: 12px;">请在服务器环境变量中设置GITHUB_TOKEN</p>
              <el-link type="primary" href="https://github.com/settings/tokens" target="_blank">
                获取GitHub Token
              </el-link>
            </div>
          </el-empty>
        </div>
        
        <!-- 无搜索结果 -->
        <div v-else-if="filteredGithubRepos.length === 0 && githubRepos.length > 0 && !loadingGithubRepos" class="empty-repos">
          <el-empty description="未找到匹配的仓库" :image-size="80">
            <el-button size="small" @click="searchKeyword = ''">清空搜索</el-button>
          </el-empty>
        </div>
        
        <!-- 仓库列表为空 -->
        <div v-else-if="githubRepos.length === 0 && !loadingGithubRepos" class="empty-repos">
          <el-empty description="未找到GitHub仓库" :image-size="80" />
        </div>
        
        <!-- 仓库列表 -->
        <div 
          v-for="repo in filteredGithubRepos" 
          :key="repo.id" 
          class="repo-item github-repo"
        >
          <div class="repo-icon">
            <el-icon><Platform /></el-icon>
          </div>
          <div class="repo-info">
            <div class="repo-name">
              {{ repo.name }}
              <el-tag v-if="repo.is_private" size="small" type="warning">私有</el-tag>
              <el-tag v-if="repo.is_fork" size="small" type="info">Fork</el-tag>
            </div>
            <div class="repo-description">{{ repo.description || '暂无描述' }}</div>
            <div class="repo-meta">
              <span v-if="repo.language" class="language">
                <span class="dot" :style="{ backgroundColor: getLanguageColor(repo.language) }"></span>
                {{ repo.language }}
              </span>
              <span v-if="repo.stars > 0" class="stars">
                <el-icon><Star /></el-icon>
                {{ repo.stars }}
              </span>
              <span class="updated">更新于 {{ formatDate(repo.updated_at) }}</span>
            </div>
          </div>
          <el-button 
            size="small" 
            type="primary"
            @click="cloneGithubRepo(repo)"
            :loading="repo.cloning"
          >
            克隆
          </el-button>
        </div>
      </div>
    </div>
    
    <!-- Git仓库已初始化 -->
    <div v-else class="panel-content">
      <!-- 分支信息 -->
      <div class="section">
        <div class="section-title">
          <el-icon><Share /></el-icon>
          <span>当前分支</span>
        </div>
        <div class="branch-info">
          <el-tag size="small" type="primary">{{ currentBranch }}</el-tag>
          <el-button size="small" text @click="showBranchList = true">
            <el-icon><ArrowDown /></el-icon>
          </el-button>
        </div>
      </div>
      
      <!-- 远程仓库 -->
      <div class="section" v-if="remotes.length > 0">
        <div class="section-title">
          <el-icon><Link /></el-icon>
          <span>远程仓库</span>
        </div>
        <div class="remote-info">
          <div v-for="remote in remotes" :key="remote.name" class="remote-item">
            <span class="remote-name">{{ remote.name }}</span>
            <span class="remote-url">{{ remote.url }}</span>
          </div>
        </div>
      </div>
      
      <!-- 更改文件 -->
      <div class="section">
        <div class="section-title">
          <el-icon><Document /></el-icon>
          <span>更改 ({{ changedFiles.length }})</span>
        </div>
        <div class="file-list">
          <div 
            v-for="file in changedFiles" 
            :key="file.path" 
            class="file-item"
            :class="file.status"
          >
            <el-icon class="file-icon">
              <DocumentAdd v-if="file.status === 'A'" />
              <Edit v-else-if="file.status === 'M'" />
              <Delete v-else-if="file.status === 'D'" />
              <Document v-else />
            </el-icon>
            <span class="file-path">{{ file.path }}</span>
          </div>
          <div v-if="changedFiles.length === 0" class="empty-tip">
            暂无更改
          </div>
        </div>
      </div>
      
      <!-- 操作按钮 -->
      <div class="actions">
        <el-button size="small" @click="handleRefresh">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
        <el-button size="small" @click="handlePull">
          <el-icon><Download /></el-icon>
          拉取
        </el-button>
        <el-button size="small" type="primary" :disabled="changedFiles.length === 0" @click="showCommitDialog = true">
          <el-icon><Upload /></el-icon>
          提交
        </el-button>
        <el-button size="small" type="success" @click="handlePush">
          <el-icon><Upload /></el-icon>
          推送
        </el-button>
      </div>
    </div>
    
    <!-- 克隆仓库对话框 -->
    <el-dialog v-model="showCloneDialog" title="克隆GitHub仓库" width="500px">
      <el-form :model="cloneForm" label-width="100px">
        <el-form-item label="仓库URL">
          <el-input
            v-model="cloneForm.repo_url"
            placeholder="https://github.com/username/repo.git"
          />
        </el-form-item>
        <el-alert
          v-if="!gitConfigured"
          :title="gitConfigError"
          type="error"
          :closable="false"
          style="margin-bottom: 16px;"
        >
          <pre v-if="gitConfigHint" style="margin: 8px 0 0 0; font-size: 12px;">{{ gitConfigHint }}</pre>
        </el-alert>
        <el-alert
          v-else
          title="将使用服务器配置的Git身份进行克隆"
          type="info"
          :closable="false"
          style="margin-bottom: 16px;"
        >
          <template #default>
            <div style="margin-top: 4px; font-size: 12px;">
              用户: {{ gitUserName }} ({{ gitUserEmail }})
            </div>
          </template>
        </el-alert>
      </el-form>
      <template #footer>
        <el-button @click="showCloneDialog = false">取消</el-button>
        <el-button 
          type="primary" 
          @click="handleClone" 
          :loading="cloning"
          :disabled="!gitConfigured"
        >
          克隆
        </el-button>
      </template>
    </el-dialog>
    
    <!-- 分支选择对话框 -->
    <el-dialog v-model="showBranchList" title="切换分支" width="350px">
      <div class="branch-list">
        <div 
          v-for="branch in branches" 
          :key="branch" 
          class="branch-item"
          :class="{ active: branch === currentBranch }"
          @click="switchBranch(branch)"
        >
          <el-icon><Share /></el-icon>
          <span>{{ branch }}</span>
          <el-icon v-if="branch === currentBranch" class="check-icon"><Check /></el-icon>
        </div>
      </div>
    </el-dialog>
    
    <!-- 提交对话框 -->
    <el-dialog v-model="showCommitDialog" title="提交更改" width="400px">
      <el-form>
        <el-form-item label="提交信息">
          <el-input
            v-model="commitMessage"
            type="textarea"
            :rows="3"
            placeholder="输入提交信息..."
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCommitDialog = false">取消</el-button>
        <el-button type="primary" @click="handleCommit" :disabled="!commitMessage.trim()" :loading="committing">
          提交
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { 
  Share, Document, DocumentAdd, Edit, Delete, 
  ArrowDown, Refresh, Upload, Download, Check, Link,
  Platform, Star, Search
} from '@element-plus/icons-vue'

// 组件引用
const repoListRef = ref(null)

// 状态
const isGitRepo = ref(false)
const currentBranch = ref('')
const branches = ref([])
const remotes = ref([])
const changedFiles = ref([])
const showCloneDialog = ref(false)
const showBranchList = ref(false)
const showCommitDialog = ref(false)
const commitMessage = ref('')
const committing = ref(false)
const cloning = ref(false)

// Git配置状态
const gitConfigured = ref(false)
const gitUserName = ref('')
const gitUserEmail = ref('')
const gitConfigError = ref('')
const gitConfigHint = ref('')

// GitHub仓库列表状态
const githubRepos = ref([])
const loadingGithubRepos = ref(false)
const githubTokenConfigured = ref(false)
const githubRepoType = ref('owner')
const searchKeyword = ref('')
const repoStats = ref(null)

// 克隆表单
const cloneForm = ref({
  repo_url: ''
})

// 过滤后的GitHub仓库列表
const filteredGithubRepos = computed(() => {
  if (!searchKeyword.value.trim()) {
    return githubRepos.value
  }
  
  const keyword = searchKeyword.value.toLowerCase().trim()
  return githubRepos.value.filter(repo => 
    repo.name.toLowerCase().includes(keyword) ||
    repo.full_name.toLowerCase().includes(keyword) ||
    (repo.description && repo.description.toLowerCase().includes(keyword))
  )
})

// 检查Git配置
async function checkGitConfig() {
  try {
    const response = await fetch('/api/git/check-config/')
    const data = await response.json()
    
    if (data.configured) {
      gitConfigured.value = true
      gitUserName.value = data.user_name
      gitUserEmail.value = data.user_email
      gitConfigError.value = ''
      gitConfigHint.value = ''
    } else {
      gitConfigured.value = false
      gitConfigError.value = data.error || 'Git未配置'
      gitConfigHint.value = data.hint || ''
    }
  } catch (error) {
    console.error('检查Git配置失败:', error)
    gitConfigured.value = false
    gitConfigError.value = '检查Git配置失败'
  }
}

// 加载Git状态
async function loadGitStatus() {
  try {
    const response = await fetch('/api/git/status/')
    const data = await response.json()
    
    if (data.is_repo) {
      isGitRepo.value = true
      currentBranch.value = data.branch
      branches.value = data.branches
      remotes.value = data.remotes
      changedFiles.value = data.changed_files
    } else {
      isGitRepo.value = false
      // 工作区不是Git仓库，加载GitHub仓库列表
      loadGithubRepos()
    }
  } catch (error) {
    console.error('加载Git状态失败:', error)
    ElMessage.error('加载Git状态失败')
  }
}

// 加载GitHub仓库列表
async function loadGithubRepos() {
  loadingGithubRepos.value = true
  try {
    const params = new URLSearchParams()
    params.append('type', githubRepoType.value)
    
    const response = await fetch(`/api/git/list-github-repos/?${params}`)
    const data = await response.json()
    
    if (data.success) {
      githubRepos.value = data.repos.map(repo => ({ ...repo, cloning: false }))
      githubTokenConfigured.value = true
      repoStats.value = data.stats || null
    } else {
      githubTokenConfigured.value = false
      repoStats.value = null
      if (data.error !== '未配置GitHub Token') {
        ElMessage.error(data.error || '加载GitHub仓库失败')
        if (data.hint) {
          ElMessage.info({ message: data.hint, duration: 5000 })
        }
      }
    }
  } catch (error) {
    console.error('加载GitHub仓库失败:', error)
    ElMessage.error('加载GitHub仓库失败')
  } finally {
    loadingGithubRepos.value = false
  }
}

// 克隆GitHub仓库
async function cloneGithubRepo(repo) {
  if (!gitConfigured.value) {
    ElMessage.error('Git未配置，请先配置服务器Git身份')
    return
  }
  
  try {
    await ElMessageBox.confirm(
      `确定要克隆仓库 ${repo.full_name} 到本地吗？`,
      '确认克隆',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'info'
      }
    )
    
    repo.cloning = true
    
    const response = await fetch('/api/git/clone/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ repo_url: repo.clone_url })
    })
    
    const data = await response.json()
    
    if (data.success) {
      ElMessage.success(data.message)
      
      // 询问是否切换到新克隆的仓库
      try {
        await ElMessageBox.confirm(
          '克隆成功！是否将工作区切换到新仓库？',
          '切换工作区',
          {
            confirmButtonText: '切换',
            cancelButtonText: '取消',
            type: 'success'
          }
        )
        
        // 设置工作区
        await setWorkspace(data.path)
      } catch {
        // 用户取消
      }
    } else {
      ElMessage.error(data.error || '克隆失败')
      if (data.hint) {
        ElMessage.info({ message: data.hint, duration: 5000 })
      }
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('克隆失败:', error)
      ElMessage.error('克隆失败')
    }
  } finally {
    repo.cloning = false
  }
}

// 设置工作区
async function setWorkspace(path) {
  try {
    const response = await fetch('/api/workspace/set/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ path })
    })
    
    const data = await response.json()
    
    if (data.success) {
      ElMessage.success(data.message)
      // 刷新页面以应用新的工作区
      window.location.reload()
    } else {
      ElMessage.error(data.error || '设置工作区失败')
    }
  } catch (error) {
    console.error('设置工作区失败:', error)
    ElMessage.error('设置工作区失败')
  }
}

// 获取编程语言颜色
function getLanguageColor(language) {
  const colors = {
    'JavaScript': '#f1e05a',
    'TypeScript': '#2b7489',
    'Python': '#3572A5',
    'Java': '#b07219',
    'C++': '#f34b7d',
    'C': '#555555',
    'Go': '#00ADD8',
    'Rust': '#dea584',
    'Vue': '#41b883',
    'HTML': '#e34c26',
    'CSS': '#563d7c',
    'Shell': '#89e051'
  }
  return colors[language] || '#cccccc'
}

// 格式化日期
function formatDate(dateString) {
  const date = new Date(dateString)
  const now = new Date()
  const diff = now - date
  const days = Math.floor(diff / (1000 * 60 * 60 * 24))
  
  if (days === 0) return '今天'
  if (days === 1) return '昨天'
  if (days < 7) return `${days}天前`
  if (days < 30) return `${Math.floor(days / 7)}周前`
  if (days < 365) return `${Math.floor(days / 30)}个月前`
  return `${Math.floor(days / 365)}年前`
}

// 刷新
function handleRefresh() {
  loadGitStatus()
  ElMessage.success('已刷新')
}

// 打开克隆对话框
function openCloneDialog() {
  checkGitConfig()
  showCloneDialog.value = true
}

// 克隆仓库
async function handleClone() {
  if (!cloneForm.value.repo_url) {
    ElMessage.warning('请输入仓库URL')
    return
  }
  
  if (!gitConfigured.value) {
    ElMessage.error('Git未配置，请先配置服务器Git身份')
    return
  }
  
  cloning.value = true
  try {
    const response = await fetch('/api/git/clone/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ repo_url: cloneForm.value.repo_url })
    })
    
    const data = await response.json()
    
    if (data.success) {
      ElMessage.success(data.message)
      showCloneDialog.value = false
      cloneForm.value = { repo_url: '' }
      // 刷新文件树和Git状态
      window.location.reload()
    } else {
      ElMessage.error(data.error || '克隆失败')
      if (data.hint) {
        ElMessage.info({ message: data.hint, duration: 5000 })
      }
    }
  } catch (error) {
    console.error('克隆失败:', error)
    ElMessage.error('克隆失败')
  } finally {
    cloning.value = false
  }
}

// 切换分支
async function switchBranch(branch) {
  try {
    const response = await fetch('/api/git/switch-branch/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ branch })
    })
    
    const data = await response.json()
    
    if (data.success) {
      currentBranch.value = branch
      showBranchList.value = false
      ElMessage.success(data.message)
      loadGitStatus()
    } else {
      ElMessage.error(data.error || '切换分支失败')
    }
  } catch (error) {
    console.error('切换分支失败:', error)
    ElMessage.error('切换分支失败')
  }
}

// 提交
async function handleCommit() {
  if (!commitMessage.value.trim()) return
  
  committing.value = true
  try {
    const response = await fetch('/api/git/commit/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: commitMessage.value })
    })
    
    const data = await response.json()
    
    if (data.success) {
      ElMessage.success(data.message)
      commitMessage.value = ''
      showCommitDialog.value = false
      loadGitStatus()
    } else {
      ElMessage.error(data.error || '提交失败')
    }
  } catch (error) {
    console.error('提交失败:', error)
    ElMessage.error('提交失败')
  } finally {
    committing.value = false
  }
}

// 推送
async function handlePush() {
  try {
    const response = await fetch('/api/git/push/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({})
    })
    
    const data = await response.json()
    
    if (data.success) {
      ElMessage.success(data.message)
    } else {
      ElMessage.error(data.error || '推送失败')
    }
  } catch (error) {
    console.error('推送失败:', error)
    ElMessage.error('推送失败')
  }
}

// 拉取
async function handlePull() {
  try {
    const response = await fetch('/api/git/pull/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({})
    })
    
    const data = await response.json()
    
    if (data.success) {
      ElMessage.success(data.message)
      loadGitStatus()
    } else {
      ElMessage.error(data.error || '拉取失败')
    }
  } catch (error) {
    console.error('拉取失败:', error)
    ElMessage.error('拉取失败')
  }
}

// 组件挂载时加载Git状态和检查配置
onMounted(() => {
  loadGitStatus()
  checkGitConfig()
})
</script>

<style scoped>
.git-panel {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: #1e1e1e;
}

/* 仓库列表容器 */
.repo-list-container {
  height: 100%;
  display: flex;
  flex-direction: column;
  padding: 12px;
  overflow: hidden;
}

.repo-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  flex-shrink: 0;
}

.repo-header h3 {
  display: flex;
  align-items: center;
  gap: 6px;
  margin: 0;
  font-size: 14px;
  color: #e0e0e0;
}

.repo-controls {
  display: flex;
  gap: 8px;
  margin-bottom: 12px;
  flex-shrink: 0;
  flex-wrap: wrap;
}

.search-input {
  flex: 1;
}

.filter-select {
  width: 100px;
  flex-shrink: 0;
}

.repo-stats {
  font-size: 11px;
  color: #999;
  margin-bottom: 8px;
  padding: 4px 8px;
  background: rgba(64, 158, 255, 0.1);
  border-radius: 4px;
  display: flex;
  gap: 8px;
  flex-shrink: 0;
}

.stats-detail {
  color: #888;
}

.repo-warning {
  margin-bottom: 12px;
  flex-shrink: 0;
}

.repo-list {
  flex: 1;
  overflow-x: hidden;
  overflow-y: auto;
  min-height: 0;
  max-height: 500px;
}

.empty-repos {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 200px;
}

.repo-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px;
  margin-bottom: 6px;
  background: #252526;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
}

.repo-item:hover {
  background: #2d2d2d;
  transform: translateX(4px);
}

.repo-icon {
  font-size: 28px;
  color: #409eff;
  flex-shrink: 0;
}

.repo-info {
  flex: 1;
  min-width: 0;
  overflow: hidden;
}

.repo-name {
  font-size: 13px;
  font-weight: 600;
  color: #e0e0e0;
  margin-bottom: 3px;
  display: flex;
  align-items: center;
  gap: 6px;
}

.repo-description {
  font-size: 11px;
  color: #999;
  margin-bottom: 4px;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 1;
  -webkit-box-orient: vertical;
}

.repo-meta {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 10px;
  color: #888;
}

.language {
  display: flex;
  align-items: center;
  gap: 4px;
}

.dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.stars {
  display: flex;
  align-items: center;
  gap: 2px;
}

.updated {
  margin-left: auto;
}

/* Git仓库内容 */
.panel-content {
  flex: 1;
  overflow-y: auto;
  padding: 12px;
}

.section {
  margin-bottom: 16px;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 8px;
  color: #888;
  font-size: 12px;
}

.branch-info {
  display: flex;
  align-items: center;
  gap: 8px;
}

.remote-info {
  background: #252526;
  border-radius: 6px;
  padding: 8px;
}

.remote-item {
  margin-bottom: 8px;
}

.remote-item:last-child {
  margin-bottom: 0;
}

.remote-name {
  font-weight: 600;
  color: #409eff;
  margin-right: 8px;
}

.remote-url {
  color: #999;
  font-size: 11px;
}

.file-list {
  background: #252526;
  border-radius: 6px;
  overflow: hidden;
}

.file-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  border-bottom: 1px solid #333;
  font-size: 12px;
  color: #ccc;
}

.file-item:last-child {
  border-bottom: none;
}

.file-item.A {
  color: #67c23a;
}

.file-item.M {
  color: #e6a23c;
}

.file-item.D {
  color: #f56c6c;
}

.file-icon {
  font-size: 14px;
}

.file-path {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.empty-tip {
  padding: 16px;
  text-align: center;
  color: #666;
  font-size: 12px;
}

.actions {
  display: flex;
  gap: 8px;
  padding-top: 12px;
  border-top: 1px solid #333;
  flex-wrap: wrap;
}

.branch-list {
  max-height: 300px;
  overflow-y: auto;
}

.branch-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  cursor: pointer;
  color: #ccc;
}

.branch-item:hover {
  background: #2d2d2d;
}

.branch-item.active {
  color: #409eff;
}

.check-icon {
  margin-left: auto;
  color: #409eff;
}

/* 滚动条样式 */
.panel-content::-webkit-scrollbar,
.repo-list::-webkit-scrollbar {
  width: 8px;
}

.panel-content::-webkit-scrollbar-track,
.repo-list::-webkit-scrollbar-track {
  background: #1a1a1a;
  border-radius: 4px;
}

.panel-content::-webkit-scrollbar-thumb,
.repo-list::-webkit-scrollbar-thumb {
  background: #555;
  border-radius: 4px;
}

.panel-content::-webkit-scrollbar-thumb:hover,
.repo-list::-webkit-scrollbar-thumb:hover {
  background: #666;
}
</style>
