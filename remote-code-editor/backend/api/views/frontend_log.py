"""
前端日志视图
"""
import json
import logging
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt

logger = logging.getLogger('frontend')


@csrf_exempt
@require_http_methods(["POST"])
def frontend_log(request):
    """
    接收前端日志并记录到后端日志

    Body:
        level: 日志级别 (error, warn, info)
        message: 日志消息
        timestamp: 时间戳
        url: 页面URL
        其他额外信息...
    """
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': '无效的JSON格式'}, status=400)

    level = data.get('level', 'info')
    message = data.get('message', '')
    timestamp = data.get('timestamp', '')
    url = data.get('url', '')

    # 构建日志消息
    log_msg = f"[前端日志] [{level.upper()}] {timestamp} | {url} | {message}"

    # 提取额外信息
    extra_info = {k: v for k, v in data.items() if k not in ['level', 'message', 'timestamp', 'url']}
    if extra_info:
        log_msg += f" | 额外信息: {extra_info}"

    # 根据级别记录日志
    if level == 'error':
        logger.error(log_msg)
    elif level == 'warn':
        logger.warning(log_msg)
    else:
        logger.info(log_msg)

    return JsonResponse({'success': True})
