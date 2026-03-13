"""
静态代码分析器
使用 pylint 和内置规则进行代码质量检查
"""
import os
import subprocess
import tempfile
import re
import ast
from typing import Tuple, Optional, List, Dict, Any
from dataclasses import dataclass


@dataclass
class LintIssue:
    """Lint 问题"""
    file: str
    line: int
    column: int
    code: str  # 错误代码，如 E0001, W0611
    symbol: str  # 错误符号，如 syntax-error, unused-import
    message: str
    category: str  # convention, refactor, warning, error, fatal


@dataclass
class LintResult:
    """Lint 检查结果"""
    success: bool
    score: float  # pylint 评分 (0-10)
    issues: List[LintIssue]
    summary: Dict[str, int]  # 各类问题统计
    raw_output: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "score": self.score,
            "issues": [
                {
                    "file": i.file,
                    "line": i.line,
                    "column": i.column,
                    "code": i.code,
                    "symbol": i.symbol,
                    "message": i.message,
                    "category": i.category
                }
                for i in self.issues
            ],
            "summary": self.summary,
            "issue_count": len(self.issues)
        }


class LintChecker:
    """静态代码分析器"""
    
    def __init__(self, min_score: float = 7.0):
        """
        初始化 Lint 检查器
        
        Args:
            min_score: 最低通过分数 (0-10)
        """
        self.min_score = min_score
        self.pylint_available = self._check_pylint_available()
        
        # pylint 配置
        self.pylint_options = [
            "--output-format=text",
            "--reports=n",  # 不生成报告
            "--score=y",    # 显示评分
            "--msg-template={path}:{line}:{column}: {msg_id} ({symbol}) {msg}",
            # 禁用一些过于严格的检查
            "--disable=C0114,C0115,C0116",  # 缺少文档字符串
            "--disable=C0103",  # 变量命名不符合规范
            "--disable=R0903",  # 类方法太少
        ]
        
        # 内置检查规则
        self.builtin_rules = [
            self._check_print_statements,
            self._check_hardcoded_passwords,
            self._check_eval_usage,
            self._check_star_imports,
            self._check_mutable_defaults,
        ]
    
    def _check_pylint_available(self) -> bool:
        """检查 pylint 是否可用"""
        try:
            result = subprocess.run(
                ["pylint", "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0
        except:
            return False
    
    def check_code(self, code: str, filename: str = "code.py") -> LintResult:
        """
        检查代码质量
        
        Args:
            code: 源代码字符串
            filename: 虚拟文件名
            
        Returns:
            LintResult: Lint 检查结果
        """
        all_issues = []
        
        # 1. 运行内置检查
        builtin_issues = self._run_builtin_checks(code, filename)
        all_issues.extend(builtin_issues)
        
        # 2. 运行 pylint（如果可用）
        if self.pylint_available:
            pylint_result = self._run_pylint(code, filename)
            all_issues.extend(pylint_result["issues"])
            score = pylint_result["score"]
            raw_output = pylint_result["raw_output"]
        else:
            # 如果 pylint 不可用，根据内置检查结果计算分数
            score = max(0, 10 - len(builtin_issues) * 0.5)
            raw_output = "pylint 未安装，仅使用内置检查"
        
        # 统计问题
        summary = {
            "convention": 0,
            "refactor": 0,
            "warning": 0,
            "error": 0,
            "fatal": 0
        }
        for issue in all_issues:
            if issue.category in summary:
                summary[issue.category] += 1
        
        return LintResult(
            success=score >= self.min_score and summary["error"] == 0 and summary["fatal"] == 0,
            score=score,
            issues=all_issues,
            summary=summary,
            raw_output=raw_output
        )
    
    def check_file(self, file_path: str) -> LintResult:
        """
        检查文件代码质量
        
        Args:
            file_path: 文件路径
            
        Returns:
            LintResult: Lint 检查结果
        """
        if not os.path.exists(file_path):
            return LintResult(
                success=False,
                score=0,
                issues=[LintIssue(
                    file=file_path,
                    line=0,
                    column=0,
                    code="E0001",
                    symbol="file-not-found",
                    message=f"文件不存在: {file_path}",
                    category="fatal"
                )],
                summary={"fatal": 1},
                raw_output=f"文件不存在: {file_path}"
            )
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                code = f.read()
            return self.check_code(code, file_path)
        except Exception as e:
            return LintResult(
                success=False,
                score=0,
                issues=[LintIssue(
                    file=file_path,
                    line=0,
                    column=0,
                    code="E0001",
                    symbol="read-error",
                    message=f"无法读取文件: {str(e)}",
                    category="fatal"
                )],
                summary={"fatal": 1},
                raw_output=f"无法读取文件: {str(e)}"
            )
    
    def _run_pylint(self, code: str, filename: str) -> Dict[str, Any]:
        """运行 pylint"""
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
            cmd = ["pylint"] + self.pylint_options + [temp_file]
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            issues = self._parse_pylint_output(
                result.stdout + result.stderr,
                temp_file,
                filename
            )
            
            # 提取评分
            score = self._extract_score(result.stdout + result.stderr)
            
            return {
                "issues": issues,
                "score": score,
                "raw_output": result.stdout + result.stderr
            }
        
        finally:
            try:
                os.unlink(temp_file)
            except:
                pass
    
    def _parse_pylint_output(
        self,
        output: str,
        temp_file: str,
        original_file: str
    ) -> List[LintIssue]:
        """解析 pylint 输出"""
        issues = []
        
        # 格式: file:line:column: CODE (symbol) message
        pattern = r'^(.+?):(\d+):(\d+):\s*([A-Z]\d{4})\s*\(([^)]+)\)\s*(.+)$'
        
        for line in output.strip().split('\n'):
            if not line.strip():
                continue
            
            match = re.match(pattern, line)
            if match:
                file_path = match.group(1)
                if temp_file in file_path:
                    file_path = original_file
                
                code = match.group(4)
                category = self._get_category_from_code(code)
                
                issues.append(LintIssue(
                    file=file_path,
                    line=int(match.group(2)),
                    column=int(match.group(3)),
                    code=code,
                    symbol=match.group(5),
                    message=match.group(6),
                    category=category
                ))
        
        return issues
    
    def _get_category_from_code(self, code: str) -> str:
        """根据错误代码获取类别"""
        if code.startswith('C'):
            return "convention"
        elif code.startswith('R'):
            return "refactor"
        elif code.startswith('W'):
            return "warning"
        elif code.startswith('E'):
            return "error"
        elif code.startswith('F'):
            return "fatal"
        return "warning"
    
    def _extract_score(self, output: str) -> float:
        """从输出中提取评分"""
        # 格式: Your code has been rated at X.XX/10
        match = re.search(r'rated at (-?\d+\.?\d*)/10', output)
        if match:
            return float(match.group(1))
        return 10.0  # 如果没找到评分，默认满分
    
    def _run_builtin_checks(self, code: str, filename: str) -> List[LintIssue]:
        """运行内置检查"""
        issues = []
        for check in self.builtin_rules:
            issues.extend(check(code, filename))
        return issues
    
    def _check_print_statements(self, code: str, filename: str) -> List[LintIssue]:
        """检查 print 语句（生产代码中不建议使用）"""
        issues = []
        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Name) and node.func.id == 'print':
                        issues.append(LintIssue(
                            file=filename,
                            line=node.lineno,
                            column=node.col_offset,
                            code="W0101",
                            symbol="print-statement",
                            message="使用 print 语句，建议使用 logging 模块",
                            category="warning"
                        ))
        except:
            pass
        return issues
    
    def _check_hardcoded_passwords(self, code: str, filename: str) -> List[LintIssue]:
        """检查硬编码密码"""
        issues = []
        password_patterns = [
            r'password\s*=\s*["\'][^"\']+["\']',
            r'passwd\s*=\s*["\'][^"\']+["\']',
            r'secret\s*=\s*["\'][^"\']+["\']',
            r'api_key\s*=\s*["\'][^"\']+["\']',
        ]
        
        for i, line in enumerate(code.split('\n'), 1):
            for pattern in password_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    issues.append(LintIssue(
                        file=filename,
                        line=i,
                        column=0,
                        code="W0901",
                        symbol="hardcoded-password",
                        message="检测到硬编码的敏感信息，建议使用环境变量",
                        category="warning"
                    ))
                    break
        
        return issues
    
    def _check_eval_usage(self, code: str, filename: str) -> List[LintIssue]:
        """检查 eval/exec 使用"""
        issues = []
        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Name):
                        if node.func.id in ('eval', 'exec'):
                            issues.append(LintIssue(
                                file=filename,
                                line=node.lineno,
                                column=node.col_offset,
                                code="W0902",
                                symbol="eval-used",
                                message=f"使用 {node.func.id}() 存在安全风险",
                                category="warning"
                            ))
        except:
            pass
        return issues
    
    def _check_star_imports(self, code: str, filename: str) -> List[LintIssue]:
        """检查 * 导入"""
        issues = []
        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom):
                    for alias in node.names:
                        if alias.name == '*':
                            issues.append(LintIssue(
                                file=filename,
                                line=node.lineno,
                                column=node.col_offset,
                                code="W0401",
                                symbol="wildcard-import",
                                message=f"使用通配符导入 from {node.module} import *",
                                category="warning"
                            ))
        except:
            pass
        return issues
    
    def _check_mutable_defaults(self, code: str, filename: str) -> List[LintIssue]:
        """检查可变默认参数"""
        issues = []
        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    for default in node.args.defaults + node.args.kw_defaults:
                        if default and isinstance(default, (ast.List, ast.Dict, ast.Set)):
                            issues.append(LintIssue(
                                file=filename,
                                line=node.lineno,
                                column=node.col_offset,
                                code="W0102",
                                symbol="dangerous-default-value",
                                message=f"函数 {node.name} 使用可变默认参数，这可能导致意外行为",
                                category="warning"
                            ))
        except:
            pass
        return issues


# 便捷函数
def lint_check(file_or_code: str, is_file: bool = False) -> Tuple[bool, Optional[str]]:
    """
    简单 Lint 检查
    
    Args:
        file_or_code: 文件路径或代码字符串
        is_file: 是否为文件路径
        
    Returns:
        (是否通过, 错误信息)
    """
    checker = LintChecker()
    
    if is_file:
        result = checker.check_file(file_or_code)
    else:
        result = checker.check_code(file_or_code)
    
    if result.success:
        return True, None
    else:
        # 只返回 error 和 fatal 级别的问题
        serious_issues = [
            i for i in result.issues 
            if i.category in ('error', 'fatal')
        ]
        if serious_issues:
            error_msg = "; ".join(
                f"Line {i.line}: [{i.code}] {i.message}" 
                for i in serious_issues[:5]  # 最多显示5个
            )
            return False, error_msg
        
        # 如果只有警告，也返回但标记为通过
        return True, f"评分: {result.score}/10，有 {len(result.issues)} 个警告"
