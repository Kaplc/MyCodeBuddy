"""
健康检查视图
"""
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings


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
