"""
运行时测试执行器
自动生成和执行测试用例
"""
import os
import subprocess
import tempfile
import re
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass


@dataclass
class TestCase:
    """测试用例"""
    name: str
    code: str
    expected: Optional[str] = None


@dataclass
class TestResult:
    """测试结果"""
    test_name: str
    passed: bool
    output: str
    error: Optional[str] = None
    duration: float = 0


@dataclass
class RuntimeTestResult:
    """运行时测试总结果"""
    success: bool
    total: int
    passed: int
    failed: int
    results: List[TestResult]
    coverage: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "total": self.total,
            "passed": self.passed,
            "failed": self.failed,
            "pass_rate": f"{self.passed}/{self.total}",
            "results": [
                {
                    "name": r.test_name,
                    "passed": r.passed,
                    "error": r.error
                }
                for r in self.results
            ]
        }


class RuntimeTester:
    """运行时测试执行器"""
    
    def __init__(self, timeout: int = 30):
        self.timeout = timeout
        self.pytest_available = self._check_pytest()
    
    def _check_pytest(self) -> bool:
        """检查 pytest 是否可用"""
        try:
            result = subprocess.run(
                ["pytest", "--version"],
                capture_output=True,
                timeout=10
            )
            return result.returncode == 0
        except:
            return False
    
    def run_tests(self, test_code: str, source_code: str = "") -> RuntimeTestResult:
        """
        运行测试代码
        
        Args:
            test_code: 测试代码
            source_code: 被测试的源代码（可选）
        """
        # 创建临时目录
        with tempfile.TemporaryDirectory() as tmpdir:
            # 写入源代码
            if source_code:
                source_file = os.path.join(tmpdir, "module.py")
                with open(source_file, 'w', encoding='utf-8') as f:
                    f.write(source_code)
            
            # 写入测试代码
            test_file = os.path.join(tmpdir, "test_module.py")
            full_test_code = test_code
            if source_code:
                full_test_code = "from module import *\n\n" + test_code
            
            with open(test_file, 'w', encoding='utf-8') as f:
                f.write(full_test_code)
            
            # 运行测试
            if self.pytest_available:
                return self._run_pytest(tmpdir)
            else:
                return self._run_simple_tests(test_file, full_test_code)
    
    def _run_pytest(self, test_dir: str) -> RuntimeTestResult:
        """使用 pytest 运行测试"""
        try:
            result = subprocess.run(
                ["pytest", test_dir, "-v", "--tb=short"],
                capture_output=True,
                text=True,
                timeout=self.timeout
            )
            
            return self._parse_pytest_output(result.stdout + result.stderr)
            
        except subprocess.TimeoutExpired:
            return RuntimeTestResult(
                success=False,
                total=0,
                passed=0,
                failed=1,
                results=[TestResult("timeout", False, "", "测试超时")]
            )
        except Exception as e:
            return RuntimeTestResult(
                success=False,
                total=0,
                passed=0,
                failed=1,
                results=[TestResult("error", False, "", str(e))]
            )
    
    def _parse_pytest_output(self, output: str) -> RuntimeTestResult:
        """解析 pytest 输出"""
        results = []
        
        # 解析单个测试结果
        test_pattern = r'(\S+::\S+)\s+(PASSED|FAILED|ERROR|SKIPPED)'
        for match in re.finditer(test_pattern, output):
            test_name = match.group(1)
            status = match.group(2)
            results.append(TestResult(
                test_name=test_name,
                passed=status == "PASSED",
                output="",
                error=None if status == "PASSED" else status
            ))
        
        # 提取总计
        summary_match = re.search(r'(\d+) passed', output)
        passed = int(summary_match.group(1)) if summary_match else 0
        
        failed_match = re.search(r'(\d+) failed', output)
        failed = int(failed_match.group(1)) if failed_match else 0
        
        total = passed + failed
        
        return RuntimeTestResult(
            success=failed == 0 and total > 0,
            total=total,
            passed=passed,
            failed=failed,
            results=results
        )
    
    def _run_simple_tests(self, test_file: str, test_code: str) -> RuntimeTestResult:
        """简单测试运行（不用 pytest）"""
        try:
            result = subprocess.run(
                ["python", test_file],
                capture_output=True,
                text=True,
                timeout=self.timeout
            )
            
            if result.returncode == 0:
                return RuntimeTestResult(
                    success=True,
                    total=1,
                    passed=1,
                    failed=0,
                    results=[TestResult("all", True, result.stdout)]
                )
            else:
                return RuntimeTestResult(
                    success=False,
                    total=1,
                    passed=0,
                    failed=1,
                    results=[TestResult("all", False, result.stdout, result.stderr)]
                )
                
        except Exception as e:
            return RuntimeTestResult(
                success=False,
                total=1,
                passed=0,
                failed=1,
                results=[TestResult("error", False, "", str(e))]
            )
    
    def generate_basic_tests(self, code: str) -> str:
        """
        为代码生成基本测试用例
        
        Args:
            code: 源代码
            
        Returns:
            测试代码
        """
        import ast
        
        tests = ["import pytest\n"]
        
        try:
            tree = ast.parse(code)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    func_name = node.name
                    args = [arg.arg for arg in node.args.args]
                    
                    # 生成基本测试
                    test_code = f'''
def test_{func_name}_basic():
    """测试 {func_name} 基本功能"""
    # TODO: 添加具体测试
    pass

def test_{func_name}_edge_cases():
    """测试 {func_name} 边界情况"""
    # TODO: 添加边界测试
    pass
'''
                    tests.append(test_code)
            
            return "\n".join(tests)
        except:
            return "# 无法解析代码生成测试\n"


def run_tests(test_code: str, source_code: str = "") -> Tuple[bool, Optional[str]]:
    """便捷函数：运行测试"""
    tester = RuntimeTester()
    result = tester.run_tests(test_code, source_code)
    
    if result.success:
        return True, f"通过 {result.passed}/{result.total} 个测试"
    else:
        errors = [r.error for r in result.results if r.error]
        return False, f"失败 {result.failed}/{result.total}: {'; '.join(errors[:3])}"


def generate_tests_for_code(code: str, test_framework: str = "pytest") -> str:
    """
    为代码生成测试用例
    
    Args:
        code: 源代码
        test_framework: 测试框架 (pytest/unittest)
    
    Returns:
        生成的测试代码
    """
    tester = RuntimeTester()
    return tester.generate_basic_tests(code)


def run_pytest(workspace_path, test_path: str = ".", verbose: bool = True) -> Dict[str, Any]:
    """
    运行 pytest 测试
    
    Args:
        workspace_path: 工作区路径
        test_path: 测试路径
        verbose: 是否详细输出
    
    Returns:
        测试结果字典
    """
    import subprocess
    
    args = ["pytest"]
    if verbose:
        args.append("-v")
    args.append("--tb=short")
    args.append(test_path)
    
    try:
        result = subprocess.run(
            args,
            cwd=str(workspace_path),
            capture_output=True,
            text=True,
            timeout=60
        )
        
        output = result.stdout + result.stderr
        
        # 解析结果
        passed_match = re.search(r'(\d+) passed', output)
        failed_match = re.search(r'(\d+) failed', output)
        
        passed = int(passed_match.group(1)) if passed_match else 0
        failed = int(failed_match.group(1)) if failed_match else 0
        
        return {
            "success": result.returncode == 0,
            "return_code": result.returncode,
            "output": output[:5000],  # 限制输出长度
            "passed": passed,
            "failed": failed,
            "summary": f"{passed} passed, {failed} failed"
        }
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "return_code": -1,
            "output": "测试超时",
            "summary": "测试超时"
        }
    except Exception as e:
        return {
            "success": False,
            "return_code": -1,
            "output": str(e),
            "summary": f"错误: {str(e)}"
        }
