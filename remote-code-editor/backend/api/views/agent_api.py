"""
Agent API 接口
提供代码生成、验证、索引等功能的 REST API
"""
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.conf import settings

from agent.code_agent import CodeAgent, solve_task
from pipeline.verify_pipeline import VerifyPipeline, verify_code
from code_index.indexer import CodeIndexer
from code_index.searcher import CodeSearcher


# 全局代码索引（延迟初始化）
_code_graph = None
_code_searcher = None


def _get_searcher(workspace: str = None) -> CodeSearcher:
    """获取代码搜索器（带缓存）"""
    global _code_graph, _code_searcher
    
    if _code_searcher is None and workspace:
        indexer = CodeIndexer(workspace)
        _code_graph = indexer.index()
        _code_searcher = CodeSearcher(_code_graph)
    
    return _code_searcher


@csrf_exempt
@require_http_methods(["POST"])
def run_agent(request):
    """
    运行代码生成 Agent
    
    POST /api/agent/run/
    {
        "task": "编写一个排序函数",
        "max_iterations": 5,
        "enable_type_check": true,
        "enable_lint": true
    }
    """
    try:
        data = json.loads(request.body)
        task = data.get("task", "")
        
        if not task:
            return JsonResponse({
                "success": False,
                "error": "缺少 task 参数"
            }, status=400)
        
        # 创建 Agent
        agent = CodeAgent(
            api_key=settings.ZHIPU_API_KEY,
            max_fix_iterations=data.get("max_iterations", 5),
            enable_type_check=data.get("enable_type_check", True),
            enable_lint=data.get("enable_lint", True)
        )
        
        # 运行任务
        result = agent.run(
            task,
            test_code=data.get("test_code"),
            z3_spec=data.get("z3_spec")
        )
        
        return JsonResponse({
            "success": result.success,
            "code": result.code,
            "iterations": result.iterations,
            "verification": result.verification_result.to_dict() if result.verification_result else None,
            "error": result.error
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            "success": False,
            "error": "无效的 JSON 数据"
        }, status=400)
    except Exception as e:
        return JsonResponse({
            "success": False,
            "error": str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def verify_code_api(request):
    """
    验证代码
    
    POST /api/agent/verify/
    {
        "code": "def hello(): pass",
        "enable_type_check": true,
        "enable_lint": true,
        "test_code": "def test_hello(): assert True"
    }
    """
    try:
        data = json.loads(request.body)
        code = data.get("code", "")
        
        if not code:
            return JsonResponse({
                "success": False,
                "error": "缺少 code 参数"
            }, status=400)
        
        # 创建验证流水线
        pipeline = VerifyPipeline(
            enable_type_check=data.get("enable_type_check", True),
            enable_lint=data.get("enable_lint", True),
            enable_symbolic=data.get("enable_symbolic", True),
            enable_z3=data.get("enable_z3", False),
            enable_runtime=data.get("enable_runtime", False)
        )
        
        # 运行验证
        result = pipeline.run(
            code,
            test_code=data.get("test_code"),
            z3_spec=data.get("z3_spec")
        )
        
        return JsonResponse(result.to_dict())
        
    except json.JSONDecodeError:
        return JsonResponse({
            "success": False,
            "error": "无效的 JSON 数据"
        }, status=400)
    except Exception as e:
        return JsonResponse({
            "success": False,
            "error": str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def generate_tests(request):
    """
    生成测试代码
    
    POST /api/agent/generate-tests/
    {
        "code": "def add(a, b): return a + b"
    }
    """
    try:
        data = json.loads(request.body)
        code = data.get("code", "")
        
        if not code:
            return JsonResponse({
                "success": False,
                "error": "缺少 code 参数"
            }, status=400)
        
        agent = CodeAgent(api_key=settings.ZHIPU_API_KEY)
        test_code = agent.generate_tests(code)
        
        return JsonResponse({
            "success": True,
            "test_code": test_code
        })
        
    except Exception as e:
        return JsonResponse({
            "success": False,
            "error": str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def index_workspace(request):
    """
    索引工作区
    
    POST /api/agent/index/
    {
        "workspace": "/path/to/workspace"
    }
    """
    global _code_graph, _code_searcher
    
    try:
        data = json.loads(request.body)
        workspace = data.get("workspace", "")
        
        if not workspace:
            return JsonResponse({
                "success": False,
                "error": "缺少 workspace 参数"
            }, status=400)
        
        # 创建索引
        indexer = CodeIndexer(workspace)
        _code_graph = indexer.index()
        _code_searcher = CodeSearcher(_code_graph)
        
        return JsonResponse({
            "success": True,
            "stats": _code_graph.to_dict()["stats"]
        })
        
    except Exception as e:
        return JsonResponse({
            "success": False,
            "error": str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def search_symbol(request):
    """
    搜索符号
    
    GET /api/agent/search/?q=function_name&type=function
    """
    try:
        query = request.GET.get("q", "")
        symbol_type = request.GET.get("type")
        limit = int(request.GET.get("limit", 20))
        
        if not query:
            return JsonResponse({
                "success": False,
                "error": "缺少 q 参数"
            }, status=400)
        
        searcher = _get_searcher()
        if not searcher:
            return JsonResponse({
                "success": False,
                "error": "代码索引未初始化，请先调用 /api/agent/index/"
            }, status=400)
        
        results = searcher.search_symbol(query, symbol_type, limit)
        
        return JsonResponse({
            "success": True,
            "results": [
                {
                    "name": r.symbol.name,
                    "type": r.symbol.type,
                    "file": r.symbol.file,
                    "line": r.symbol.line,
                    "score": r.score,
                    "match_type": r.match_type
                }
                for r in results
            ]
        })
        
    except Exception as e:
        return JsonResponse({
            "success": False,
            "error": str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def get_references(request):
    """
    获取符号引用
    
    GET /api/agent/references/?name=function_name
    """
    try:
        name = request.GET.get("name", "")
        
        if not name:
            return JsonResponse({
                "success": False,
                "error": "缺少 name 参数"
            }, status=400)
        
        searcher = _get_searcher()
        if not searcher:
            return JsonResponse({
                "success": False,
                "error": "代码索引未初始化"
            }, status=400)
        
        references = searcher.search_references(name)
        
        return JsonResponse({
            "success": True,
            "references": references
        })
        
    except Exception as e:
        return JsonResponse({
            "success": False,
            "error": str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def get_call_graph(request):
    """
    获取调用图
    
    GET /api/agent/call-graph/?name=function_name&depth=2
    """
    try:
        name = request.GET.get("name", "")
        depth = int(request.GET.get("depth", 2))
        
        if not name:
            return JsonResponse({
                "success": False,
                "error": "缺少 name 参数"
            }, status=400)
        
        searcher = _get_searcher()
        if not searcher:
            return JsonResponse({
                "success": False,
                "error": "代码索引未初始化"
            }, status=400)
        
        call_graph = searcher.get_call_graph(name, depth)
        
        return JsonResponse({
            "success": True,
            "call_graph": call_graph
        })
        
    except Exception as e:
        return JsonResponse({
            "success": False,
            "error": str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def get_file_outline(request):
    """
    获取文件大纲
    
    GET /api/agent/outline/?file=path/to/file.py
    """
    try:
        file = request.GET.get("file", "")
        
        if not file:
            return JsonResponse({
                "success": False,
                "error": "缺少 file 参数"
            }, status=400)
        
        searcher = _get_searcher()
        if not searcher:
            return JsonResponse({
                "success": False,
                "error": "代码索引未初始化"
            }, status=400)
        
        outline = searcher.get_file_outline(file)
        
        return JsonResponse({
            "success": True,
            "outline": outline
        })
        
    except Exception as e:
        return JsonResponse({
            "success": False,
            "error": str(e)
        }, status=500)
