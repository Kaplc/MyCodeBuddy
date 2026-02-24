"""
工作区管理视图
"""
import os
import json
from pathlib import Path
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings

from services.file_service import FileService
from services.git_service import GitService


def sync_to_async(coro):
    """将协程转换为同步调用的辅助函数"""
    import asyncio
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
def get_system_drives(request):
    """获取系统驱动器列表（Windows）或根目录（Unix）"""
    import platform
    
    try:
        if platform.system() == 'Windows':
            import string
            drives = []
            for letter in string.ascii_uppercase:
                drive_path = f"{letter}:\\"
                if os.path.exists(drive_path):
                    drives.append({
                        'name': f"{letter}:",
                        'path': drive_path,
                        'is_drive': True
                    })
            return JsonResponse({'drives': drives})
        else:
            # Unix/Linux/Mac
            return JsonResponse({
                'drives': [{
                    'name': 'Root',
                    'path': '/',
                    'is_drive': True
                }]
            })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def browse_directory(request):
    """浏览目录，返回子目录列表（用于选择工作区）"""
    import platform
    
    path = request.GET.get('path', '')
    
    try:
        if not path:
            # 返回根目录/驱动器列表
            if platform.system() == 'Windows':
                import string
                items = []
                for letter in string.ascii_uppercase:
                    drive_path = f"{letter}:\\"
                    if os.path.exists(drive_path):
                        items.append({
                            'name': f"{letter}:",
                            'path': drive_path,
                            'is_dir': True,
                            'is_drive': True
                        })
                return JsonResponse({'current_path': '', 'items': items, 'parent': None})
            else:
                path = '/'
        
        # 获取目录内容
        path_obj = Path(path)
        if not path_obj.exists() or not path_obj.is_dir():
            return JsonResponse({'error': f'目录不存在: {path}'}, status=404)
        
        items = []
        try:
            for item in sorted(path_obj.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower())):
                if item.is_dir():
                    # 检查是否可以访问
                    try:
                        list(item.iterdir())
                        items.append({
                            'name': item.name,
                            'path': str(item),
                            'is_dir': True
                        })
                    except PermissionError:
                        # 跳过无权限的目录
                        pass
        except PermissionError:
            return JsonResponse({'error': f'无权限访问: {path}'}, status=403)
        
        # 获取父目录
        parent = str(path_obj.parent) if path_obj.parent != path_obj else None
        
        return JsonResponse({
            'current_path': str(path_obj),
            'items': items,
            'parent': parent
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def set_workspace(request):
    """设置工作区路径"""
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        logger.info(f"收到设置工作区请求: {request.body}")
        data = json.loads(request.body)
    except json.JSONDecodeError as e:
        logger.error(f"JSON解析失败: {e}, body: {request.body}")
        return JsonResponse({'error': '无效的JSON数据'}, status=400)
    
    # 支持两种模式：通过name创建或通过path设置
    workspace_name = data.get('name', '')
    new_path = data.get('path', '')
    
    # 优先使用name参数
    if workspace_name:
        logger.info(f"通过名称创建工作区: {workspace_name}")
        # 获取项目根目录
        project_root = Path(settings.BASE_DIR).parent
        workspaces_dir = project_root / 'workspaces'
        
        # 确保workspaces目录存在
        workspaces_dir.mkdir(parents=True, exist_ok=True)
        
        # 创建工作区路径
        path_obj = (workspaces_dir / workspace_name).resolve()
        
        # 如果目录不存在，创建它
        if not path_obj.exists():
            try:
                logger.info(f"创建工作区目录: {path_obj}")
                path_obj.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                logger.error(f"创建目录失败: {e}")
                return JsonResponse({'error': f'无法创建工作区目录: {str(e)}'}, status=400)
    elif new_path:
        # 兼容旧的path参数模式
        logger.info(f"通过路径设置工作区: {new_path}")
        
        if not new_path:
            return JsonResponse({'error': '缺少name或path参数'}, status=400)
        
        # 获取项目根目录
        project_root = Path(settings.BASE_DIR).parent
        workspaces_dir = project_root / 'workspaces'
        
        # 如果是相对路径，相对于项目根目录解析
        path_obj = Path(new_path)
        if not path_obj.is_absolute():
            # 总是相对于项目根目录解析相对路径
            path_obj = (project_root / new_path).resolve()
            logger.info(f"相对路径，已转换为项目根目录相对路径: {path_obj}")
        else:
            path_obj = path_obj.resolve()
        
        # 如果目录不存在，询问是否创建
        if not path_obj.exists():
            try:
                logger.info(f"创建目录: {path_obj}")
                path_obj.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                logger.error(f"创建目录失败: {e}")
                return JsonResponse({'error': f'无法创建目录: {str(e)}'}, status=400)
    else:
        return JsonResponse({'error': '缺少name或path参数'}, status=400)
    
    logger.info(f"最终路径对象: {path_obj}, 存在: {path_obj.exists()}")
    
    # 禁止将项目根目录设置为工作区
    if path_obj == Path(settings.BASE_DIR).parent.resolve():
        return JsonResponse({
            'error': '不能将项目根目录设置为工作区，请选择 workspaces 目录下的子目录'
        }, status=400)
    
    # 确保工作区在 workspaces 目录下
    workspaces_resolved = (Path(settings.BASE_DIR).parent / 'workspaces').resolve()
    logger.info(f"解析后的路径: {path_obj}, workspaces解析: {workspaces_resolved}")
    
    # 使用兼容的方式检查路径关系
    try:
        is_relative = path_obj.is_relative_to(workspaces_resolved)
    except AttributeError:
        # Python 3.9 以下版本不支持 is_relative_to，使用替代方法
        is_relative = str(path_obj).startswith(str(workspaces_resolved))
    
    if not is_relative:
        return JsonResponse({
            'error': f'工作区必须在 workspaces 目录下创建。有效路径格式: workspaces/你的工作区名称'
        }, status=400)
    
    # 检查是否是目录
    if not path_obj.is_dir():
        return JsonResponse({'error': '路径不是目录'}, status=400)
    
    # 更新settings中的WORKSPACE_PATH
    workspace_path = str(path_obj.absolute())
    logger.info(f"更新工作区路径: {workspace_path}")
    settings.WORKSPACE_PATH = workspace_path
    
    # 更新file_service的工作区
    from . import files
    files.file_service = FileService(workspace_path)
    
    # 更新git_service的工作区
    from . import git
    git.git_service = GitService(workspace_path)
    
    # 保存到配置文件（包括工作区列表）
    config_file = Path(settings.BASE_DIR) / 'workspace_config.json'
    logger.info(f"配置文件路径: {config_file}")
    
    # 读取现有配置
    config = {}
    if config_file.exists():
        logger.info("读取现有配置文件")
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
    
    # 更新当前工作区
    config['workspace_path'] = workspace_path
    
    # 获取工作区列表并规范化路径（统一使用正斜杠 + 小写）
    workspaces = config.get('workspaces', [])
    normalized_path = str(path_obj).replace('\\', '/').lower()  # 规范化路径

    # 去重：移除所有指向同一目录的路径（规范化后比较）
    unique_workspaces = []
    normalized_list = []
    for ws in workspaces:
        norm_ws = ws.replace('\\', '/').lower()
        if norm_ws not in normalized_list:
            normalized_list.append(norm_ws)
            unique_workspaces.append(ws)

    # 如果当前工作区不在列表中，则添加
    if normalized_path not in normalized_list:
        unique_workspaces.append(workspace_path)
        normalized_list.append(normalized_path)
    
    # 保存配置
    config['workspaces'] = unique_workspaces
    logger.info(f"保存配置: {config}")
    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)
    
    logger.info(f"工作区设置成功: {workspace_path}")
    return JsonResponse({
        'success': True,
        'workspace': workspace_path,
        'message': f'工作区已设置为: {workspace_path}'
    })


@csrf_exempt
@require_http_methods(["GET"])
def get_workspace(request):
    """获取当前工作区路径"""
    return JsonResponse({
        'workspace': settings.WORKSPACE_PATH
    })


@csrf_exempt
@require_http_methods(["GET"])
def list_workspaces(request):
    """获取工作区列表"""
    try:
        config_file = Path(settings.BASE_DIR) / 'workspace_config.json'
        
        workspaces = []
        seen_paths = set()  # 用于去重
        
        if config_file.exists():
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
                
                # 获取工作区列表（可能是一个列表，也可能是一个包含列表的对象）
                workspace_list = config.get('workspaces', [])
                
                for ws_path in workspace_list:
                    # 验证工作区是否存在
                    ws_obj = Path(ws_path)
                    if ws_obj.exists() and ws_obj.is_dir():
                        # 规范化路径（统一使用正斜杠 + 小写）
                        normalized_path = str(ws_obj).replace('\\', '/').lower()

                        # 去重：如果路径已存在则跳过
                        if normalized_path in seen_paths:
                            continue
                        seen_paths.add(normalized_path)
                        
                        # 提取目录名作为显示名称
                        name = ws_obj.name
                        workspaces.append({
                            'path': ws_path,
                            'name': name
                        })
        
        return JsonResponse({'workspaces': workspaces})
    except Exception as e:
        print(f'获取工作区列表失败: {str(e)}')
        return JsonResponse({'workspaces': []})


@csrf_exempt
@require_http_methods(["POST"])
def delete_workspace(request):
    """删除工作区（从列表中移除，不删除实际目录）"""
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': '无效的JSON数据'}, status=400)
    
    path_to_delete = data.get('path', '')
    
    if not path_to_delete:
        return JsonResponse({'error': '缺少path参数'}, status=400)
    
    try:
        config_file = Path(settings.BASE_DIR) / 'workspace_config.json'
        
        if not config_file.exists():
            return JsonResponse({'error': '配置文件不存在'}, status=404)
        
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        workspaces = config.get('workspaces', [])
        
        if path_to_delete not in workspaces:
            return JsonResponse({'error': '工作区不存在'}, status=404)
        
        # 从列表中移除
        workspaces.remove(path_to_delete)
        config['workspaces'] = workspaces
        
        # 如果删除的是当前工作区，清空当前工作区
        if settings.WORKSPACE_PATH == path_to_delete:
            settings.WORKSPACE_PATH = ''
            # 重新初始化 file_service
            from . import files
            files.file_service = FileService('')
        
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        
        return JsonResponse({'success': True, 'message': '工作区已删除'})
        
    except Exception as e:
        print(f'删除工作区失败: {str(e)}')
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def get_workspace_files(request):
    """
    获取工作区的所有文件列表
    
    Query params:
        path: 工作区路径
    """
    workspace_path = request.GET.get('path', '')
    
    if not workspace_path:
        return JsonResponse({'error': '缺少工作区路径'}, status=400)
    
    if not os.path.exists(workspace_path):
        return JsonResponse({'error': '工作区路径不存在'}, status=404)
    
    try:
        files = []
        
        # 遍历工作区目录
        for root, dirs, filenames in os.walk(workspace_path):
            # 过滤掉隐藏目录和常见的忽略目录
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in [
                'node_modules', '__pycache__', 'venv', 'env', 'dist', 'build', 
                '.git', '.vscode', '.idea', 'target', 'out'
            ]]
            
            for filename in filenames:
                # 过滤掉隐藏文件
                if filename.startswith('.'):
                    continue
                
                file_path = os.path.join(root, filename)
                
                # 只包含文本文件（根据扩展名）
                text_extensions = [
                    '.txt', '.md', '.py', '.js', '.ts', '.jsx', '.tsx', '.vue', 
                    '.java', '.c', '.cpp', '.h', '.hpp', '.cs', '.go', '.rs', 
                    '.php', '.rb', '.swift', '.kt', '.scala', '.lua', '.sh', 
                    '.bash', '.zsh', '.fish', '.ps1', '.bat', '.cmd', '.json', 
                    '.xml', '.yaml', '.yml', '.toml', '.ini', '.cfg', '.conf', 
                    '.html', '.css', '.scss', '.sass', '.less', '.sql', '.r', 
                    '.m', '.mm', '.dart', '.ex', '.exs', '.erl', '.hrl', '.clj', 
                    '.cljs', '.cljc', '.edn', '.groovy', '.gradle', '.proto'
                ]
                
                if any(filename.endswith(ext) for ext in text_extensions):
                    files.append({
                        'path': file_path,
                        'name': filename
                    })
        
        return JsonResponse({
            'files': files,
            'count': len(files)
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
