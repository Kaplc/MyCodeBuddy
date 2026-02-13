<template>
  <div class="search-panel" v-show="visible">
    <div class="search-header">
      <span class="search-title">搜索</span>
      <el-button class="close-btn" text @click="visible = false">
        <el-icon><Close /></el-icon>
      </el-button>
    </div>

    <!-- 搜索输入 -->
    <div class="search-input-wrapper">
      <el-input
        ref="searchInputRef"
        v-model="searchText"
        placeholder="搜索内容"
        @keyup.enter="handleSearch"
        @input="handleInput"
      >
        <template #prefix>
          <el-icon><Search /></el-icon>
        </template>
      </el-input>
    </div>

    <!-- 搜索选项 -->
    <div class="search-options">
      <el-checkbox v-model="options.regex">正则</el-checkbox>
      <el-checkbox v-model="options.caseSensitive">区分大小写</el-checkbox>
    </div>

    <!-- 搜索结果 -->
    <div class="search-results" v-if="results.length > 0">
      <div class="results-count">{{ results.length }} 个文件</div>
      <div
        v-for="result in results"
        :key="result.file"
        class="result-file"
        @click="handleFileClick(result)"
      >
        <div class="result-file-header">
          <el-icon class="file-icon"><Document /></el-icon>
          <span class="file-name">{{ result.file }}</span>
        </div>
        <div class="result-matches">
          <div
            v-for="(match, idx) in result.matches.slice(0, 3)"
            :key="idx"
            class="result-match"
            @click.stop="handleMatchClick(result, match)"
          >
            <span class="line-number">{{ match.line }}:</span>
            <span class="match-content" v-html="highlightMatch(match.lineContent)"></span>
          </div>
          <div v-if="result.matches.length > 3" class="more-matches">
            +{{ result.matches.length - 3 }} 更多
          </div>
        </div>
      </div>
    </div>

    <!-- 空状态 -->
    <div class="search-empty" v-else-if="searched && searchText">
      <span>无结果</span>
    </div>

    <!-- 初始状态 -->
    <div class="search-initial" v-else-if="!searched">
      <span>输入搜索内容</span>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, nextTick } from 'vue'
import { Search, Document, Close } from '@element-plus/icons-vue'
import axios from 'axios'

const props = defineProps({
  modelValue: Boolean
})

const emit = defineEmits(['update:modelValue', 'select-file'])

const visible = ref(props.modelValue)
const searchInputRef = ref(null)
const searchText = ref('')
const searched = ref(false)
const results = ref([])
const options = ref({
  regex: false,
  caseSensitive: false,
  wholeWord: false
})

let searchTimeout = null

watch(() => props.modelValue, (val) => {
  visible.value = val
  if (val) {
    nextTick(() => {
      searchInputRef.value?.focus()
    })
  }
})

watch(visible, (val) => {
  emit('update:modelValue', val)
})

function handleOpen() {
  searchText.value = ''
  results.value = []
  searched.value = false
  searchInputRef.value?.focus()
}

function handleInput() {
  clearTimeout(searchTimeout)
  if (searchText.value.length >= 2) {
    searchTimeout = setTimeout(() => {
      handleSearch()
    }, 500)
  } else {
    results.value = []
    searched.value = false
  }
}

async function handleSearch() {
  if (!searchText.value.trim()) return

  searched.value = true
  try {
    const response = await axios.post('/api/search/content/', {
      query: searchText.value,
      options: options.value
    })
    if (response.data.error) {
      ElMessage.warning(response.data.error)
      results.value = []
    } else {
      results.value = response.data.results || []
    }
  } catch (error) {
    console.error('搜索失败:', error)
    results.value = []
  }
}

function handleFileClick(result) {
  if (result.matches.length > 0) {
    handleMatchClick(result, result.matches[0])
  }
}

function handleMatchClick(result, match) {
  emit('select-file', {
    file: result.file,
    line: match.line,
    column: match.column
  })
  visible.value = false
}

function highlightMatch(text) {
  if (!searchText.value) return text
  const escaped = searchText.value.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
  const regex = new RegExp(`(${escaped})`, 'gi')
  return text.replace(regex, '<mark>$1</mark>')
}
</script>

<style scoped>
.search-panel {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: #1e1e1e;
  border-right: 1px solid #333;
}

.search-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  border-bottom: 1px solid #333;
  background: #252526;
}

.search-title {
  font-size: 13px;
  font-weight: 500;
  color: #e0e0e0;
}

.close-btn {
  padding: 4px;
  color: #999;
}

.close-btn:hover {
  color: #fff;
}

.search-input-wrapper {
  padding: 12px;
  margin-bottom: 0;
}

.search-input-wrapper :deep(.el-input__wrapper) {
  background: #252526;
  box-shadow: none;
  border: 1px solid #333;
}

.search-input-wrapper :deep(.el-input__wrapper:hover),
.search-input-wrapper :deep(.el-input__wrapper.is-focus) {
  border-color: #409eff;
}

.search-options {
  display: flex;
  gap: 12px;
  padding: 0 12px 12px;
  font-size: 12px;
}

.search-options :deep(.el-checkbox__label) {
  color: #999;
}

.results-count {
  font-size: 12px;
  color: #999;
  padding: 8px 12px;
}

.search-results {
  flex: 1;
  overflow-y: auto;
  padding: 0 12px 12px;
}

.result-file {
  border: 1px solid #333;
  border-radius: 4px;
  margin-bottom: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.result-file:hover {
  border-color: #409eff;
  background: rgba(64, 158, 255, 0.1);
}

.result-file-header {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 10px;
  background: rgba(0, 0, 0, 0.2);
  border-bottom: 1px solid #333;
}

.result-file-header .file-icon {
  color: #dcb67a;
}

.result-file-header .file-name {
  flex: 1;
  font-size: 13px;
  color: #e0e0e0;
}

.result-matches {
  padding: 6px 0;
}

.result-match {
  display: flex;
  gap: 8px;
  padding: 4px 10px;
  font-size: 12px;
  cursor: pointer;
}

.result-match:hover {
  background: rgba(64, 158, 255, 0.1);
}

.line-number {
  color: #666;
  min-width: 30px;
}

.match-content {
  color: #ccc;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.match-content :deep(mark) {
  background: #f6b44c;
  color: #1e1e1e;
  padding: 0 2px;
  border-radius: 2px;
}

.more-matches {
  font-size: 11px;
  color: #666;
  padding: 4px 10px;
}

.search-empty,
.search-initial {
  text-align: center;
  padding: 40px;
  color: #666;
  font-size: 13px;
}
</style>
