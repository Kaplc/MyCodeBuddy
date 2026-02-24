<template>
  <div class="code-editor">
    <div class="editor-header">
      <div class="file-info">
        <span class="file-path" :title="currentFile?.path">{{ currentFile?.path || '未选择文件' }}</span>
        <span v-if="hasUnsavedChanges" class="unsaved-indicator">●</span>
      </div>

    </div>
    
    <div ref="editorContainer" class="editor-container"></div>
    
    <div v-if="loading" class="loading-overlay">
      <el-icon class="is-loading"><Loading /></el-icon>
      <span>加载中...</span>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch, shallowRef } from 'vue'
import { ElMessage } from 'element-plus'
import { Loading } from '@element-plus/icons-vue'
import * as monaco from 'monaco-editor'
import axios from 'axios'
import { loadHLSLTextMate, defineEnhancedTheme } from '../utils/textmate-loader'

// 定义事件
const emit = defineEmits(['selection-change', 'cursor-change'])

// Props
const props = defineProps({
  file: {
    type: Object,
    default: null
  },
  fontSize: {
    type: Number,
    default: 14
  }
})

// 状态
const editorContainer = ref(null)
const currentFile = ref(null)
const loading = ref(false)
const hasUnsavedChanges = ref(false)

// Monaco Editor实例（使用shallowRef避免深度响应）
const editor = shallowRef(null)

// 自动保存相关
const autoSaveTimer = ref(null)

// 初始化 TextMate 语法
async function initTextMate() {
  // 加载 HLSL TextMate 语法
  loadHLSLTextMate()
  
  // 定义增强主题
  defineEnhancedTheme()
  
  console.log('✅ Shader 语法高亮已启用 (TextMate 增强版)')
}

// 初始化编辑器
onMounted(() => {
  initEditor()
})

// 销毁编辑器
onUnmounted(() => {
  if (editor.value) {
    editor.value.dispose()
  }
  // 清除自动保存定时器
  if (autoSaveTimer.value) {
    clearTimeout(autoSaveTimer.value)
  }
})

// 监听文件变化
watch(() => props.file, (newFile) => {
  if (newFile) {
    loadFile(newFile)
  }
})

// 监听字体大小变化
watch(() => props.fontSize, (newSize) => {
  if (editor.value) {
    editor.value.updateOptions({ fontSize: newSize })
  }
})

// 初始化Monaco Editor
async function initEditor() {
  if (!editorContainer.value) return

  // 初始化 TextMate 语法
  await initTextMate()

  editor.value = monaco.editor.create(editorContainer.value, {
    value: '',
    language: 'plaintext',
    theme: 'enhanced-dark-hlsl',  // 使用新的增强主题
    automaticLayout: true,
    fontSize: props.fontSize,
    fontFamily: "'Fira Code', 'Consolas', 'Monaco', 'Courier New', monospace",
    fontLigatures: true,
    lineNumbers: 'on',
    minimap: { enabled: true },
    scrollBeyondLastLine: false,
    wordWrap: 'on',
    tabSize: 2,
    renderWhitespace: 'selection',
    folding: true,
    bracketPairColorization: { enabled: true },
    smoothScrolling: true,
    cursorBlinking: 'smooth',
    cursorSmoothCaretAnimation: 'on',
    renderLineHighlight: 'all',
    occurrencesHighlight: 'singleFile',
    selectionHighlight: true,
    codeLens: false,
    overviewRulerBorder: false,
    renderVerticalScrollbar: 'auto',
    renderHorizontalScrollbar: 'auto',
    quickSuggestions: {
      other: true,
      comments: false,
      strings: false
    },
    suggestOnTriggerCharacters: true,
    acceptSuggestionOnCommitCharacter: true,
    acceptSuggestionOnEnter: 'off',
    snippetSuggestions: 'top'
  })
  
  // 注册AI代码补全提供器
  registerAICompletionProvider()
  
  // 监听内容变化
  editor.value.onDidChangeModelContent(() => {
    hasUnsavedChanges.value = true

    // 清除之前的定时器
    if (autoSaveTimer.value) {
      clearTimeout(autoSaveTimer.value)
    }

    // 设置新的自动保存定时器（3秒后保存）
    autoSaveTimer.value = setTimeout(() => {
      saveCurrentFile()
    }, 3000)

    // 内容变化时也发出光标位置信息（包含新的总行数）
    const position = editor.value.getPosition()
    if (position) {
      const lineCount = editor.value.getModel().getLineCount()
      emit('cursor-change', {
        line: position.lineNumber,
        column: position.column,
        lineCount: lineCount
      })
    }
  })
  
  // 监听选择变化
  editor.value.onDidChangeCursorSelection((e) => {
    const selection = editor.value.getSelection()
    if (selection && !selection.isEmpty()) {
      const selectedText = editor.value.getModel().getValueInRange(selection)
      emit('selection-change', selectedText)
    }
    // 发出光标位置变化事件
    const position = editor.value.getPosition()
    if (position) {
      const lineCount = editor.value.getModel().getLineCount()
      emit('cursor-change', {
        line: position.lineNumber,
        column: position.column,
        lineCount: lineCount
      })
    }
  })
  
  // 监听粘贴事件，检测代码块
  editor.value.onDidPaste((e) => {
    // 可以在这里处理粘贴的代码
  })
}

// 加载文件
async function loadFile(file) {
  if (!editor.value) return
  
  loading.value = true
  
  try {
    const response = await axios.get('/api/files/read/', {
      params: { path: file.path }
    })
    
    // 检查是否为二进制文件
    if (response.data.is_binary) {
      ElMessage.warning('该文件是二进制文件，无法在编辑器中显示')
      // 显示文件信息而非内容
      const size = response.data.size || 0
      const sizeStr = size > 1024 * 1024 
        ? (size / 1024 / 1024).toFixed(2) + ' MB' 
        : (size / 1024).toFixed(2) + ' KB'
      editor.value.setValue(`[二进制文件]\n\n文件: ${file.path}\n类型: ${response.data.mime_type || '未知'}\n大小: ${sizeStr}\n\n此文件无法在编辑器中编辑。`)
      monaco.editor.setModelLanguage(editor.value.getModel(), 'plaintext')
      currentFile.value = null // 不允许编辑二进制文件
      hasUnsavedChanges.value = false
      loading.value = false
      return
    }
    
    currentFile.value = file
    
    // 设置编辑器内容和语言
    editor.value.setValue(response.data.content)
    
    // 根据文件扩展名设置语言
    const language = getLanguageFromPath(file.path)
    monaco.editor.setModelLanguage(editor.value.getModel(), language)
    
    hasUnsavedChanges.value = false
  } catch (error) {
    ElMessage.error('加载文件失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    loading.value = false
  }
}

// 根据路径获取语言
function getLanguageFromPath(path) {
  const ext = path.split('.').pop()?.toLowerCase()
  const langMap = {
    'js': 'javascript',
    'jsx': 'javascript',
    'ts': 'typescript',
    'tsx': 'typescript',
    'vue': 'vue',
    'html': 'html',
    'css': 'css',
    'scss': 'scss',
    'less': 'less',
    'json': 'json',
    'md': 'markdown',
    'py': 'python',
    'lua': 'lua',
    'java': 'java',
    'go': 'go',
    'rs': 'rust',
    'c': 'c',
    'cpp': 'cpp',
    'h': 'c',
    'hpp': 'cpp',
    'cs': 'csharp',
    'rb': 'ruby',
    'php': 'php',
    'sql': 'sql',
    'yaml': 'yaml',
    'yml': 'yaml',
    'xml': 'xml',
    'sh': 'shell',
    'bash': 'shell',
    'ps1': 'powershell',
    // Shader 文件
    'shader': 'hlsl',      // Unity Shader
    'glsl': 'glsl',        // OpenGL Shader
    'vert': 'glsl',        // GLSL Vertex Shader
    'frag': 'glsl',        // GLSL Fragment Shader
    'geom': 'glsl',        // GLSL Geometry Shader
    'comp': 'glsl',        // GLSL Compute Shader
    'tesc': 'glsl',        // GLSL Tessellation Control
    'tese': 'glsl',        // GLSL Tessellation Evaluation
    'hlsl': 'hlsl',        // DirectX Shader
    'fx': 'hlsl',          // DirectX Effect
    'cg': 'hlsl',          // NVIDIA Cg (similar to HLSL)
    'cginc': 'hlsl',       // Unity CG Include
    'compute': 'glsl',     // Unity Compute Shader
    'raytrace': 'hlsl',    // Ray Tracing Shader
  }
  return langMap[ext] || 'plaintext'
}

// 注册AI代码补全提供器
function registerAICompletionProvider() {
  // 为所有语言注册补全提供器
  const languages = ['javascript', 'typescript', 'python', 'java', 'go', 'cpp', 'csharp', 'php', 'ruby', 'rust', 'lua']

  languages.forEach(language => {
    monaco.languages.registerCompletionItemProvider(language, {
      triggerCharacters: ['.', '(', ' ', '\n'],
      provideCompletionItems: async (model, position) => {
        try {
          // 获取当前行之前的文本作为上下文
          const textBeforeCursor = model.getValueInRange({
            startLineNumber: Math.max(1, position.lineNumber - 10),
            startColumn: 1,
            endLineNumber: position.lineNumber,
            endColumn: position.column
          })
          
          // 获取当前行文本
          const currentLine = model.getLineContent(position.lineNumber)
          const textBeforePosition = currentLine.substring(0, position.column - 1)
          
          // 如果文本太短，不触发AI补全
          if (textBeforePosition.trim().length < 2) {
            return { suggestions: [] }
          }
          
          // 调用AI补全API
          const response = await axios.post('/api/ai/complete/', {
            code: textBeforeCursor,
            language: language,
            position: {
              line: position.lineNumber,
              column: position.column
            }
          }, {
            timeout: 3000 // 3秒超时
          })
          
          if (response.data.suggestions && response.data.suggestions.length > 0) {
            // 获取当前行从行首到光标位置的文本
            const lineContent = model.getLineContent(position.lineNumber)
            const textBeforeCursor = lineContent.substring(0, position.column - 1)
            
            // 找到最后一个单词的开始位置（标识符：字母、数字、下划线）
            let wordStart = position.column - 1
            while (wordStart > 0 && /[\w]/.test(textBeforeCursor[wordStart - 1])) {
              wordStart--
            }
            
            // 获取当前已输入的单词
            const currentWord = textBeforeCursor.substring(wordStart)
            // 获取光标前的完整文本（可能包含非单词字符如括号）
            const fullTextBeforeCursor = textBeforeCursor

            return {
              suggestions: response.data.suggestions.map((suggestion, index) => {
                let insertText = suggestion.text
                let rangeStartColumn = position.column

                // 检查建议文本与光标前已输入文本的重叠（后缀匹配）
                // 例如：光标前文本 "int result"，AI返回 "int result = a;"
                // 需要找到已输入文本的后缀与建议文本的前缀的最长重叠
                if (fullTextBeforeCursor.length > 0 && suggestion.text.length > 0) {
                  let bestOverlap = 0
                  const maxCheck = Math.min(fullTextBeforeCursor.length, suggestion.text.length)
                  
                  // 从长到短检查：已输入文本的后缀 是否等于 建议文本的前缀
                  for (let len = maxCheck; len >= 1; len--) {
                    const suffix = fullTextBeforeCursor.substring(fullTextBeforeCursor.length - len)
                    const prefix = suggestion.text.substring(0, len)
                    if (suffix === prefix) {
                      bestOverlap = len
                      break
                    }
                  }
                  
                  if (bestOverlap > 0) {
                    // 有重叠：将range起始位置回退到重叠开始处，插入完整建议文本
                    // 这样Monaco会用完整建议文本替换从rangeStartColumn到光标位置的内容
                    rangeStartColumn = position.column - bestOverlap
                    insertText = suggestion.text
                  }
                }
                
                // 如果没有后缀重叠，再检查建议是否以当前单词开头
                if (rangeStartColumn === position.column && currentWord && suggestion.text.startsWith(currentWord)) {
                  rangeStartColumn = wordStart + 1
                  insertText = suggestion.text
                }

                return {
                  label: suggestion.text,
                  kind: monaco.languages.CompletionItemKind.Snippet,
                  insertText: insertText,
                  detail: '✨ AI建议',
                  documentation: suggestion.description || 'AI生成的代码补全',
                  sortText: `0${index}`,
                  range: {
                    startLineNumber: position.lineNumber,
                    startColumn: rangeStartColumn,
                    endLineNumber: position.lineNumber,
                    endColumn: position.column
                  }
                }
              })
            }
          }
        } catch (error) {
          // AI补全失败时静默处理，不影响正常使用
          console.warn('AI补全失败:', error.message)
        }
        
        return { suggestions: [] }
      }
    })
  })
}

// 插入代码
function insertCode(code, position = null) {
  if (!editor.value) return
  
  const pos = position || editor.value.getPosition()
  editor.value.executeEdits('', [{
    range: new monaco.Range(pos.lineNumber, pos.column, pos.lineNumber, pos.column),
    text: code,
    forceMoveMarkers: true
  }])
  
  editor.value.focus()
}

// 获取当前内容
function getContent() {
  return editor.value?.getValue() || ''
}

// 保存当前文件（自动保存）
async function saveCurrentFile() {
  if (!currentFile.value || !editor.value) return

  try {
    const content = editor.value.getValue()
    await axios.post('/api/files/save/', {
      path: currentFile.value.path,
      content: content
    })
    hasUnsavedChanges.value = false
    // 可选：显示保存成功的提示（如果不需要可以注释掉）
    // ElMessage.success('文件已自动保存')
  } catch (error) {
    console.error('自动保存失败:', error)
    ElMessage.error('保存失败: ' + (error.response?.data?.error || error.message))
  }
}

// 手动保存文件
async function saveFile() {
  await saveCurrentFile()
  if (!hasUnsavedChanges.value) {
    ElMessage.success('文件已保存')
  }
}

// 设置内容
function setContent(content) {
  if (editor.value) {
    editor.value.setValue(content)
  }
}

// 获取选中文本
function getSelectedText() {
  if (!editor.value) return ''
  const selection = editor.value.getSelection()
  if (selection && !selection.isEmpty()) {
    return editor.value.getModel().getValueInRange(selection)
  }
  return ''
}

// 重新加载当前文件
async function reloadFile() {
  if (!currentFile.value) {
    console.log('[CodeEditor] reloadFile: 没有当前文件')
    return
  }
  
  console.log('[CodeEditor] 开始重新加载文件:', currentFile.value.path)
  
  // 保存当前光标位置
  const position = editor.value?.getPosition()
  console.log('[CodeEditor] 保存的光标位置:', position)
  
  // 重新加载文件
  await loadFile(currentFile.value)
  console.log('[CodeEditor] 文件加载完成')
  
  // 恢复光标位置
  if (position && editor.value) {
    editor.value.setPosition(position)
    console.log('[CodeEditor] 恢复光标位置')
  }
  
  ElMessage.success('文件已刷新')
}

// 暴露方法
defineExpose({
  insertCode,
  getContent,
  setContent,
  getSelectedText,
  loadFile,
  saveFile,
  reloadFile,
  triggerFind,
  triggerReplace,
  goToLine
})

// 触发查找
function triggerFind() {
  if (editor.value) {
    editor.value.getAction('actions.find').run()
  }
}

// 触发替换
function triggerReplace() {
  if (editor.value) {
    editor.value.getAction('editor.action.startFindReplaceAction').run()
  }
}

// 跳转到指定行
function goToLine(line, column = 1) {
  if (editor.value) {
    editor.value.revealLineInCenter(line)
    editor.value.setPosition({ lineNumber: line, column: column })
    editor.value.focus()
  }
}
</script>

<style scoped>
.code-editor {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: #1e1e1e;
}

.editor-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  background: #252526;
  border-bottom: 1px solid #333;
}

.file-info {
  display: flex;
  align-items: center;
  gap: 6px;
  color: #cccccc;
  font-size: 13px;
}

.file-path {
  font-weight: 500;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 400px;
}

.unsaved-indicator {
  color: #e2c08d;
  font-size: 18px;
}

.editor-container {
  flex: 1;
  overflow: hidden;
}

.loading-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(30, 30, 30, 0.8);
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  gap: 12px;
  color: #cccccc;
  font-size: 14px;
}

.loading-overlay .el-icon {
  font-size: 32px;
  color: #409eff;
}
</style>
