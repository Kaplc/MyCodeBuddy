"""
代码搜索器
提供基于代码图的智能搜索功能
"""
import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from .code_graph import CodeGraph, CodeSymbol


@dataclass
class SearchResult:
    """搜索结果"""
    symbol: CodeSymbol
    score: float
    match_type: str  # exact, prefix, contains, fuzzy


class CodeSearcher:
    """
    代码搜索器
    
    基于代码图进行智能搜索
    支持符号搜索、引用搜索、调用链搜索等
    """
    
    def __init__(self, graph: CodeGraph):
        """
        初始化搜索器
        
        Args:
            graph: 代码图
        """
        self.graph = graph
    
    def search_symbol(
        self,
        query: str,
        symbol_type: Optional[str] = None,
        limit: int = 20
    ) -> List[SearchResult]:
        """
        搜索符号
        
        Args:
            query: 搜索词
            symbol_type: 符号类型过滤 (function/class/method)
            limit: 最大返回数量
            
        Returns:
            搜索结果列表
        """
        results = []
        query_lower = query.lower()
        
        for key, symbol in self.graph.symbols.items():
            # 类型过滤
            if symbol_type and symbol.type != symbol_type:
                continue
            
            name_lower = symbol.name.lower()
            score = 0
            match_type = ""
            
            # 精确匹配
            if name_lower == query_lower:
                score = 100
                match_type = "exact"
            # 前缀匹配
            elif name_lower.startswith(query_lower):
                score = 80
                match_type = "prefix"
            # 包含匹配
            elif query_lower in name_lower:
                score = 60
                match_type = "contains"
            # 模糊匹配（首字母）
            elif self._fuzzy_match(query_lower, name_lower):
                score = 40
                match_type = "fuzzy"
            else:
                continue
            
            results.append(SearchResult(
                symbol=symbol,
                score=score,
                match_type=match_type
            ))
        
        # 按分数排序
        results.sort(key=lambda r: r.score, reverse=True)
        return results[:limit]
    
    def search_definition(self, name: str) -> List[CodeSymbol]:
        """
        搜索定义位置
        
        Args:
            name: 符号名称
            
        Returns:
            定义符号列表
        """
        definitions = []
        for key, symbol in self.graph.symbols.items():
            if symbol.name == name or symbol.name.endswith(f".{name}"):
                definitions.append(symbol)
        return definitions
    
    def search_references(self, name: str) -> List[Dict[str, Any]]:
        """
        搜索引用
        
        Args:
            name: 符号名称
            
        Returns:
            引用位置列表
        """
        return self.graph.find_references(name)
    
    def search_callers(self, func_name: str) -> List[Dict[str, Any]]:
        """
        搜索调用者
        
        Args:
            func_name: 函数名
            
        Returns:
            调用者信息列表
        """
        callers = self.graph.find_callers(func_name)
        results = []
        
        for caller_key in callers:
            symbol = self.graph.symbols.get(caller_key)
            if symbol:
                results.append({
                    "name": symbol.name,
                    "file": symbol.file,
                    "line": symbol.line,
                    "type": symbol.type
                })
        
        return results
    
    def search_callees(self, func_name: str) -> List[Dict[str, Any]]:
        """
        搜索被调用函数
        
        Args:
            func_name: 函数名
            
        Returns:
            被调用函数信息列表
        """
        callees = self.graph.find_callees(func_name)
        results = []
        
        for callee_key in callees:
            # 尝试解析通配符
            name = callee_key.split("::")[-1]
            definitions = self.search_definition(name)
            
            if definitions:
                for d in definitions:
                    results.append({
                        "name": d.name,
                        "file": d.file,
                        "line": d.line,
                        "type": d.type
                    })
            else:
                results.append({
                    "name": name,
                    "file": "external",
                    "line": 0,
                    "type": "unknown"
                })
        
        return results
    
    def search_in_file(self, file: str) -> List[CodeSymbol]:
        """
        获取文件中的所有符号
        
        Args:
            file: 文件路径
            
        Returns:
            符号列表
        """
        return self.graph.get_file_symbols(file)
    
    def get_file_outline(self, file: str) -> Dict[str, Any]:
        """
        获取文件大纲
        
        Args:
            file: 文件路径
            
        Returns:
            文件大纲结构
        """
        symbols = self.search_in_file(file)
        
        outline = {
            "file": file,
            "imports": [],
            "classes": [],
            "functions": [],
            "variables": []
        }
        
        for symbol in symbols:
            if symbol.type == "class":
                class_info = {
                    "name": symbol.name,
                    "line": symbol.line,
                    "docstring": symbol.docstring,
                    "methods": []
                }
                # 查找方法
                for s in symbols:
                    if s.type == "method" and s.parent == symbol.name:
                        class_info["methods"].append({
                            "name": s.name.split(".")[-1],
                            "line": s.line
                        })
                outline["classes"].append(class_info)
            elif symbol.type == "function":
                outline["functions"].append({
                    "name": symbol.name,
                    "line": symbol.line,
                    "signature": symbol.signature,
                    "docstring": symbol.docstring
                })
        
        return outline
    
    def get_call_graph(self, func_name: str, depth: int = 2) -> Dict[str, Any]:
        """
        获取调用图
        
        Args:
            func_name: 起始函数名
            depth: 深度
            
        Returns:
            调用图结构
        """
        visited = set()
        
        def build_tree(name: str, current_depth: int) -> Dict[str, Any]:
            if current_depth > depth or name in visited:
                return {"name": name, "calls": []}
            
            visited.add(name)
            callees = self.search_callees(name)
            
            return {
                "name": name,
                "calls": [
                    build_tree(c["name"], current_depth + 1)
                    for c in callees
                    if c["name"] not in visited
                ]
            }
        
        return build_tree(func_name, 0)
    
    def _fuzzy_match(self, query: str, target: str) -> bool:
        """模糊匹配（驼峰/下划线首字母）"""
        # 提取目标的首字母
        initials = ""
        prev_lower = True
        for c in target:
            if c == '_':
                prev_lower = True
            elif c.isupper() and prev_lower:
                initials += c.lower()
                prev_lower = False
            elif prev_lower and c.isalpha():
                initials += c.lower()
                prev_lower = c.islower()
            else:
                prev_lower = c.islower()
        
        return query in initials
    
    def semantic_search(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        语义搜索（基于文档字符串）
        
        Args:
            query: 搜索词
            limit: 最大返回数量
            
        Returns:
            搜索结果
        """
        results = []
        query_lower = query.lower()
        
        for key, symbol in self.graph.symbols.items():
            score = 0
            
            # 检查名称
            if query_lower in symbol.name.lower():
                score += 50
            
            # 检查文档字符串
            if symbol.docstring:
                if query_lower in symbol.docstring.lower():
                    score += 30
            
            # 检查签名
            if symbol.signature and query_lower in symbol.signature.lower():
                score += 20
            
            if score > 0:
                results.append({
                    "name": symbol.name,
                    "type": symbol.type,
                    "file": symbol.file,
                    "line": symbol.line,
                    "score": score,
                    "docstring": symbol.docstring
                })
        
        results.sort(key=lambda r: r["score"], reverse=True)
        return results[:limit]


# ===== 便捷函数 =====

def create_searcher(workspace_path):
    """
    创建代码搜索器（自动索引）
    
    Args:
        workspace_path: 工作区路径
    
    Returns:
        CodeSearcher 实例
    """
    from .indexer import CodeIndexer
    
    indexer = CodeIndexer(workspace_path)
    graph = indexer.index()
    return CodeSearcher(graph)


def search(symbol_name: str, workspace_path = None) -> List[Dict[str, Any]]:
    """
    搜索符号（便捷函数）
    
    Args:
        symbol_name: 符号名称
        workspace_path: 工作区路径
    
    Returns:
        搜索结果列表
    """
    if workspace_path is None:
        return []
    
    try:
        searcher = create_searcher(workspace_path)
        results = searcher.search_symbol(symbol_name)
        
        return [
            {
                "name": r.symbol.name,
                "type": r.symbol.type,
                "file": r.symbol.file,
                "line": r.symbol.line,
                "signature": r.symbol.signature,
                "match_type": r.match_type
            }
            for r in results
        ]
    except Exception as e:
        return []


def get_references(file_path: str, symbol_name: str, workspace_path = None) -> List[Dict[str, Any]]:
    """
    获取符号引用（便捷函数）
    
    Args:
        file_path: 文件路径
        symbol_name: 符号名称
        workspace_path: 工作区路径
    
    Returns:
        引用列表
    """
    if workspace_path is None:
        return []
    
    try:
        searcher = create_searcher(workspace_path)
        refs = searcher.search_references(symbol_name)
        
        # 过滤当前文件的引用
        return [
            {
                "name": r["name"],
                "file": r["file"],
                "line": r["line"],
                "context": r.get("context", "")
            }
            for r in refs
            if file_path in r.get("file", "")
        ]
    except Exception as e:
        return []
