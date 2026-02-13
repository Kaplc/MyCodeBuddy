<template>
  <header class="app-header" :style="{ fontSize: uiFontSize + 'px' }">
    <div class="header-left">
      <el-icon class="logo-icon"><Edit /></el-icon>
      <span class="app-title">RemoteBuddy</span>
      
      <!-- 导航菜单 -->
      <nav class="nav-menu">
        <el-dropdown trigger="click" @command="handleCommand">
          <span class="nav-item">
            编辑
            <el-icon class="arrow"><ArrowDown /></el-icon>
          </span>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="undo">
                <el-icon><Back /></el-icon>
                撤销
              </el-dropdown-item>
              <el-dropdown-item command="redo">
                <el-icon><Right /></el-icon>
                重做
              </el-dropdown-item>
              <el-dropdown-item command="cut" :divided="true">
                <el-icon><Operation /></el-icon>
                剪切
              </el-dropdown-item>
              <el-dropdown-item command="copy">
                <el-icon><CopyDocument /></el-icon>
                复制
              </el-dropdown-item>
              <el-dropdown-item command="paste">
                <el-icon><Document /></el-icon>
                粘贴
              </el-dropdown-item>
              <el-dropdown-item command="find" :divided="true">
                <el-icon><Search /></el-icon>
                查找
              </el-dropdown-item>
              <el-dropdown-item command="replace">
                <el-icon><Switch /></el-icon>
                替换
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>

        <el-dropdown trigger="click" @command="handleCommand">
          <span class="nav-item">
            版本管理
            <el-icon class="arrow"><ArrowDown /></el-icon>
          </span>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="git">
                <el-icon><Share /></el-icon>
                Git
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>

        <el-dropdown trigger="click" @command="handleCommand">
          <span class="nav-item">
            设置
            <el-icon class="arrow"><ArrowDown /></el-icon>
          </span>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="appearance">
                <el-icon><Setting /></el-icon>
                外观
              </el-dropdown-item>
              <el-dropdown-item command="editorSettings">
                <el-icon><Document /></el-icon>
                文本编辑器
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </nav>
    </div>
    
    <div class="header-right">
    </div>
  </header>
</template>

<script setup>
import { 
  Edit, Setting, Share, ArrowDown,
  Document, FolderOpened, DocumentCopy, Back, Right,
  Operation, CopyDocument, Search, Switch, Fold, 
  ChatDotRound, Monitor, ZoomIn, ZoomOut, Aim,
  MagicStick, Reading, Key, InfoFilled
} from '@element-plus/icons-vue'

// Props
const props = defineProps({
  uiFontSize: {
    type: Number,
    default: 14
  }
})

// Emits
const emit = defineEmits(['command'])

// 处理命令
function handleCommand(command) {
  emit('command', command)
}
</script>

<style scoped>
.app-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: #323233;
  border-bottom: 1px solid #333;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.logo-icon {
  font-size: 24px;
  color: #0969da;
  font-weight: bold;
}

.app-title {
  font-size: 16px;
  font-weight: 600;
  color: #e0e0e0;
}

.nav-menu {
  display: flex;
  align-items: center;
  gap: 4px;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 2px;
  padding: 6px 12px;
  font-size: 13px;
  color: #e0e0e0;
  cursor: pointer;
  border-radius: 4px;
}

.nav-item:hover {
  background: rgba(255, 255, 255, 0.15);
  color: #ffffff;
}

.nav-item .arrow {
  font-size: 10px;
  margin-left: 2px;
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
  border-radius: 12px;
}
</style>
