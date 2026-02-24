"""
API视图模块
"""
from .health import health_check, ai_health_check, ai_tab_health_check
from .files import get_file_tree, read_file, save_file, create_file_or_dir, rename_file_or_dir, delete_file_or_dir, check_exists, copy_file_or_dir
from .workspace import get_workspace, set_workspace, list_workspaces, delete_workspace, browse_directory, get_system_drives, get_workspace_files
from .git import git_status, git_check_config, git_list_repos, git_list_github_repos, git_clone, git_commit, git_push, git_pull, git_switch_branch, git_history
from .search import search_content
from .ai_chat import list_conversations, create_conversation, get_conversation, update_conversation, delete_conversation, add_message, clear_conversation, ai_code_complete
from .frontend_log import frontend_log

__all__ = [
    # 健康检查
    'health_check', 'ai_health_check', 'ai_tab_health_check',
    # 文件操作
    'get_file_tree', 'read_file', 'save_file', 'create_file_or_dir', 'rename_file_or_dir', 'delete_file_or_dir', 'check_exists', 'copy_file_or_dir',
    # 工作区
    'get_workspace', 'set_workspace', 'list_workspaces', 'delete_workspace', 'browse_directory', 'get_system_drives', 'get_workspace_files',
    # Git
    'git_status', 'git_check_config', 'git_list_repos', 'git_list_github_repos', 'git_clone', 'git_commit', 'git_push', 'git_pull', 'git_switch_branch', 'git_history',
    # 搜索
    'search_content',
    # AI对话
    'list_conversations', 'create_conversation', 'get_conversation', 'update_conversation', 'delete_conversation', 'add_message', 'clear_conversation', 'ai_code_complete',
    # 前端日志
    'frontend_log',
]
