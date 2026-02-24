"""
搜索视图
"""
import os
import re
import json
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
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
