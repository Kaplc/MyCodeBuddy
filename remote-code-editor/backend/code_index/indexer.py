"""
代码索引器
扫描项目并构建代码图
"""
import os
import ast
import sys
from typing import List, Set, Optional
from pathlib import Path
from .code_graph import CodeGraph, CodeSymbol, CodeEdge


# Python 3.8 兼容：ast.unparse
if sys.version_info >= (3, 9):
    ast_unparse = ast.unparse
else:
    try:
        import astunparse
        ast_unparse = astunparse.unparse
    except ImportError:
        def ast_unparse(node):
            """简单的 AST 反解析（Python 3.8 兼容）"""
            if isinstance(node, ast.Name):
                return node.id
            elif isinstance(node, ast.Attribute):
                return f"{ast_unparse(node.value)}.{node.attr}"
            elif isinstance(node, ast.Subscript):
                return f"{ast_unparse(node.value)}[{ast_unparse(node.slice)}]"
            elif isinstance(node, ast.Constant):
                return repr(node.value)
            elif isinstance(node, ast.Tuple):
                return f"({', '.join(ast_unparse(e) for e in node.elts)})"
            elif isinstance(node, ast.List):
                return f"[{', '.join(ast_unparse(e) for e in node.elts)}]"
            elif isinstance(node, ast.Index):  # Python 3.8
                return ast_unparse(node.value)
            else:
                return "..."


class CodeIndexer:
    """
    代码索引器
    
    扫描项目目录，解析 Python 文件，构建代码图
    """
    
    # 忽略的目录
    IGNORE_DIRS = {
        '.git', '__pycache__', 'node_modules', '.venv', 'venv',
        'dist', 'build', '.eggs', '*.egg-info', '.tox', '.mypy_cache'
    }
    
    # 支持的文件扩展名
    SUPPORTED_EXTENSIONS = {'.py'}
    
    def __init__(self, workspace_path: str):
        """
        初始化索引器
        
        Args:
            workspace_path: 工作区路径
        """
        self.workspace = Path(workspace_path).resolve()
        self.graph = CodeGraph()
    
    def index(self, incremental: bool = False) -> CodeGraph:
        """
        索引整个项目
        
        Args:
            incremental: 是否增量索引
            
        Returns:
            构建的代码图
        """
        if not incremental:
            self.graph = CodeGraph()
        
        # 遍历所有 Python 文件
        for file_path in self._iter_python_files():
            try:
                self._index_file(file_path)
            except Exception as e:
                print(f"索引文件失败 {file_path}: {e}")
        
        return self.graph
    
    def index_file(self, file_path: str) -> CodeGraph:
        """索引单个文件"""
        self._index_file(Path(file_path))
        return self.graph
    
    def _iter_python_files(self):
        """遍历所有 Python 文件"""
        for root, dirs, files in os.walk(self.workspace):
            # 过滤忽略的目录
            dirs[:] = [d for d in dirs if d not in self.IGNORE_DIRS]
            
            for file in files:
                if Path(file).suffix in self.SUPPORTED_EXTENSIONS:
                    yield Path(root) / file
    
    def _index_file(self, file_path: Path):
        """索引单个文件"""
        try:
            content = file_path.read_text(encoding='utf-8')
            tree = ast.parse(content, filename=str(file_path))
        except (SyntaxError, UnicodeDecodeError):
            return
        
        rel_path = str(file_path.relative_to(self.workspace))
        
        # 第一遍：收集所有符号
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                self._add_function(node, rel_path)
            elif isinstance(node, ast.AsyncFunctionDef):
                self._add_function(node, rel_path, is_async=True)
            elif isinstance(node, ast.ClassDef):
                self._add_class(node, rel_path)
            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                self._add_import(node, rel_path)
        
        # 第二遍：分析调用关系
        analyzer = CallAnalyzer(rel_path, self.graph)
        analyzer.visit(tree)
    
    def _add_function(self, node: ast.FunctionDef, file: str, is_async: bool = False):
        """添加函数符号"""
        # 构建签名
        args = []
        for arg in node.args.args:
            arg_str = arg.arg
            if arg.annotation:
                arg_str += f": {ast_unparse(arg.annotation)}"
            args.append(arg_str)
        
        signature = f"{'async ' if is_async else ''}def {node.name}({', '.join(args)})"
        if node.returns:
            signature += f" -> {ast_unparse(node.returns)}"
        
        symbol = CodeSymbol(
            name=node.name,
            type="function",
            file=file,
            line=node.lineno,
            end_line=node.end_lineno or node.lineno,
            signature=signature,
            docstring=ast.get_docstring(node)
        )
        self.graph.add_symbol(symbol)
    
    def _add_class(self, node: ast.ClassDef, file: str):
        """添加类符号"""
        # 获取基类
        bases = [ast_unparse(base) for base in node.bases]
        signature = f"class {node.name}"
        if bases:
            signature += f"({', '.join(bases)})"
        
        symbol = CodeSymbol(
            name=node.name,
            type="class",
            file=file,
            line=node.lineno,
            end_line=node.end_lineno or node.lineno,
            signature=signature,
            docstring=ast.get_docstring(node)
        )
        self.graph.add_symbol(symbol)
        
        # 添加继承关系
        for base in bases:
            self.graph.add_edge(CodeEdge(
                source=f"{file}::{node.name}",
                target=f"*::{base}",  # * 表示需要解析
                type="inherits"
            ))
        
        # 添加方法
        for item in node.body:
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                method_symbol = CodeSymbol(
                    name=f"{node.name}.{item.name}",
                    type="method",
                    file=file,
                    line=item.lineno,
                    end_line=item.end_lineno or item.lineno,
                    signature=f"def {item.name}(...)",
                    docstring=ast.get_docstring(item),
                    parent=node.name
                )
                self.graph.add_symbol(method_symbol)
    
    def _add_import(self, node, file: str):
        """添加导入"""
        if isinstance(node, ast.Import):
            for alias in node.names:
                self.graph.imports_map[file].add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            for alias in node.names:
                self.graph.imports_map[file].add(f"{module}.{alias.name}")


class CallAnalyzer(ast.NodeVisitor):
    """调用关系分析器"""
    
    def __init__(self, file: str, graph: CodeGraph):
        self.file = file
        self.graph = graph
        self.current_function: Optional[str] = None
    
    def visit_FunctionDef(self, node: ast.FunctionDef):
        """访问函数定义"""
        old_func = self.current_function
        self.current_function = node.name
        self.generic_visit(node)
        self.current_function = old_func
    
    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        """访问异步函数定义"""
        old_func = self.current_function
        self.current_function = node.name
        self.generic_visit(node)
        self.current_function = old_func
    
    def visit_Call(self, node: ast.Call):
        """访问函数调用"""
        if self.current_function:
            callee = self._get_call_name(node)
            if callee:
                self.graph.add_edge(CodeEdge(
                    source=f"{self.file}::{self.current_function}",
                    target=f"*::{callee}",
                    type="calls"
                ))
        self.generic_visit(node)
    
    def _get_call_name(self, node: ast.Call) -> Optional[str]:
        """获取调用的函数名"""
        if isinstance(node.func, ast.Name):
            return node.func.id
        elif isinstance(node.func, ast.Attribute):
            return node.func.attr
        return None
