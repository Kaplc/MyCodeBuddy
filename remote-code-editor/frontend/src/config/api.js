// API 配置文件
export const API_CONFIG = {
  // 后端 API 基础地址
  BASE_URL: 'http://localhost:8000',
  
  // WebSocket 地址
  WS_URL: 'ws://localhost:8000',
  
  // API 路径
  API_PATHS: {
    // 工作区相关
    WORKSPACE_LIST: '/api/workspace/list/',
    SET_WORKSPACE: '/api/workspace/set/',
    BROWSE_DIRECTORY: '/api/workspace/browse/',
    
    // 文件相关
    READ_FILE: '/api/file/read/',
    WRITE_FILE: '/api/file/write/',
    DELETE_FILE: '/api/file/delete/',
    CREATE_FILE: '/api/file/create/',
    RENAME_FILE: '/api/file/rename/',
    
    // AI 相关
    AI_CHAT: '/api/ai/chat'
  }
}
