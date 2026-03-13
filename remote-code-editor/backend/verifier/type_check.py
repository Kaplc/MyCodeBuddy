"""
类型检查器
使用 mypy 进行静态类型检查
"""
import os
import subprocess
import tempfile
import re
from typing import Tuple, Optional, List, Dict, Any
from dataclasses import dataclass
from pathlib import Path


@dataclass
class TypeCheckError:
    """类型检查错误"""
    file: str
    line: int
    column: int
    severity: str  # error, warning, note
    message: str
    error_code: Optional[str] = None


@dataclass
class TypeCheckResult:
    """类型检查结果"""
    success: bool
    errors: List[TypeCheckError]
    warnings: List[TypeCheckError]
    notes: List[TypeCheckError]
    raw_output: str
    
    def to_dict(self) -> Dict[str, Any]:
        def error_to_dict(e: TypeCheckError) -> Dict:
            return {
                "file": e.file,
                "line": e.line,
                "column": e.column,
                "severity": e.severity,
                "message": e.message,
                "error_code": e.error_code
            }
        
        return {
            "success": self.success,
            "errors": [error_to_dict(e) for e in self.errors],
            "warnings": [error_to_dict(w) for w in self.warnings],
            "notes": [error_to_dict(n) for n in self.notes],
            "error_count": len(self.errors),
            "warning_count": len(self.warnings)
        }


class TypeChecker:
    """类型检查器 - 基于 mypy"""
    
    def __init__(self, python_version: str = "3.8"):
        self.python_version = python_version
        self.mypy_available = self._check_mypy_available()
        
        # mypy 配置选项
        self.mypy_options = [
            "--ignore-missing-imports",  # 忽略缺少的导入
            "--no-error-summary",        # 不显示错误摘要
            "--show-column-numbers",     # 显示列号
            "--show-error-codes",        # 显示错误代码
            f"--python-version={python_version}"
        ]
    
    def _check_mypy_available(self) -> bool:
        """检查 mypy 是否可用"""
        try:
            result = subprocess.run(
                ["mypy", "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0
        except:
            return False
    
    def check_code(self, code: str, filename: str = "code.py") -> TypeCheckResult:
        """
        检查代码的类型
        
        Args:
            code: 源代码字符串
            filename: 虚拟文件名
            
        Returns:
            TypeCheckResult: 类型检查结果
        """
        if not self.mypy_available:
            return TypeCheckResult(
                success=True,
                errors=[],
                warnings=[],
                notes=[],
                raw_output="mypy 未安装，跳过类型检查"
            )
        
        # 创建临时文件
        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.py',
            delete=False,
            encoding='utf-8'
        ) as f:
            f.write(code)
            temp_file = f.name
        
        try:
            # 运行 mypy
            cmd = ["mypy"] + self.mypy_options + [temp_file]
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            # 解析输出
            errors, warnings, notes = self._parse_output(
                result.stdout + result.stderr,
                temp_file,
                filename
            )
            
            return TypeCheckResult(
                success=len(errors) == 0,
                errors=errors,
                warnings=warnings,
                notes=notes,
                raw_output=result.stdout + result.stderr
            )
        
        finally:
            # 清理临时文件
            try:
                os.unlink(temp_file)
            except:
                pass
    
    def check_file(self, file_path: str) -> TypeCheckResult:
        """
        检查文件的类型
        
        Args:
            file_path: 文件路径
            
        Returns:
            TypeCheckResult: 类型检查结果
        """
        if not self.mypy_available:
            return TypeCheckResult(
                success=True,
                errors=[],
                warnings=[],
                notes=[],
                raw_output="mypy 未安装，跳过类型检查"
            )
        
        if not os.path.exists(file_path):
            return TypeCheckResult(
                success=False,
                errors=[TypeCheckError(
                    file=file_path,
                    line=0,
                    column=0,
                    severity="error",
                    message=f"文件不存在: {file_path}"
                )],
                warnings=[],
                notes=[],
                raw_output=f"文件不存在: {file_path}"
            )
        
        try:
            cmd = ["mypy"] + self.mypy_options + [file_path]
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            errors, warnings, notes = self._parse_output(
                result.stdout + result.stderr,
                file_path,
                file_path
            )
            
            return TypeCheckResult(
                success=len(errors) == 0,
                errors=errors,
                warnings=warnings,
                notes=notes,
                raw_output=result.stdout + result.stderr
            )
        
        except subprocess.TimeoutExpired:
            return TypeCheckResult(
                success=False,
                errors=[TypeCheckError(
                    file=file_path,
                    line=0,
                    column=0,
                    severity="error",
                    message="类型检查超时"
                )],
                warnings=[],
                notes=[],
                raw_output="类型检查超时（60秒）"
            )
    
    def _parse_output(
        self,
        output: str,
        temp_file: str,
        original_file: str
    ) -> Tuple[List[TypeCheckError], List[TypeCheckError], List[TypeCheckError]]:
        """
        解析 mypy 输出
        
        Args:
            output: mypy 输出
            temp_file: 临时文件路径（用于替换）
            original_file: 原始文件名
            
        Returns:
            (errors, warnings, notes)
        """
        errors = []
        warnings = []
        notes = []
        
        # mypy 输出格式: file:line:column: severity: message [error-code]
        pattern = r'^(.+?):(\d+):(\d+):\s*(error|warning|note):\s*(.+?)(?:\s*\[(.+?)\])?$'
        
        for line in output.strip().split('\n'):
            if not line.strip():
                continue
            
            match = re.match(pattern, line)
            if match:
                file_path = match.group(1)
                # 将临时文件路径替换为原始文件名
                if temp_file in file_path:
                    file_path = original_file
                
                error = TypeCheckError(
                    file=file_path,
                    line=int(match.group(2)),
                    column=int(match.group(3)),
                    severity=match.group(4),
                    message=match.group(5),
                    error_code=match.group(6)
                )
                
                if error.severity == "error":
                    errors.append(error)
                elif error.severity == "warning":
                    warnings.append(error)
                else:
                    notes.append(error)
        
        return errors, warnings, notes
    
    def get_type_hints(self, code: str) -> Dict[str, Any]:
        """
        分析代码中的类型提示
        
        Args:
            code: 源代码
            
        Returns:
            类型提示信息
        """
        import ast
        
        try:
            tree = ast.parse(code)
            hints = {
                "functions": [],
                "variables": [],
                "classes": []
            }
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    func_hints = {
                        "name": node.name,
                        "args": {},
                        "return": None
                    }
                    
                    # 参数类型
                    for arg in node.args.args:
                        if arg.annotation:
                            func_hints["args"][arg.arg] = ast.unparse(arg.annotation)
                    
                    # 返回类型
                    if node.returns:
                        func_hints["return"] = ast.unparse(node.returns)
                    
                    hints["functions"].append(func_hints)
                
                elif isinstance(node, ast.AnnAssign):
                    # 带类型注解的变量
                    if isinstance(node.target, ast.Name):
                        hints["variables"].append({
                            "name": node.target.id,
                            "type": ast.unparse(node.annotation) if node.annotation else None
                        })
            
            return hints
        
        except:
            return {"functions": [], "variables": [], "classes": []}


# 便捷函数
def type_check(file_or_code: str, is_file: bool = False) -> Tuple[bool, Optional[str]]:
    """
    简单类型检查
    
    Args:
        file_or_code: 文件路径或代码字符串
        is_file: 是否为文件路径
        
    Returns:
        (是否通过, 错误信息)
    """
    checker = TypeChecker()
    
    if is_file:
        result = checker.check_file(file_or_code)
    else:
        result = checker.check_code(file_or_code)
    
    if result.success:
        return True, None
    else:
        error_msg = "; ".join(
            f"Line {e.line}: {e.message}" 
            for e in result.errors
        )
        return False, error_msg
