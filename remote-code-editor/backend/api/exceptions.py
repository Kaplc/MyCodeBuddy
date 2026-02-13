"""
自定义异常处理
"""
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status


def custom_exception_handler(exc, context):
    """
    自定义异常处理器，避免依赖django.contrib.auth
    """
    # 调用DRF默认异常处理
    response = exception_handler(exc, context)
    
    if response is not None:
        return response
    
    # 处理未捕获的异常
    return Response(
        {'error': str(exc)},
        status=status.HTTP_500_INTERNAL_SERVER_ERROR
    )
