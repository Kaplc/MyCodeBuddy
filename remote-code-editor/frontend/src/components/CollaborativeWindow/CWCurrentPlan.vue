<template>
  <div class="interactive-planner">
    <!-- 顶部：步骤进度条 -->
    <div class="progress-bar">
      <div
        v-for="(step, idx) in steps"
        :key="step.key"
        class="step-item"
        :class="{
          'is-active': currentStep === step.key,
          'is-done': stepOrder.indexOf(currentStep) > stepOrder.indexOf(step.key)
        }"
      >
        <div class="step-icon">
          <el-icon v-if="stepOrder.indexOf(currentStep) > stepOrder.indexOf(step.key)"><Check /></el-icon>
          <span v-else>{{ idx + 1 }}</span>
        </div>
        <span class="step-name">{{ step.label }}</span>
        <div v-if="idx < steps.length - 1" class="step-line"></div>
      </div>
    </div>

    <!-- 主内容区 -->
    <div class="main-content">
      <!-- 步骤1：输入目标 -->
      <div v-if="currentStep === 'goal'" class="step-content">
        <div class="goal-input-section">
          <h2 class="section-title">🚀 交互式开发</h2>
          <p class="section-desc">描述你想要实现的功能或解决的问题，开启智能开发之旅</p>
          <el-input
            v-model="goalInput"
            type="textarea"
            :rows="5"
            placeholder="例如：帮我优化 backend/api/urls.py 的代码结构，使其更易维护和扩展"
            maxlength="500"
            show-word-limit
          />
          <div class="action-row">
            <el-button type="primary" size="large" :loading="startLoading" @click="handleStartSession">
              开始问答
            </el-button>
          </div>
        </div>
      </div>

      <!-- 步骤2：回答问题 -->
      <div v-else-if="currentStep === 'question'" class="qa-layout">
          <!-- 左侧：当前问题 -->
          <div class="current-question-area">
            <div class="question-header">
              <div class="question-section-tag">{{ currentQuestion?.section_name }}</div>
              <div class="question-progress">{{ currentIndex + 1 }} / {{ totalQuestions }}</div>
            </div>

            <div class="question-text">{{ currentQuestion?.question }}</div>

            <div v-if="currentQuestion?.hint" class="question-hint">
              <el-icon><InfoFilled /></el-icon>
              {{ currentQuestion.hint }}
            </div>

            <!-- AI 解释区域 -->
            <div class="explain-section">
              <div class="explain-input-row">
                <el-input
                  v-model="explainInput"
                  type="text"
                  placeholder="有疑问？向AI提问解释此题"
                  @keyup.enter="handleExplain"
                >
                  <template #append>
                    <el-button @click="handleExplain" :disabled="explainLoading || !explainInput.trim()">
                      {{ explainLoading ? '思考中' : '提问' }}
                    </el-button>
                  </template>
                </el-input>
              </div>
              <div v-if="explainResult" class="explain-result">
                <div class="explain-result-text">{{ explainResult }}</div>
              </div>
            </div>

            <!-- 选项列表 -->
            <div class="options-list" :class="{ 'is-disabled': submitLoading }">
              <div
                v-for="option in currentQuestion?.options || []"
                :key="option.id"
                class="option-item"
                :class="{
                  'is-selected': selectedOptionIds.includes(option.id),
                  'is-multi-select': currentQuestion?.allow_multi_select
                }"
                @click="!submitLoading && handleSelectOption(option.id)"
              >
                <div class="option-checkbox">
                  <el-icon v-if="selectedOptionIds.includes(option.id)"><Check /></el-icon>
                </div>
                <span class="option-text">{{ option.text }}</span>
              </div>
            </div>

            <!-- 按钮布局保持在底部 -->
            <div class="answer-submit-section">
              <!-- 自定义输入 -->
              <div class="custom-input-section">
                <el-input
                  v-model="customInput"
                  type="text"
                  placeholder="输入自定义选项（可选）"
                  maxlength="30"
                  show-word-limit
                >
                  <template #append>
                    <el-button @click="addCustomAsOption" :disabled="submitLoading || !customInput.trim()">添加</el-button>
                  </template>
                </el-input>
              </div>

              <div class="action-row">
                <el-button @click="handleResetSession" :disabled="submitLoading">重新开始</el-button>
                <el-button @click="handleSkipQuestion" :disabled="submitLoading">跳过此题</el-button>
                <el-button
                  type="primary"
                  :disabled="submitLoading || selectedOptionIds.length === 0"
                  :loading="submitLoading"
                  @click="handleSubmitAnswer"
                >
                  确认答案
                </el-button>
              </div>
            </div>
          </div>

          <!-- 右侧：回答汇总 -->
          <div class="answers-summary-area">
            <div class="summary-title">已回答</div>
            <div v-if="Object.keys(answersSummary).length === 0" class="summary-empty">
              暂无回答
            </div>
            <div v-else class="summary-list">
              <div
                v-for="(sectionAnswers, sectionId) in answersSummary"
                :key="sectionId"
                class="summary-section"
              >
                <div class="summary-section-name">{{ sectionAnswers.section_name }}</div>
                <div
                  v-for="(answer, idx) in [...sectionAnswers.answers].reverse()"
                  :key="idx"
                  class="summary-item"
                >
                  <span class="summary-question">{{ answer.question }}</span>
                  <div class="summary-selected">
                    <el-tag
                      v-for="opt in answer.selected_options"
                      :key="opt.id"
                      size="small"
                      type="info"
                    >
                      {{ opt.text }}
                    </el-tag>
                  </div>
                </div>
              </div>
            </div>
          </div>
      </div>

        <!-- 步骤3：生成文档 -->
      <div v-else-if="currentStep === 'generate'" class="step-content">
        <div class="generate-section">
          <div class="generate-success">
            <el-icon class="success-icon"><CircleCheck /></el-icon>
            <h2>所有问题已回答完毕</h2>
            <p>已收集到完整的需求信息，点击下方按钮生成需求文档</p>
          </div>

          <div class="answers-review">
            <div class="review-title">需求概要</div>
            <div class="review-goal">{{ sessionGoal }}</div>
            <div class="review-summary">
              <div
                v-for="(sectionAnswers, sectionId) in answersSummary"
                :key="sectionId"
                class="review-section"
              >
                <div class="review-section-name">{{ sectionAnswers.section_name }}</div>
                <div class="review-answers">
                  <el-tag
                    v-for="(opt, idx) in sectionAnswers.flat_options"
                    :key="idx"
                    size="small"
                  >
                    {{ opt.text }}
                  </el-tag>
                </div>
              </div>
            </div>
          </div>

          <div class="action-row">
            <el-button @click="handleBackToQuestion">返回修改</el-button>
            <el-button type="success" size="large" :loading="generateLoading" @click="handleGenerateDoc">
              生成需求文档
            </el-button>
          </div>
        </div>
      </div>

      <!-- 步骤4：文档结果 -->
      <div v-else-if="currentStep === 'result'" class="step-content">
        <div class="result-section">
          <div class="result-header">
            <h2 class="result-title">{{ requirementDoc?.doc_title || '需求文档' }}</h2>
            <el-tag type="success">已完成</el-tag>
          </div>

          <div class="doc-sections">
            <div
              v-for="section in requirementDoc?.sections || []"
              :key="section.section_id"
              class="doc-section-card"
            >
              <div class="doc-section-header">
                <span class="doc-section-num">{{ section.section_id }}</span>
                <span class="doc-section-name">{{ section.section_name }}</span>
              </div>
              <div class="doc-section-prompt">{{ section.section_prompt }}</div>
            </div>
          </div>

          <div class="action-row">
            <el-button @click="handleResetSession">新建需求</el-button>
            <el-button type="primary" @click="handleCopyDoc">复制文档内容</el-button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { Check, InfoFilled, CircleCheck } from '@element-plus/icons-vue'
import axios from 'axios'

const props = defineProps({
  initialSessionId: {
    type: String,
    default: null
  }
})

const emit = defineEmits(['session-created', 'session-updated'])

// 步骤定义
const steps = [
  { key: 'goal', label: '输入目标' },
  { key: 'question', label: '回答问题' },
  { key: 'generate', label: '生成文档' },
  { key: 'result', label: '文档结果' },
]
const stepOrder = ['goal', 'question', 'generate', 'result']

// 状态
const currentStep = ref('goal')
const goalInput = ref('')
const sessionId = ref(null)
const sessionGoal = ref('')

// 问答状态
const currentQuestion = ref(null)
const currentIndex = ref(0)
const totalQuestions = ref(0)
const selectedOptionIds = ref([])
const customInput = ref('')
const answersSummary = reactive({})

// 文档状态
const requirementDoc = ref(null)

// 加载状态
const startLoading = ref(false)
const generateLoading = ref(false)
const submitLoading = ref(false)
const explainLoading = ref(false)
const historyLoading = ref(false)
const explainInput = ref('')
const explainResult = ref('')

// 监听 initialSessionId 变化
watch(() => props.initialSessionId, async (newId) => {
  if (newId && newId !== sessionId.value) {
    await loadSession(newId)
  }
})

// API 调用
async function callAPI(url, data = null, method = 'POST') {
  try {
    const response = method === 'GET'
      ? await axios.get(url, { params: data })
      : await axios({ url, method, data })
    return response.data
  } catch (error) {
    console.error('API 调用失败:', error)
    const errorMsg = error.response?.data?.error || error.message || '请求失败'
    ElMessage.error(errorMsg)
    throw error
  }
}

// 开始会话
async function handleStartSession() {
  if (!goalInput.value.trim()) {
    ElMessage.warning('请输入需求目标')
    return
  }

  startLoading.value = true
  try {
    const result = await callAPI('/api/collaboration/interactive/start/', {
      goal: goalInput.value.trim()
    })

    sessionId.value = result.session_id
    sessionGoal.value = result.goal
    totalQuestions.value = result.total_questions
    currentQuestion.value = result.current_question
    currentIndex.value = 0
    selectedOptionIds.value = []
    customInput.value = ''

    // 清空之前的汇总
    Object.keys(answersSummary).forEach(key => delete answersSummary[key])

    currentStep.value = 'question'
    ElMessage.success('会话已创建，开始问答')

    // 保存到 localStorage
    localStorage.setItem('last_collab_session_id', sessionId.value)

    // 通知父组件
    emit('session-created', sessionId.value)
  } catch (error) {
    // 错误已在 callAPI 中处理
  } finally {
    startLoading.value = false
  }
}

// 加载已有会话
async function loadSession(id) {
  if (!id) return

  try {
    const result = await callAPI('/api/collaboration/sessions/get/', { session_id: id }, 'GET')
    if (!result.session) {
      ElMessage.error('会话不存在')
      return
    }

    const session = result.session
    sessionId.value = id
    sessionGoal.value = session.goal || ''
    goalInput.value = session.goal || ''

    const metadata = session.metadata || {}

    // 根据会话状态恢复界面
    if (session.phase === 'doc_generated' && metadata.requirement_doc) {
      // 已生成文档
      requirementDoc.value = metadata.requirement_doc
      currentStep.value = 'result'
    } else {
      // 获取消息历史来恢复答案汇总
      const messagesResult = await callAPI('/api/collaboration/interactive/messages/', { session_id: id }, 'GET')
      if (messagesResult.messages && messagesResult.messages.length > 0) {
        // 清空并重建答案汇总
        Object.keys(answersSummary).forEach(key => delete answersSummary[key])
        for (const msg of messagesResult.messages) {
          if (msg.type === 'answer') {
            // 从 answer 消息中恢复
            const sectionId = msg.question_id?.split('_')[0] || '1'
            if (!answersSummary[sectionId]) {
              answersSummary[sectionId] = { section_name: '', answers: [] }
            }
            answersSummary[sectionId].answers.push({
              question: msg.question_text || msg.question_id,
              question_id: msg.question_id,
              selected_options: msg.selected_options || []
            })
          }
        }
        // 设置当前索引
        currentIndex.value = metadata.current_question_index || 0
        currentStep.value = 'question'
      }

      // 获取当前问题
      const questionResult = await callAPI('/api/collaboration/interactive/question/', { session_id: id }, 'GET')
      if (questionResult.completed) {
        currentStep.value = 'generate'
      } else {
        currentQuestion.value = questionResult.current_question
        if (!messagesResult.messages || messagesResult.messages.length === 0) {
          currentIndex.value = questionResult.current_index || 0
          currentStep.value = 'question'
        }
      }
    }

    ElMessage.success('会话已恢复')
  } catch (error) {
    console.error('加载会话失败:', error)
    const errorStatus = error.response?.status
    if (errorStatus === 404) {
      ElMessage.warning('会话不存在或已过期，请开始新的会话')
    } else {
      ElMessage.error('加载会话失败')
    }
  }
}

// 向 AI 解释问题
async function handleExplain() {
  if (!explainInput.value.trim() || !currentQuestion.value) return

  explainLoading.value = true
  explainResult.value = ''
  try {
    const result = await callAPI('/api/collaboration/interactive/explain/', {
      session_id: sessionId.value,
      question_text: currentQuestion.value.question,
      user_question: explainInput.value.trim()
    })
    if (result.success) {
      explainResult.value = result.explanation
    } else {
      ElMessage.error(result.error || '解释失败')
    }
  } catch (error) {
    console.error('解释失败:', error)
    ElMessage.error('解释失败')
  } finally {
    explainLoading.value = false
  }
}

// 选择选项
function handleSelectOption(optionId) {
  if (currentQuestion.value?.allow_multi_select) {
    // 多选
    const idx = selectedOptionIds.value.indexOf(optionId)
    if (idx >= 0) {
      selectedOptionIds.value.splice(idx, 1)
    } else {
      selectedOptionIds.value.push(optionId)
    }
  } else {
    // 单选
    selectedOptionIds.value = [optionId]
  }
}

// 添加自定义输入为选项
function addCustomAsOption() {
  if (!customInput.value.trim()) return
  const customId = `_custom_${Date.now()}`
  // 先添加到选项列表显示
  if (currentQuestion.value) {
    currentQuestion.value.options = currentQuestion.value.options || []
    currentQuestion.value.options.push({
      id: customId,
      text: customInput.value.trim()
    })
  }
  selectedOptionIds.value.push(customId)
  customInput.value = ''
}

// 提交答案
async function handleSubmitAnswer() {
  if (selectedOptionIds.value.length === 0 && !customInput.value.trim()) {
    ElMessage.warning('请至少选择一个选项或输入自定义内容')
    return
  }

  submitLoading.value = true
  try {
    const result = await callAPI('/api/collaboration/interactive/answer/', {
      session_id: sessionId.value,
      selected_ids: selectedOptionIds.value,
      custom_input: customInput.value.trim() || null
    })

    // 更新汇总
    updateAnswersSummary(currentQuestion.value, selectedOptionIds.value)

    // 检查是否是 AI 直接生成的文档（AI 认为信息足够）
    if (result.current_question?.is_final_doc) {
      requirementDoc.value = result.current_question.final_doc_content
      currentStep.value = 'result'
      ElMessage.success('需求文档已生成！')
      emit('session-updated')
      return
    }

    if (result.completed) {
      // 所有问题回答完毕
      currentStep.value = 'generate'
      ElMessage.success('所有问题已回答完毕！')
      emit('session-updated')
    } else {
      // 下一题
      currentQuestion.value = result.current_question
      currentIndex.value = result.current_index
      selectedOptionIds.value = []
      customInput.value = ''
    }
  } catch (error) {
    // 错误已在 callAPI 中处理
  } finally {
    submitLoading.value = false
  }
}

// 更新答案汇总
function updateAnswersSummary(question, selectedIds) {
  const sectionId = question.section_id
  const optionsMap = {}
  question.options?.forEach(opt => {
    optionsMap[opt.id] = opt.text
  })

  if (!answersSummary[sectionId]) {
    answersSummary[sectionId] = {
      section_name: question.section_name,
      answers: []
    }
  }

  answersSummary[sectionId].answers.push({
    question: question.question,
    question_id: question.question_id,
    selected_options: selectedIds.map(id => ({
      id,
      text: optionsMap[id] || id
    }))
  })
}

// 跳过此题
async function handleSkipQuestion() {
  submitLoading.value = true
  try {
    const result = await callAPI('/api/collaboration/interactive/skip/', {
      session_id: sessionId.value
    })

    if (result.completed) {
      currentStep.value = 'generate'
      ElMessage.success('所有问题已回答完毕！')
      emit('session-updated')
    } else {
      currentQuestion.value = result.current_question
      currentIndex.value = result.current_index
      selectedOptionIds.value = []
      customInput.value = ''
    }
  } catch (error) {
    // 错误已在 callAPI 中处理
  } finally {
    submitLoading.value = false
  }
}

// 重置会话
async function handleResetSession() {
  if (!sessionId.value) {
    currentStep.value = 'goal'
    goalInput.value = ''
    return
  }

  try {
    const result = await callAPI('/api/collaboration/interactive/reset/', {
      session_id: sessionId.value
    })

    sessionGoal.value = result.goal || sessionGoal.value
    totalQuestions.value = result.total_questions
    currentQuestion.value = result.current_question
    currentIndex.value = 0
    selectedOptionIds.value = []
    customInput.value = ''

    // 清空汇总
    Object.keys(answersSummary).forEach(key => delete answersSummary[key])

    currentStep.value = 'question'
    ElMessage.success('会话已重置')
    emit('session-updated')
  } catch (error) {
    // 重置失败则直接回到目标输入
    currentStep.value = 'goal'
    goalInput.value = ''
    sessionId.value = null
  }
}

// 返回修改
function handleBackToQuestion() {
  currentStep.value = 'question'
}

// 生成文档
async function handleGenerateDoc() {
  generateLoading.value = true
  try {
    const result = await callAPI('/api/collaboration/interactive/generate/', {
      session_id: sessionId.value
    })

    requirementDoc.value = result.requirement_doc
    currentStep.value = 'result'
    ElMessage.success('需求文档已生成！')
    emit('session-updated')
  } catch (error) {
    // 错误已在 callAPI 中处理
  } finally {
    generateLoading.value = false
  }
}

// 复制文档
function handleCopyDoc() {
  if (!requirementDoc.value) return

  const content = generateDocText()
  navigator.clipboard.writeText(content).then(() => {
    ElMessage.success('文档内容已复制到剪贴板')
  }).catch(() => {
    ElMessage.error('复制失败')
  })
}

// 生成文档文本
function generateDocText() {
  if (!requirementDoc.value) return ''

  let text = `# ${requirementDoc.value.doc_title}\n\n`
  text += `**目标**: ${requirementDoc.value.goal}\n\n`

  requirementDoc.value.sections?.forEach(section => {
    text += `## ${section.section_id}. ${section.section_name}\n\n`
    text += `${section.section_prompt}\n\n`
  })

  return text
}

// 恢复会话（如果刷新页面）
onMounted(async () => {
  // TODO: 可以从 localStorage 读取上次 session_id，调用 /interactive/state/ 恢复
})

// 重置到目标输入阶段（用于新建方案）
function resetToGoal() {
  currentStep.value = 'goal'
  goalInput.value = ''
  sessionId.value = null
  sessionGoal.value = ''
  requirementDoc.value = null
  // 清空汇总
  Object.keys(answersSummary).forEach(key => delete answersSummary[key])
}

// 暴露方法给父组件调用
defineExpose({
  loadSession,
  resetToGoal
})
</script>

<style scoped>
.interactive-planner {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: #1e1e1e;
  color: #ccc;
}

/* 进度条 */
.progress-bar {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px 40px;
  border-bottom: 1px solid #333;
  flex-shrink: 0;
}

.step-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.step-icon {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  border: 2px solid #555;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  color: #888;
  background: #252526;
}

.step-item.is-active .step-icon {
  border-color: #409eff;
  background: #409eff;
  color: #fff;
}

.step-item.is-done .step-icon {
  border-color: #67c23a;
  background: #67c23a;
  color: #fff;
}

.step-name {
  font-size: 13px;
  color: #888;
}

.step-item.is-active .step-name {
  color: #409eff;
  font-weight: 500;
}

.step-item.is-done .step-name {
  color: #67c23a;
}

.step-line {
  width: 60px;
  height: 2px;
  background: #333;
  margin: 0 12px;
}

.step-item.is-done + .step-item .step-line,
.step-item.is-done .step-line {
  background: #67c23a;
}

/* 主内容 */
.main-content {
  flex: 1;
  overflow: hidden;
  padding: 24px;
  display: flex;
  flex-direction: column;
}

.step-content {
  max-width: 1200px;
  margin: 0 auto;
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

/* 目标输入 */
.goal-input-section {
  max-width: 600px;
  margin: 40px auto;
  text-align: center;
}

.section-title {
  font-size: 20px;
  font-weight: 600;
  margin-bottom: 8px;
  color: #fff;
}

.section-desc {
  font-size: 14px;
  color: #888;
  margin-bottom: 20px;
}

.goal-input-section .el-textarea {
  margin-bottom: 16px;
}

.goal-input-section :deep(.el-textarea__inner) {
  background: #252526;
  border: 1px solid #333;
  border-radius: 8px;
  font-size: 14px;
  padding: 12px 16px;
  color: #ccc;
}

.goal-input-section :deep(.el-textarea__inner:focus) {
  border-color: #409eff;
}

.action-row {
  display: flex;
  justify-content: center;
  gap: 12px;
  margin-top: 20px;
}

/* 问答布局 */
.qa-layout {
  display: flex;
  gap: 24px;
  height: 100%;
}

.current-question-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: #252526;
  border-radius: 12px;
  padding: 20px;
  overflow: hidden;
}

.question-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  flex-shrink: 0;
}

.question-section-tag {
  padding: 4px 12px;
  background: rgba(64, 158, 255, 0.2);
  border: 1px solid rgba(64, 158, 255, 0.3);
  border-radius: 16px;
  font-size: 12px;
  color: #409eff;
}

.question-progress {
  font-size: 13px;
  color: #888;
}

.question-text {
  font-size: 16px;
  font-weight: 500;
  color: #fff;
  margin-bottom: 12px;
  line-height: 1.6;
  flex-shrink: 0;
}

.question-hint {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: #888;
  margin-bottom: 16px;
  padding: 8px 12px;
  background: rgba(255, 255, 255, 0.03);
  border-radius: 6px;
  flex-shrink: 0;
}

/* AI 解释区域 */
.explain-section {
  margin-bottom: 16px;
  flex-shrink: 0;
}

.explain-input-row {
  margin-bottom: 8px;
}

.explain-result {
  padding: 12px;
  background: rgba(64, 158, 255, 0.1);
  border-radius: 6px;
  border-left: 3px solid #409eff;
}

.explain-result-text {
  font-size: 13px;
  color: #e0e0e0;
  line-height: 1.6;
  white-space: pre-wrap;
}

/* 选项列表 */
.options-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
  overflow-y: auto;
  flex: 1;
  min-height: 0;
}

.options-list.is-disabled {
  opacity: 0.6;
  pointer-events: none;
}

/* 暗色滚动条 */
.options-list::-webkit-scrollbar {
  width: 6px;
}

.options-list::-webkit-scrollbar-track {
  background: #2a2a2a;
  border-radius: 3px;
}

.options-list::-webkit-scrollbar-thumb {
  background: #555;
  border-radius: 3px;
}

.options-list::-webkit-scrollbar-thumb:hover {
  background: #666;
}

/* 选项下面的布局：自定义输入 + 按钮 */
.answer-submit-section {
  flex-shrink: 0;
  padding-top: 12px;
  border-top: 1px solid #333;
}

.option-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 16px;
  background: #1e1e1e;
  border: 1.5px solid #333;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.option-item:hover {
  border-color: #409eff;
  background: rgba(64, 158, 255, 0.05);
}

.option-item.is-selected {
  border-color: #409eff;
  background: rgba(64, 158, 255, 0.1);
}

.option-checkbox {
  width: 20px;
  height: 20px;
  border: 2px solid #555;
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  transition: all 0.2s;
}

.option-item.is-multi-select .option-checkbox {
  border-radius: 50%;
}

.option-item.is-selected .option-checkbox {
  border-color: #409eff;
  background: #409eff;
  color: #fff;
}

.option-text {
  font-size: 14px;
  color: #ccc;
  line-height: 1.4;
}

.option-item.is-selected .option-text {
  color: #fff;
}

/* 自定义输入 */
.custom-input-section {
  margin-bottom: 16px;
}

.custom-input-section :deep(.el-input__inner) {
  background: #1e1e1e;
  border-color: #333;
  color: #ccc;
}

/* 回答汇总 */
.answers-summary-area {
  width: 320px;
  flex-shrink: 0;
  background: #252526;
  border-radius: 12px;
  padding: 16px;
  overflow-y: auto;
}

.summary-title {
  font-size: 14px;
  font-weight: 600;
  color: #888;
  margin-bottom: 16px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.summary-empty {
  color: #555;
  font-size: 13px;
  text-align: center;
  padding: 40px 0;
}

.summary-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.summary-section-name {
  font-size: 12px;
  font-weight: 600;
  color: #409eff;
  margin-bottom: 8px;
  padding-bottom: 4px;
  border-bottom: 1px solid #333;
}

.summary-item {
  margin-bottom: 10px;
}

.summary-question {
  display: block;
  font-size: 11px;
  color: #777;
  margin-bottom: 4px;
}

.summary-selected {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.summary-selected .el-tag {
  background: #333;
  border: none;
  color: #ccc;
}

/* 生成文档 */
.generate-section {
  max-width: 700px;
  margin: 0 auto;
  text-align: center;
}

.generate-success {
  padding: 40px 0;
}

.success-icon {
  font-size: 60px;
  color: #67c23a;
  margin-bottom: 16px;
}

.generate-success h2 {
  font-size: 20px;
  font-weight: 600;
  color: #fff;
  margin-bottom: 8px;
}

.generate-success p {
  color: #888;
  font-size: 14px;
}

.answers-review {
  background: #252526;
  border-radius: 12px;
  padding: 20px;
  text-align: left;
  margin: 20px 0;
}

.review-title {
  font-size: 14px;
  font-weight: 600;
  color: #888;
  margin-bottom: 12px;
}

.review-goal {
  font-size: 15px;
  color: #fff;
  padding: 12px;
  background: #1e1e1e;
  border-radius: 6px;
  margin-bottom: 16px;
}

.review-summary {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.review-section {
  padding: 10px 0;
  border-bottom: 1px solid #333;
}

.review-section:last-child {
  border-bottom: none;
}

.review-section-name {
  font-size: 12px;
  font-weight: 600;
  color: #409eff;
  margin-bottom: 8px;
}

.review-answers {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.review-answers .el-tag {
  background: rgba(64, 158, 255, 0.2);
  border: none;
  color: #409eff;
}

/* 结果 */
.result-section {
  max-width: 800px;
  margin: 0 auto;
}

.result-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 16px;
  border-bottom: 1px solid #333;
}

.result-title {
  font-size: 20px;
  font-weight: 600;
  color: #fff;
}

.doc-sections {
  display: flex;
  flex-direction: column;
  gap: 16px;
  margin-bottom: 24px;
}

.doc-section-card {
  background: #252526;
  border-radius: 8px;
  padding: 16px;
  border-left: 3px solid #409eff;
}

.doc-section-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 10px;
}

.doc-section-num {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: #409eff;
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 600;
}

.doc-section-name {
  font-size: 15px;
  font-weight: 600;
  color: #fff;
}

.doc-section-prompt {
  font-size: 13px;
  color: #aaa;
  line-height: 1.6;
  white-space: pre-wrap;
}
</style>
