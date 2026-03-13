"""
AST 语法检查器
使用 Python ast 模块进行语法分析
"""
import ast
import re
from typing import Tuple, Optional, Dict, Any, List
from dataclasses import dataclass


@dataclass
class SyntaxErrorInfo:
    """语法错误详情"""
    line: int
    column: int
    message: str
    code_snippet: Optional[str] = None


@dataclass
class ASTCheckResult:
    """AST 检查结果"""
    success: bool
    errors: List[SyntaxErrorInfo]
    warnings: List[str]
    ast_tree: Optional[ast.AST] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "errors": [
                {
                    "line": e.line,
                    "column": e.column,
                    "message": e.message,
                    "code_snippet": e.code_snippet
                }
                for e in self.errors
            ],
            "warnings": self.warnings
        }


class ASTChecker:
    """AST 语法检查器"""
    
    def __init__(self):
        self.common_fixes = {
            r"unexpected EOF": "代码不完整，可能缺少闭合括号或缩进",
            r"invalid syntax": "语法错误，检查括号、冒号、引号是否匹配",
            r"expected ':'": "缺少冒号，通常在 if/for/def/class 后面需要",
            r"unindent does not match": "缩进不一致，检查使用的是空格还是制表符",
        }
    
    def check_syntax(self, code: str, filename: str = "<code>") -> ASTCheckResult:
        """
        检查代码语法
        
        Args:
            code: 源代码字符串
            filename: 文件名（用于错误报告）
            
        Returns:
            ASTCheckResult: 检查结果
        """
        errors = []
        warnings = []
        ast_tree = None
        
        try:
            # 尝试解析 AST
            ast_tree = ast.parse(code, filename=filename)
            
            # 进行额外的静态检查
            warnings.extend(self._check_code_quality(ast_tree))
            
            return ASTCheckResult(
                success=True,
                errors=[],
                warnings=warnings,
                ast_tree=ast_tree
            )
            
        except Exception as e:
            # 处理语法错误
            lines = code.split('\n')
            code_snippet = None
            lineno = getattr(e, 'lineno', 0) or 0
            if lineno and 0 < lineno <= len(lines):
                code_snippet = lines[lineno - 1]
            
            error = SyntaxErrorInfo(
                line=lineno,
                column=getattr(e, 'offset', 0) or 0,
                message=str(getattr(e, 'msg', str(e))),
                code_snippet=code_snippet
            )
            errors.append(error)
            
            # 添加修复建议
            suggestion = self._get_fix_suggestion(str(e))
            if suggestion:
                warnings.append(f"修复建议: {suggestion}")
            
            return ASTCheckResult(
                success=False,
                errors=errors,
                warnings=warnings
            )
    
    def _check_code_quality(self, tree: ast.AST) -> List[str]:
        """检查代码质量问题"""
        warnings = []
        
        for node in ast.walk(tree):
            # 检查未使用的变量
            if isinstance(node, ast.Name) and node.id.startswith('_'):
                if isinstance(node.ctx, ast.Store):
                    warnings.append(f"变量 '{node.id}' 以下划线开头但被赋值")
            
            # 检查过长的函数
            if isinstance(node, ast.FunctionDef):
                body_lines = node.end_lineno - node.lineno if node.end_lineno else 0
                if body_lines > 50:
                    warnings.append(
                        f"函数 '{node.name}' 有 {body_lines} 行，"
                        "建议拆分成更小的函数"
                    )
                    
            # 检查过深的嵌套
            if isinstance(node, (ast.If, ast.For, ast.While)):
                depth = self._get_nesting_depth(node)
                if depth > 4:
                    warnings.append(
                        f"第 {node.lineno} 行嵌套深度为 {depth}，"
                        "建议重构以降低复杂度"
                    )
        
        return warnings
    
    def _get_nesting_depth(self, node: ast.AST, current_depth: int = 0) -> int:
        """计算嵌套深度"""
        max_depth = current_depth
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.If, ast.For, ast.While, ast.Try)):
                child_depth = self._get_nesting_depth(child, current_depth + 1)
                max_depth = max(max_depth, child_depth)
        return max_depth
    
    def _get_fix_suggestion(self, error_msg: str) -> Optional[str]:
        """根据错误信息获取修复建议"""
        for pattern, suggestion in self.common_fixes.items():
            if re.search(pattern, error_msg, re.IGNORECASE):
                return suggestion
        return None
    
    def extract_functions(self, code: str) -> List[Dict[str, Any]]:
        """
        提取代码中的函数定义
        
        Args:
            code: 源代码
            
        Returns:
            函数定义列表
        """
        try:
            tree = ast.parse(code)
            functions = []
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    # 提取参数
                    args = []
                    for arg in node.args.args:
                        arg_info = {"name": arg.arg}
                        if arg.annotation:
                            arg_info["type"] = ast.unparse(arg.annotation)
                        args.append(arg_info)
                    
                    # 提取返回类型
                    return_type = None
                    if node.returns:
                        return_type = ast.unparse(node.returns)
                    
                    # 提取文档字符串
                    docstring = ast.get_docstring(node)
                    
                    functions.append({
                        "name": node.name,
                        "args": args,
                        "return_type": return_type,
                        "docstring": docstring,
                        "line": node.lineno,
                        "end_line": node.end_lineno
                    })
            
            return functions
        except:
            return []
    
    def extract_classes(self, code: str) -> List[Dict[str, Any]]:
        """
        提取代码中的类定义
        
        Args:
            code: 源代码
            
        Returns:
            类定义列表
        """
        try:
            tree = ast.parse(code)
            classes = []
            
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    # 提取基类
                    bases = [ast.unparse(base) for base in node.bases]
                    
                    # 提取方法
                    methods = []
                    for item in node.body:
                        if isinstance(item, ast.FunctionDef):
                            methods.append(item.name)
                    
                    # 提取文档字符串
                    docstring = ast.get_docstring(node)
                    
                    classes.append({
                        "name": node.name,
                        "bases": bases,
                        "methods": methods,
                        "docstring": docstring,
                        "line": node.lineno,
                        "end_line": node.end_lineno
                    })
            
            return classes
        except:
            return []
    
    def extract_imports(self, code: str) -> List[Dict[str, Any]]:
        """
        提取代码中的导入语句
        
        Args:
            code: 源代码
            
        Returns:
            导入语句列表
        """
        try:
            tree = ast.parse(code)
            imports = []
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append({
                            "type": "import",
                            "module": alias.name,
                            "alias": alias.asname,
                            "line": node.lineno
                        })
                elif isinstance(node, ast.ImportFrom):
                    for alias in node.names:
                        imports.append({
                            "type": "from",
                            "module": node.module or "",
                            "name": alias.name,
                            "alias": alias.asname,
                            "line": node.lineno
                        })
            
            return imports
        except:
            return []


# 便捷函数
def check_syntax(code: str) -> Tuple[bool, Optional[str]]:
    """
    简单语法检查
    
    Args:
        code: 源代码
        
    Returns:
        (是否通过, 错误信息)
    """
    checker = ASTChecker()
    result = checker.check_syntax(code)
    
    if result.success:
        return True, None
    else:
        error_msg = "; ".join(
            f"Line {e.line}: {e.message}" 
            for e in result.errors
        )
        return False, error_msg
