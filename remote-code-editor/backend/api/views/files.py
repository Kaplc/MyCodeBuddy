"""
文件操作视图
"""
import json
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings

from services.file_service import FileService


# 初始化文件服务
file_service = FileService(settings.WORKSPACE_PATH)


def sync_to_async(coro):
    """将协程转换为同步调用的辅助函数"""
    import asyncio
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
        result = sync_to_async(file_service.read_file(path))
        # result 包含 content, is_binary, mime_type 等信息
        return JsonResponse({'path': path, **result})
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
@require_http_methods(["POST"])
def copy_file_or_dir(request):
    """复制文件或目录"""
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': '无效的JSON数据'}, status=400)

    source_path = data.get('source_path', '')
    target_path = data.get('target_path', '')
    is_dir = data.get('is_dir', False)

    if not source_path or not target_path:
        return JsonResponse({'error': '缺少参数'}, status=400)

    try:
        result = sync_to_async(file_service.copy(source_path, target_path, is_dir))
        return JsonResponse({'success': True, 'new_path': result})
    except FileNotFoundError:
        return JsonResponse({'error': f'源文件或目录不存在: {source_path}'}, status=404)
    except FileExistsError:
        return JsonResponse({'error': f'目标文件或目录已存在: {target_path}'}, status=409)
    except PermissionError:
        return JsonResponse({'error': '无权限复制'}, status=403)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
