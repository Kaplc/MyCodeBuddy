"""
API视图
提供文件操作和系统接口
"""
import asyncio
import json
import os
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt

from services.file_service import FileService
from services.git_service import GitService
from django.conf import settings


# 初始化文件服务
file_service = FileService(settings.WORKSPACE_PATH)

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
        # 如果事件循环正在运行（在ASGI中），创建一个新的事件循环
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
def health_check(request):
    """健康检查"""
    return JsonResponse({
        'status': 'healthy',
        'workspace': settings.WORKSPACE_PATH
    })


@csrf_exempt
@require_http_methods(["GET"])
def ai_health_check(request):
    """AI服务健康检查"""
    try:
        # 检查是否配置了API key
        if not settings.ZHIPU_API_KEY:
            return JsonResponse({
                'status': 'unhealthy',
                'message': 'AI服务未配置API密钥'
            }, status=503)
        
        # 简单验证API key格式（zhipu API key格式检查）
        api_key = settings.ZHIPU_API_KEY
        if not api_key or len(api_key) < 10:
            return JsonResponse({
                'status': 'unhealthy',
                'message': 'AI服务API密钥格式无效'
            }, status=503)
        
        # 只在初次检查时测试真实连接（可通过参数控制）
        test_connection = request.GET.get('test', 'false').lower() == 'true'
        
        if test_connection:
            # 测试API连接
            from zhipuai import ZhipuAI
            client = ZhipuAI(api_key=settings.ZHIPU_API_KEY)
            
            response = client.chat.completions.create(
                model="glm-4-flash",
                messages=[{"role": "user", "content": "test"}],
                max_tokens=10
            )
        
        return JsonResponse({
            'status': 'healthy',
            'message': 'AI服务已配置'
        })
        
    except Exception as e:
        return JsonResponse({
            'status': 'unhealthy',
            'message': f'AI服务连接失败: {str(e)}'
        }, status=503)


@csrf_exempt
@require_http_methods(["GET"])
def ai_tab_health_check(request):
    """AI Tab补全服务健康检查"""
    try:
        # 检查是否配置了API key
        if not settings.ZHIPU_API_KEY:
            return JsonResponse({
                'status': 'unhealthy',
                'enabled': False,
                'message': 'AI服务未配置API密钥'
            }, status=503)
        
        return JsonResponse({
            'status': 'healthy',
            'enabled': True,
            'message': 'AI Tab补全服务已配置'
        })
        
    except Exception as e:
        return JsonResponse({
            'status': 'unhealthy',
            'enabled': False,
            'message': f'AI服务连接失败: {str(e)}'
        }, status=503)


@csrf_exempt
@require_http_methods(["GET"])
def get_file_tree(request):
    """获取文件目录树"""
    # 检查工作区是否设置
    if not settings.WORKSPACE_PATH:
        return JsonResponse({
            'error': '工作区未设置，请先选择工作区'
        }, status=400)

    path = request.GET.get('path', '')

    try:
        items = sync_to_async(file_service.list_directory(path))
        return JsonResponse(items, safe=False)
    except ValueError as e:
        # 捕获工作区未设置的错误
        return JsonResponse({'error': str(e)}, status=400)
    except FileNotFoundError:
        return JsonResponse({'error': f'目录不存在: {path}'}, status=404)
    except PermissionError:
        return JsonResponse({'error': f'无权限访问: {path}'}, status=403)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def read_file(request):
    """读取文件内容"""
    path = request.GET.get('path', '')

    if not path:
        return JsonResponse({'error': '缺少path参数'}, status=400)

    try:
        content = sync_to_async(file_service.read_file(path))
        return JsonResponse({'path': path, 'content': content})
    except FileNotFoundError:
        return JsonResponse({'error': f'文件不存在: {path}'}, status=404)
    except IsADirectoryError:
        return JsonResponse({'error': f'路径是目录，不是文件: {path}'}, status=400)
    except PermissionError:
        return JsonResponse({'error': f'无权限访问: {path}'}, status=403)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def save_file(request):
    """保存文件内容"""
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': '无效的JSON数据'}, status=400)

    path = data.get('path', '')
    content = data.get('content', '')

    if not path:
        return JsonResponse({'error': '缺少path参数'}, status=400)

    try:
        sync_to_async(file_service.save_file(path, content))
        return JsonResponse({'success': True, 'message': f'文件已保存: {path}'})
    except FileNotFoundError:
        return JsonResponse({'error': '目录不存在'}, status=404)
    except PermissionError:
        return JsonResponse({'error': '无权限写入'}, status=403)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def create_file_or_dir(request):
    """创建文件或目录"""
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': '无效的JSON数据'}, status=400)
    
    path = data.get('path', '')
    is_dir = data.get('is_dir', False)
    
    if not path:
        return JsonResponse({'error': '缺少path参数'}, status=400)
    
    try:
        result = sync_to_async(file_service.create(path, is_dir))
        return JsonResponse({'success': True, 'path': result, 'is_dir': is_dir})
    except FileExistsError:
        return JsonResponse({'error': f'文件或目录已存在: {path}'}, status=409)
    except PermissionError:
        return JsonResponse({'error': '无权限创建'}, status=403)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def rename_file_or_dir(request):
    """重命名文件或目录"""
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': '无效的JSON数据'}, status=400)
    
    old_path = data.get('old_path', '')
    new_name = data.get('new_name', '')
    
    if not old_path or not new_name:
        return JsonResponse({'error': '缺少参数'}, status=400)
    
    try:
        result = sync_to_async(file_service.rename(old_path, new_name))
        return JsonResponse({'success': True, 'new_path': result})
    except FileNotFoundError:
        return JsonResponse({'error': f'文件或目录不存在: {old_path}'}, status=404)
    except FileExistsError:
        return JsonResponse({'error': f'目标名称已存在: {new_name}'}, status=409)
    except PermissionError:
        return JsonResponse({'error': '无权限重命名'}, status=403)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def delete_file_or_dir(request):
    """删除文件或目录"""
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': '无效的JSON数据'}, status=400)
    
    path = data.get('path', '')
    
    if not path:
        return JsonResponse({'error': '缺少path参数'}, status=400)
    
    try:
        sync_to_async(file_service.delete(path))
        return JsonResponse({'success': True, 'message': f'已删除: {path}'})
    except FileNotFoundError:
        return JsonResponse({'error': f'文件或目录不存在: {path}'}, status=404)
    except PermissionError:
        return JsonResponse({'error': '无权限删除'}, status=403)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def check_exists(request):
    """检查文件或目录是否存在"""
    path = request.GET.get('path', '')
    
    if not path:
        return JsonResponse({'error': '缺少path参数'}, status=400)
    
    exists = sync_to_async(file_service.exists(path))
    return JsonResponse({'exists': exists, 'path': path})


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
    import os
    from pathlib import Path
    
    path = request.GET.get('path', '')
    
    try:
        if not path:
            # 返回根目录/驱动器列表
            import platform
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
    import os
    import logging
    from pathlib import Path
    
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
    global file_service
    file_service = FileService(settings.WORKSPACE_PATH)
    
    # 更新git_service的工作区
    global git_service
    git_service = GitService(settings.WORKSPACE_PATH)
    
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
    
    # 获取工作区列表并规范化路径（统一使用正斜杠）
    workspaces = config.get('workspaces', [])
    normalized_path = str(path_obj).replace('\\', '/')  # 规范化路径
    
    # 去重：移除所有指向同一目录的路径（规范化后比较）
    unique_workspaces = []
    normalized_list = []
    for ws in workspaces:
        norm_ws = ws.replace('\\', '/')
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
    import os
    from pathlib import Path
    
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
                        # 规范化路径（统一使用正斜杠）
                        normalized_path = str(ws_obj).replace('\\', '/')
                        
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
    import os
    from pathlib import Path
    
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
            global file_service
            from services.file_service import FileService
            file_service = FileService('')
            # 重新初始化 git_service
            global git_service
            from services.git_service import GitService
            git_service = GitService('')
        
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        
        return JsonResponse({'success': True, 'message': '工作区已删除'})
        
    except Exception as e:
        print(f'删除工作区失败: {str(e)}')
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def ai_code_complete(request):
    """AI代码补全"""
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': '无效的JSON数据'}, status=400)
    
    code = data.get('code', '')
    language = data.get('language', 'python')
    
    if not code:
        return JsonResponse({'suggestions': []})
    
    try:
        # 调用智谱AI进行代码补全
        from zhipuai import ZhipuAI
        client = ZhipuAI(api_key=settings.ZHIPU_API_KEY)
        
        # 构建提示词
        prompt = f"""你是一个代码补全助手。请根据以下{language}代码上下文，提供3个最可能的代码补全建议。
只返回补全的代码片段，不要解释。每个建议单独一行。

代码上下文：
{code}

补全建议："""
        
        response = client.chat.completions.create(
            model="glm-4-flash",
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=200
        )
        
        # 解析AI返回的建议
        suggestions_text = response.choices[0].message.content.strip()
        suggestions = []
        
        for line in suggestions_text.split('\n'):
            line = line.strip()
            if line and not line.startswith('#') and not line.startswith('//'):
                suggestions.append({
                    'text': line,
                    'description': f'AI建议的{language}代码'
                })
        
        return JsonResponse({'suggestions': suggestions[:3]})  # 最多返回3个建议
        
    except Exception as e:
        print(f'AI补全错误: {str(e)}')
        return JsonResponse({'suggestions': []})


# ==================== Git相关视图 ====================

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
    """克隆远程仓库（使用系统Git凭据）"""
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': '无效的JSON数据'}, status=400)
    
    repo_url = data.get('repo_url', '')
    
    if not repo_url:
        return JsonResponse({'error': '缺少仓库URL'}, status=400)
    
    try:
        result = sync_to_async(git_service.clone(repo_url))
        return JsonResponse(result)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def git_commit(request):
    """提交更改"""
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


import re
from django.conf import settings

@csrf_exempt
@require_http_methods(["POST"])
def search_content(request):
    """在文件中搜索内容"""
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': '无效的JSON数据'}, status=400)
    
    query = data.get('query', '')
    options = data.get('options', {})
    
    if not query:
        return JsonResponse({'results': []})
    
    # 获取搜索选项
    use_regex = options.get('regex', False)
    case_sensitive = options.get('caseSensitive', False)
    whole_word = options.get('wholeWord', False)
    
    # 获取工作区路径
    workspace_path = settings.WORKSPACE_PATH
    if not workspace_path or not os.path.exists(workspace_path):
        return JsonResponse({'error': '工作区路径无效'}, status=400)
    
    results = []
    
    # 需要忽略的目录
    ignore_dirs = {'.git', '__pycache__', 'node_modules', '.venv', 'venv', 'dist', 'build', '.idea', '.vscode'}
    
    def should_ignore(path):
        return any(ignored in path for ignored in ignore_dirs)
    
    def search_in_file(file_path):
        """在单个文件中搜索"""
        matches = []
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                for line_num, line in enumerate(f, 1):
                    # 构建搜索模式
                    search_pattern = query
                    if not use_regex:
                        search_pattern = re.escape(query)
                    if whole_word:
                        search_pattern = r'\b' + search_pattern + r'\b'
                    
                    flags = 0 if case_sensitive else re.IGNORECASE
                    
                    try:
                        if re.search(search_pattern, line, flags):
                            # 找到匹配，提取上下文
                            matches.append({
                                'line': line_num,
                                'column': 1,
                                'lineContent': line.rstrip()[:200]  # 限制显示长度
                            })
                    except re.error:
                        continue
                    
                    # 限制每个文件的匹配数量
                    if len(matches) >= 10:
                        break
        except Exception:
            pass
        return matches
    
    def walk_directory(directory):
        """遍历目录搜索"""
        for root, dirs, files in os.walk(directory):
            # 过滤掉忽略的目录
            dirs[:] = [d for d in dirs if d not in ignore_dirs]
            
            if should_ignore(root):
                continue
            
            for file in files:
                # 跳过二进制文件和大型文件
                if file.startswith('.') or file.endswith(('.pyc', '.exe', '.dll', '.so', '.bin')):
                    continue
                
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, workspace_path)
                
                matches = search_in_file(file_path)
                if matches:
                    results.append({
                        'file': rel_path,
                        'matches': matches
                    })
                    
                    # 限制返回的文件数量
                    if len(results) >= 50:
                        return
    
    walk_directory(workspace_path)
    
    return JsonResponse({'results': results})


# ==================== AI对话历史管理 ====================

@csrf_exempt
@require_http_methods(["GET"])
def list_conversations(request):
    """
    获取对话列表
    
    Query params:
        workspace: 工作区路径（可选，用于过滤）
        limit: 返回数量限制（默认20）
    """
    from api.models import Conversation
    
    workspace = request.GET.get('workspace', '')
    limit = int(request.GET.get('limit', 20))
    
    try:
        queryset = Conversation.objects.all()
        
        # 如果指定了工作区，则过滤
        if workspace:
            queryset = queryset.filter(workspace=workspace)
        
        conversations = queryset[:limit]
        
        result = []
        for conv in conversations:
            # 获取最后一条消息作为预览
            last_message = conv.messages.order_by('-created_at').first()
            preview = ''
            if last_message:
                preview = last_message.content[:100] if last_message.content else ''
            
            result.append({
                'id': str(conv.id),
                'title': conv.title,
                'workspace': conv.workspace,
                'model': conv.model,
                'mode': conv.mode,
                'message_count': conv.messages.count(),
                'preview': preview,
                'created_at': conv.created_at.isoformat(),
                'updated_at': conv.updated_at.isoformat()
            })
        
        return JsonResponse({'conversations': result})
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def create_conversation(request):
    """
    创建新对话
    
    Body:
        title: 对话标题（可选）
        workspace: 工作区路径（可选）
        model: 使用的模型（可选）
        mode: 对话模式 chat/agent（可选）
    """
    from api.models import Conversation
    
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        data = {}
    
    try:
        conversation = Conversation.objects.create(
            title=data.get('title', '新对话'),
            workspace=data.get('workspace', ''),
            model=data.get('model', 'glm-4-flash'),
            mode=data.get('mode', 'chat')
        )
        
        return JsonResponse({
            'id': str(conversation.id),
            'title': conversation.title,
            'workspace': conversation.workspace,
            'model': conversation.model,
            'mode': conversation.mode,
            'created_at': conversation.created_at.isoformat()
        })
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def get_conversation(request):
    """
    获取对话详情（包含所有消息）
    
    Query params:
        id: 对话ID
    """
    from api.models import Conversation
    
    conversation_id = request.GET.get('id', '')
    
    if not conversation_id:
        return JsonResponse({'error': '缺少对话ID'}, status=400)
    
    try:
        conversation = Conversation.objects.get(id=conversation_id)
        
        messages = []
        for msg in conversation.messages.all().order_by('created_at'):
            messages.append(msg.to_dict())
        
        return JsonResponse({
            'id': str(conversation.id),
            'title': conversation.title,
            'workspace': conversation.workspace,
            'model': conversation.model,
            'mode': conversation.mode,
            'messages': messages,
            'created_at': conversation.created_at.isoformat(),
            'updated_at': conversation.updated_at.isoformat()
        })
    
    except Conversation.DoesNotExist:
        return JsonResponse({'error': '对话不存在'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def update_conversation(request):
    """
    更新对话信息（如标题）
    
    Body:
        id: 对话ID
        title: 新标题（可选）
    """
    from api.models import Conversation
    
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': '无效的JSON格式'}, status=400)
    
    conversation_id = data.get('id', '')
    
    if not conversation_id:
        return JsonResponse({'error': '缺少对话ID'}, status=400)
    
    try:
        conversation = Conversation.objects.get(id=conversation_id)
        
        if 'title' in data:
            conversation.title = data['title']
        if 'model' in data:
            conversation.model = data['model']
        if 'mode' in data:
            conversation.mode = data['mode']
        
        conversation.save()
        
        return JsonResponse({
            'id': str(conversation.id),
            'title': conversation.title,
            'updated_at': conversation.updated_at.isoformat()
        })
    
    except Conversation.DoesNotExist:
        return JsonResponse({'error': '对话不存在'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def delete_conversation(request):
    """
    删除对话
    
    Body:
        id: 对话ID
    """
    from api.models import Conversation
    
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': '无效的JSON格式'}, status=400)
    
    conversation_id = data.get('id', '')
    
    if not conversation_id:
        return JsonResponse({'error': '缺少对话ID'}, status=400)
    
    try:
        conversation = Conversation.objects.get(id=conversation_id)
        conversation.delete()
        
        return JsonResponse({'success': True})
    
    except Conversation.DoesNotExist:
        return JsonResponse({'error': '对话不存在'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def add_message(request):
    """
    向对话添加消息
    
    Body:
        conversation_id: 对话ID
        role: 消息角色 (user/assistant/system/tool)
        content: 消息内容
        reasoning: 思考过程（可选）
        tool_calls: 工具调用信息（可选）
        tool_call_id: 工具调用ID（可选）
        tool_name: 工具名称（可选）
    """
    from api.models import Conversation, Message
    
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': '无效的JSON格式'}, status=400)
    
    conversation_id = data.get('conversation_id', '')
    role = data.get('role', '')
    content = data.get('content', '')
    
    if not conversation_id:
        return JsonResponse({'error': '缺少对话ID'}, status=400)
    
    if not role:
        return JsonResponse({'error': '缺少消息角色'}, status=400)
    
    try:
        conversation = Conversation.objects.get(id=conversation_id)
        
        message = Message.objects.create(
            conversation=conversation,
            role=role,
            content=content,
            reasoning=data.get('reasoning', ''),
            tool_calls=data.get('tool_calls'),
            tool_call_id=data.get('tool_call_id', ''),
            tool_name=data.get('tool_name', '')
        )
        
        # 更新对话的更新时间
        conversation.save()
        
        # 如果是第一条用户消息且标题是默认的，自动更新标题
        if role == 'user' and conversation.title == '新对话':
            # 使用消息内容的前30个字符作为标题
            new_title = content[:30].strip()
            if len(content) > 30:
                new_title += '...'
            conversation.title = new_title
            conversation.save()
        
        return JsonResponse({
            'id': str(message.id),
            'conversation_id': str(conversation.id),
            'role': message.role,
            'content': message.content,
            'created_at': message.created_at.isoformat()
        })
    
    except Conversation.DoesNotExist:
        return JsonResponse({'error': '对话不存在'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def clear_conversation(request):
    """
    清空对话消息（保留对话本身）
    
    Body:
        id: 对话ID
    """
    from api.models import Conversation
    
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': '无效的JSON格式'}, status=400)
    
    conversation_id = data.get('id', '')
    
    if not conversation_id:
        return JsonResponse({'error': '缺少对话ID'}, status=400)
    
    try:
        conversation = Conversation.objects.get(id=conversation_id)
        conversation.messages.all().delete()
        conversation.title = '新对话'
        conversation.save()
        
        return JsonResponse({'success': True})
    
    except Conversation.DoesNotExist:
        return JsonResponse({'error': '对话不存在'}, status=404)
    except Exception as e:
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



