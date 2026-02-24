"""
Git操作视图
"""
import asyncio
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings

from services.git_service import GitService


# 初始化Git服务
git_service = GitService(settings.WORKSPACE_PATH)


def sync_to_async(coro):
    """将协程转换为同步调用的辅助函数"""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    if loop.is_running():
        new_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(new_loop)
        try:
            return new_loop.run_until_complete(coro)
        finally:
            new_loop.close()
    else:
        return loop.run_until_complete(coro)


@csrf_exempt
@require_http_methods(["GET"])
def git_status(request):
    """获取Git状态"""
    try:
        result = sync_to_async(git_service.get_status())
        return JsonResponse(result)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def git_check_config(request):
    """检查Git配置状态"""
    try:
        result = git_service.check_git_config()
        return JsonResponse(result)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def git_list_repos(request):
    """列出Git仓库"""
    try:
        search_path = request.GET.get('path')
        result = sync_to_async(git_service.list_git_repos(search_path))
        return JsonResponse(result)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def git_list_github_repos(request):
    """列出GitHub仓库（使用服务器配置的Token）"""
    try:
        repo_type = request.GET.get('type', 'all')
        result = sync_to_async(git_service.list_github_repos(None, repo_type))
        return JsonResponse(result)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def git_clone(request):
    """克隆远程仓库（使用系统Git凭据），克隆成功后自动切换工作区"""
    global git_service
    import json
    from pathlib import Path
    from django.conf import settings
    from services.file_service import FileService
    from services.git_service import GitService
    
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': '无效的JSON数据'}, status=400)
    
    repo_url = data.get('repo_url', '')
    
    if not repo_url:
        return JsonResponse({'error': '缺少仓库URL'}, status=400)
    
    try:
        result = sync_to_async(git_service.clone(repo_url))
        
        # 如果克隆成功，自动切换工作区到新仓库
        if result.get('success') and result.get('path'):
            workspace_path = result['path']
            
            # 更新settings中的WORKSPACE_PATH
            settings.WORKSPACE_PATH = workspace_path
            
            # 更新file_service和git_service的工作区
            from . import files
            files.file_service = FileService(workspace_path)
            git_service = GitService(workspace_path)
            
            # 保存到配置文件
            config_file = Path(settings.BASE_DIR) / 'workspace_config.json'
            config = {}
            if config_file.exists():
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
            
            config['workspace_path'] = workspace_path
            
            # 更新工作区列表
            workspaces = config.get('workspaces', [])
            normalized_path = workspace_path.replace('\\', '/').lower()
            
            unique_workspaces = []
            normalized_list = []
            for ws in workspaces:
                norm_ws = ws.replace('\\', '/').lower()
                if norm_ws not in normalized_list:
                    normalized_list.append(norm_ws)
                    unique_workspaces.append(ws)
            
            if normalized_path not in normalized_list:
                unique_workspaces.append(workspace_path)
            
            config['workspaces'] = unique_workspaces
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            
            # 在返回结果中添加工作区切换信息
            result['workspace_changed'] = True
            result['workspace'] = workspace_path
        
        return JsonResponse(result)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def git_commit(request):
    """提交更改"""
    import json
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': '无效的JSON数据'}, status=400)
    
    message = data.get('message', '')
    files = data.get('files')
    
    if not message:
        return JsonResponse({'error': '缺少提交信息'}, status=400)
    
    try:
        result = sync_to_async(git_service.commit(message, files))
        return JsonResponse(result)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def git_push(request):
    """推送到远程仓库"""
    import json
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': '无效的JSON数据'}, status=400)
    
    remote = data.get('remote', 'origin')
    branch = data.get('branch')
    
    try:
        result = sync_to_async(git_service.push(remote, branch))
        return JsonResponse(result)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def git_pull(request):
    """从远程仓库拉取"""
    import json
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': '无效的JSON数据'}, status=400)
    
    remote = data.get('remote', 'origin')
    branch = data.get('branch')
    
    try:
        result = sync_to_async(git_service.pull(remote, branch))
        return JsonResponse(result)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def git_switch_branch(request):
    """切换分支"""
    import json
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': '无效的JSON数据'}, status=400)
    
    branch = data.get('branch', '')
    
    if not branch:
        return JsonResponse({'error': '缺少分支名称'}, status=400)
    
    try:
        result = sync_to_async(git_service.switch_branch(branch))
        return JsonResponse(result)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def git_history(request):
    """获取提交历史"""
    try:
        limit = int(request.GET.get('limit', 20))
        result = sync_to_async(git_service.get_commit_history(limit))
        return JsonResponse(result)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
