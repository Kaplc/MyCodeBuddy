"""
AI对话和对话历史管理视图
"""
import json
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings


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


# ==================== 对话历史管理 ====================

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
