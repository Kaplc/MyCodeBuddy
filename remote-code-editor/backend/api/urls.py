"""
API URL路由配置
"""
from django.urls import path
from . import views
from workflow import views as workflow_views
from collaboration import views as collab_views

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
    path('files/copy/', views.copy_file_or_dir, name='file_copy'),
    
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

    # Workflow API
    path('workflow/list/', views.list_workflows, name='workflow_list'),
    path('workflow/create/', views.create_workflow, name='workflow_create'),
    path('workflow/get/', views.get_workflow, name='workflow_get'),
    path('workflow/update/', views.update_workflow, name='workflow_update'),
    path('workflow/delete/', views.delete_workflow, name='workflow_delete'),
    path('workflow/run/', views.run_workflow, name='workflow_run'),
    path('workflow/tools/', views.list_workflow_tools, name='workflow_tools'),
    path('workflow/models/', views.list_models, name='workflow_models'),  # 来自 workflow.views
    path('workflow/reload-config/', views.reload_ai_config, name='workflow_reload_config'),
    path('workflow/debug-log/', workflow_views.debug_log, name='workflow_debug_log'),
    # 工作流执行状态API
    path('workflow/execution-state/', workflow_views.get_execution_state, name='workflow_execution_state'),
    path('workflow/execution-state/clear/', workflow_views.clear_execution_state_api, name='workflow_execution_state_clear'),
    # 工作流状态API
    path('workflow/last/', workflow_views.get_last_workflow, name='workflow_last_get'),
    path('workflow/last/set/', workflow_views.set_last_workflow, name='workflow_last_set'),
    path('workflow/last/clear/', workflow_views.clear_last_workflow, name='workflow_last_clear'),

    # 交互式需求文档生成 API
    path('collaboration/interactive/start/', collab_views.interactive_start_api, name='collaboration_interactive_start'),
    path('collaboration/interactive/question/', collab_views.interactive_question_api, name='collaboration_interactive_question'),
    path('collaboration/interactive/answer/', collab_views.interactive_answer_api, name='collaboration_interactive_answer'),
    path('collaboration/interactive/generate/', collab_views.interactive_generate_api, name='collaboration_interactive_generate'),
    path('collaboration/interactive/state/', collab_views.interactive_state_api, name='collaboration_interactive_state'),
    path('collaboration/interactive/reset/', collab_views.interactive_reset_api, name='collaboration_interactive_reset'),
    path('collaboration/interactive/skip/', collab_views.interactive_skip_api, name='collaboration_interactive_skip'),
    path('collaboration/interactive/messages/', collab_views.interactive_messages_api, name='collaboration_interactive_messages'),
    path('collaboration/interactive/explain/', collab_views.interactive_explain_api, name='collaboration_interactive_explain'),

    # 历史方案管理 API
    path('collaboration/sessions/list/', collab_views.list_sessions_api, name='collaboration_sessions_list'),
    path('collaboration/sessions/get/', collab_views.get_session_detail_api, name='collaboration_sessions_get'),
    path('collaboration/sessions/delete/', collab_views.delete_session_api, name='collaboration_sessions_delete'),




    # 前端日志API
    path('frontend-log/', views.frontend_log, name='frontend_log'),

    # Agent API（代码验证架构）
    path('agent/run/', views.run_agent, name='agent_run'),
    path('agent/verify/', views.verify_code_api, name='agent_verify'),
    path('agent/generate-tests/', views.generate_tests, name='agent_generate_tests'),
    path('agent/index/', views.index_workspace, name='agent_index'),
    path('agent/search/', views.search_symbol, name='agent_search'),
    path('agent/references/', views.get_references, name='agent_references'),
    path('agent/call-graph/', views.get_call_graph, name='agent_call_graph'),
    path('agent/outline/', views.get_file_outline, name='agent_outline'),
]
