"""
Git操作视图
"""
import asyncio
import json
from pathlib import Path
from typing import Any, TypeVar, Union, Dict, List, Coroutine as CoroutineTyping

from django.conf import settings
from django.http import JsonResponse, HttpRequest
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from services.file_service import FileService
from services.git_service import GitService

# 泛型类型变量，用于保持协程返回类型
T = TypeVar('T')

# 初始化Git服务
git_service = GitService(settings.WORKSPACE_PATH)


def sync_to_async(coro: CoroutineTyping[Any, Any, T]) -> T:
    """将协程转换为同步调用的辅助函数
    
    Args:
        coro: 要执行的协程对象
        
    Returns:
        协程的返回值
    """
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
def git_status(request: HttpRequest) -> JsonResponse:
    """获取Git状态"""
    try:
        result: Dict[str, Any] = sync_to_async(git_service.get_status())
        return JsonResponse(result)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def git_check_config(request: HttpRequest) -> JsonResponse:
    """检查Git配置状态"""
    try:
        result: Dict[str, Any] = git_service.check_git_config()
        return JsonResponse(result)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def git_list_repos(request: HttpRequest) -> JsonResponse:
    """列出Git仓库"""
    try:
        search_path_val = request.GET.get('path')
        search_path: Union[str, None] = str(search_path_val) if search_path_val is not None else None
        result: Dict[str, Any] = sync_to_async(git_service.list_git_repos(search_path))
        return JsonResponse(result)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def git_list_github_repos(request: HttpRequest) -> JsonResponse:
    """列出GitHub仓库（使用服务器配置的Token）"""
    try:
        repo_type_val = request.GET.get('type', 'all')
        repo_type: str = str(repo_type_val) if repo_type_val else 'all'
        result: Dict[str, Any] = sync_to_async(git_service.list_github_repos(None, repo_type))
        return JsonResponse(result)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def git_clone(request: HttpRequest) -> JsonResponse:
    """克隆远程仓库（使用系统Git凭据），克隆成功后自动切换工作区"""
    global git_service
    
    try:
        data: Dict[str, Any] = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': '无效的JSON数据'}, status=400)
    
    repo_url: str = data.get('repo_url', '')
    
    if not repo_url:
        return JsonResponse({'error': '缺少仓库URL'}, status=400)
    
    try:
        result: Dict[str, Any] = sync_to_async(git_service.clone(repo_url))
        
        # 如果克隆成功，自动切换工作区到新仓库
        if result.get('success') and result.get('path'):
            workspace_path: str = result['path']
            
            # 更新settings中的WORKSPACE_PATH
            settings.WORKSPACE_PATH = workspace_path
            
            # 更新file_service和git_service的工作区
            from . import files
            files.file_service = FileService(workspace_path)
            git_service = GitService(workspace_path)
            
            # 保存到配置文件
            config_file: Path = Path(settings.BASE_DIR) / 'workspace_config.json'
            config: Dict[str, Any] = {}
            if config_file.exists():
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
            
            config['workspace_path'] = workspace_path
            
            # 更新工作区列表
            workspaces: List[str] = config.get('workspaces', [])
            normalized_path: str = workspace_path.replace('\\', '/').lower()
            
            unique_workspaces: List[str] = []
            normalized_list: List[str] = []
            for ws in workspaces:
                norm_ws: str = ws.replace('\\', '/').lower()
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
def git_commit(request: HttpRequest) -> JsonResponse:
    """提交更改"""
    try:
        data: Dict[str, Any] = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': '无效的JSON数据'}, status=400)
    
    message: str = data.get('message', '')
    files: Union[List[str], None] = data.get('files')
    
    if not message:
        return JsonResponse({'error': '缺少提交信息'}, status=400)
    
    try:
        result: Dict[str, Any] = sync_to_async(git_service.commit(message, files))
        return JsonResponse(result)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def git_push(request: HttpRequest) -> JsonResponse:
    """推送到远程仓库"""
    try:
        data: Dict[str, Any] = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': '无效的JSON数据'}, status=400)
    
    remote: str = data.get('remote', 'origin')
    branch: Union[str, None] = data.get('branch')
    
    try:
        result: Dict[str, Any] = sync_to_async(git_service.push(remote, branch))
        return JsonResponse(result)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def git_pull(request: HttpRequest) -> JsonResponse:
    """从远程仓库拉取"""
    try:
        data: Dict[str, Any] = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': '无效的JSON数据'}, status=400)
    
    remote: str = data.get('remote', 'origin')
    branch: Union[str, None] = data.get('branch')
    
    try:
        result: Dict[str, Any] = sync_to_async(git_service.pull(remote, branch))
        return JsonResponse(result)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def git_switch_branch(request: HttpRequest) -> JsonResponse:
    """切换分支"""
    try:
        data: Dict[str, Any] = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': '无效的JSON数据'}, status=400)
    
    branch: str = data.get('branch', '')
    
    if not branch:
        return JsonResponse({'error': '缺少分支名称'}, status=400)
    
    try:
        result: Dict[str, Any] = sync_to_async(git_service.switch_branch(branch))
        return JsonResponse(result)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def git_history(request: HttpRequest) -> JsonResponse:
    """获取提交历史"""
    try:
        limit_val = request.GET.get('limit', '20')
        limit: int = int(str(limit_val)) if limit_val else 20
        result: Dict[str, Any] = sync_to_async(git_service.get_commit_history(limit))
        return JsonResponse(result)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
