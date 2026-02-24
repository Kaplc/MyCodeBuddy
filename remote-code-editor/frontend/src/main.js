import { createApp } from 'vue'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
import App from './App.vue'
import axios from 'axios'
import { API_CONFIG } from './config/api.js'

// Monaco Editor Worker 配置
import editorWorker from 'monaco-editor/esm/vs/editor/editor.worker?worker'
import jsonWorker from 'monaco-editor/esm/vs/language/json/json.worker?worker'
import cssWorker from 'monaco-editor/esm/vs/language/css/css.worker?worker'
import htmlWorker from 'monaco-editor/esm/vs/language/html/html.worker?worker'
import tsWorker from 'monaco-editor/esm/vs/language/typescript/ts.worker?worker'

self.MonacoEnvironment = {
  getWorker(_, label) {
    if (label === 'json') {
      return new jsonWorker()
    }
    if (label === 'css' || label === 'scss' || label === 'less') {
      return new cssWorker()
    }
    if (label === 'html' || label === 'handlebars' || label === 'razor') {
      return new htmlWorker()
    }
    if (label === 'typescript' || label === 'javascript') {
      return new tsWorker()
    }
    return new editorWorker()
  }
}

// 配置 axios
axios.defaults.baseURL = API_CONFIG.BASE_URL

// 配置 axios 拦截器，添加错误处理
axios.interceptors.response.use(
  response => response,
  error => {
    console.error('API 请求错误:', error)
    return Promise.reject(error)
  }
)

// 前端日志发送到后端
async function sendLogToBackend(level, message, extra = {}) {
  try {
    await axios.post('/api/frontend-log/', {
      level,
      message,
      timestamp: new Date().toISOString(),
      url: window.location.href,
      ...extra
    })
  } catch (e) {
    // 静默失败，避免循环错误
  }
}

// 全局错误处理器
window.onerror = function(message, source, lineno, colno, error) {
  console.error('[全局错误]', { message, source, lineno, colno, error })
  sendLogToBackend('error', message, { source, lineno, colno, stack: error?.stack })
  return false
}

// Promise 未捕获错误
window.addEventListener('unhandledrejection', function(event) {
  console.error('[Promise错误]', event.reason)
  sendLogToBackend('error', String(event.reason), { type: 'unhandledrejection' })
})

const app = createApp(App)

// Vue 组件错误处理
app.config.errorHandler = (err, instance, info) => {
  console.error('[Vue错误]', err, info)
  sendLogToBackend('error', String(err), { info, stack: err?.stack })
}

// Vue 警告处理（开发环境）
app.config.warnHandler = (msg, instance, trace) => {
  console.warn('[Vue警告]', msg, trace)
  sendLogToBackend('warn', msg, { trace })
}

// 注册Element Plus
app.use(ElementPlus)

// 注册所有图标
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

app.mount('#app')
