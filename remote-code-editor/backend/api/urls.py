"""
API URL路由配置
"""
from django.urls import path
from . import views

urlpatterns = [
    # 健康检查
    path('health/', views.health_check, name='health'),
    
    # 文件操作API
    path('files/tree/', views.get_file_tree, name='file_tree'),
    path('files/read/', views.read_file, name='file_read'),
    path('files/save/', views.save_file, name='file_save'),
    path('files/create/', views.create_file_or_dir, name='file_create'),
    path('files/rename/', views.rename_file_or_dir, name='file_rename'),
    path('files/delete/', views.delete_file_or_dir, name='file_delete'),
    path('files/exists/', views.check_exists, name='file_exists'),
    
    # 工作区API
    path('workspace/get/', views.get_workspace, name='workspace_get'),
    path('workspace/set/', views.set_workspace, name='workspace_set'),
    path('workspace/list/', views.list_workspaces, name='workspace_list'),
    path('workspace/delete/', views.delete_workspace, name='workspace_delete'),
    path('workspace/browse/', views.browse_directory, name='workspace_browse'),
    path('workspace/drives/', views.get_system_drives, name='workspace_drives'),
    path('workspace/files/', views.get_workspace_files, name='workspace_files'),
    
    # AI功能API
    path('ai/health/', views.ai_health_check, name='ai_health'),
    path('ai/tab/health/', views.ai_tab_health_check, name='ai_tab_health'),
    path('ai/complete/', views.ai_code_complete, name='ai_complete'),
    
    # Git功能API
    path('git/status/', views.git_status, name='git_status'),
    path('git/check-config/', views.git_check_config, name='git_check_config'),
    path('git/list-repos/', views.git_list_repos, name='git_list_repos'),
    path('git/list-github-repos/', views.git_list_github_repos, name='git_list_github_repos'),
    path('git/clone/', views.git_clone, name='git_clone'),
    path('git/commit/', views.git_commit, name='git_commit'),
    path('git/push/', views.git_push, name='git_push'),
    path('git/pull/', views.git_pull, name='git_pull'),
    path('git/switch-branch/', views.git_switch_branch, name='git_switch_branch'),
    path('git/history/', views.git_history, name='git_history'),
    
    # 搜索功能API
    path('search/content/', views.search_content, name='search_content'),
    
    # AI对话历史管理API
    path('conversations/list/', views.list_conversations, name='conversations_list'),
    path('conversations/create/', views.create_conversation, name='conversations_create'),
    path('conversations/get/', views.get_conversation, name='conversations_get'),
    path('conversations/update/', views.update_conversation, name='conversations_update'),
    path('conversations/delete/', views.delete_conversation, name='conversations_delete'),
    path('conversations/message/', views.add_message, name='conversations_message'),
    path('conversations/clear/', views.clear_conversation, name='conversations_clear'),

    # 前端日志API
    path('frontend-log/', views.frontend_log, name='frontend_log'),
]
