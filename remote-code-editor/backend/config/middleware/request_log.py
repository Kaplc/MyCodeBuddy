"""请求日志中间件 - 记录所有 API 请求"""
import logging
import json
import traceback

logger = logging.getLogger('workflow')

class RequestLogMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # 记录请求信息
        request_id = id(request)
        logger.info(f"[Request] {request.method} {request.path} | query: {request.GET.dict()}")

        # 记录请求体（如果是 POST/PUT）
        if request.method in ['POST', 'PUT', 'PATCH']:
            body = request.body
            if body:
                try:
                    body_json = json.loads(body)
                    # 隐藏敏感字段
                    if 'graph' in body_json:
                        body_json['graph'] = f"<graph with {len(body_json.get('graph', {}).get('nodes', []))} nodes>"
                    logger.info(f"[Request] {request.method} {request.path} | body: {json.dumps(body_json, ensure_ascii=False)[:500]}")
                except:
                    logger.info(f"[Request] {request.method} {request.path} | body: {body[:200]}")

        # 捕获视图异常
        try:
            response = self.get_response(request)
        except Exception as e:
            # 记录完整的 traceback
            tb = traceback.format_exc()
            logger.error(f"[Exception] {request.method} {request.path} | {type(e).__name__}: {str(e)}\n{tb}")
            raise  # 重新抛出异常让 Django 处理

        # 记录响应状态
        if response.status_code >= 400:
            # 尝试读取响应内容
            try:
                if hasattr(response, 'content'):
                    content = response.content.decode('utf-8')[:200]
                    logger.warning(f"[Response] {request.method} {request.path} | status: {response.status_code} | body: {content}")
                else:
                    logger.warning(f"[Response] {request.method} {request.path} | status: {response.status_code}")
            except:
                logger.warning(f"[Response] {request.method} {request.path} | status: {response.status_code}")
        else:
            logger.info(f"[Response] {request.method} {request.path} | status: {response.status_code}")

        return response
