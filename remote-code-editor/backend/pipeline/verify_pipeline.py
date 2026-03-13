"""
验证流水线
统一管理所有验证步骤
"""
import time
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

from verifier.ast_check import ASTChecker, check_syntax
from verifier.type_check import TypeChecker, type_check
from verifier.lint_check import LintChecker, lint_check
from verifier.symbolic_exec import SymbolicExecutor, symbolic_analyze
from verifier.z3_verify import Z3Verifier
from verifier.runtime_test import RuntimeTester, run_tests


class VerifyStage(Enum):
    """验证阶段"""
    SYNTAX = "syntax"
    TYPE = "type"
    LINT = "lint"
    SYMBOLIC = "symbolic"
    Z3 = "z3"
    RUNTIME = "runtime"


@dataclass
class StageResult:
    """单个阶段的结果"""
    stage: VerifyStage
    passed: bool
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    duration: float = 0
    skipped: bool = False


@dataclass
class PipelineResult:
    """流水线执行结果"""
    success: bool
    stages: List[StageResult]
    total_duration: float
    failed_stage: Optional[VerifyStage] = None
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "total_duration": f"{self.total_duration:.2f}s",
            "failed_stage": self.failed_stage.value if self.failed_stage else None,
            "error_message": self.error_message,
            "stages": [
                {
                    "stage": s.stage.value,
                    "passed": s.passed,
                    "message": s.message,
                    "duration": f"{s.duration:.2f}s",
                    "skipped": s.skipped
                }
                for s in self.stages
            ]
        }


class VerifyPipeline:
    """
    验证流水线
    
    执行顺序：
    1. AST 语法检查
    2. 类型检查
    3. 静态分析 (Lint)
    4. 符号执行
    5. Z3 验证（可选）
    6. 运行时测试（可选）
    """
    
    def __init__(
        self,
        enable_type_check: bool = True,
        enable_lint: bool = True,
        enable_symbolic: bool = True,
        enable_z3: bool = False,
        enable_runtime: bool = False,
        lint_min_score: float = 7.0,
        timeout: int = 60
    ):
        """
        初始化验证流水线
        
        Args:
            enable_type_check: 是否启用类型检查
            enable_lint: 是否启用静态分析
            enable_symbolic: 是否启用符号执行
            enable_z3: 是否启用 Z3 验证
            enable_runtime: 是否启用运行时测试
            lint_min_score: Lint 最低通过分数
            timeout: 超时时间（秒）
        """
        self.enable_type_check = enable_type_check
        self.enable_lint = enable_lint
        self.enable_symbolic = enable_symbolic
        self.enable_z3 = enable_z3
        self.enable_runtime = enable_runtime
        self.lint_min_score = lint_min_score
        self.timeout = timeout
        
        # 初始化检查器
        self.ast_checker = ASTChecker()
        self.type_checker = TypeChecker()
        self.lint_checker = LintChecker(min_score=lint_min_score)
        self.symbolic_executor = SymbolicExecutor()
        self.z3_verifier = Z3Verifier()
        self.runtime_tester = RuntimeTester(timeout=timeout)
    
    def run(
        self,
        code: str,
        test_code: Optional[str] = None,
        z3_spec: Optional[Dict[str, Any]] = None
    ) -> PipelineResult:
        """
        运行验证流水线
        
        Args:
            code: 源代码
            test_code: 测试代码（用于运行时测试）
            z3_spec: Z3 验证规约
            
        Returns:
            PipelineResult: 验证结果
        """
        start_time = time.time()
        stages: List[StageResult] = []
        
        # 1. 语法检查（必须）
        stage_result = self._run_syntax_check(code)
        stages.append(stage_result)
        if not stage_result.passed:
            return self._build_result(stages, start_time, VerifyStage.SYNTAX, stage_result.message)
        
        # 2. 类型检查
        if self.enable_type_check:
            stage_result = self._run_type_check(code)
            stages.append(stage_result)
            if not stage_result.passed:
                return self._build_result(stages, start_time, VerifyStage.TYPE, stage_result.message)
        
        # 3. 静态分析
        if self.enable_lint:
            stage_result = self._run_lint_check(code)
            stages.append(stage_result)
            if not stage_result.passed:
                return self._build_result(stages, start_time, VerifyStage.LINT, stage_result.message)
        
        # 4. 符号执行
        if self.enable_symbolic:
            stage_result = self._run_symbolic_analysis(code)
            stages.append(stage_result)
            # 符号执行的警告不阻止流水线
        
        # 5. Z3 验证
        if self.enable_z3 and z3_spec:
            stage_result = self._run_z3_verify(code, z3_spec)
            stages.append(stage_result)
            if not stage_result.passed:
                return self._build_result(stages, start_time, VerifyStage.Z3, stage_result.message)
        
        # 6. 运行时测试
        if self.enable_runtime and test_code:
            stage_result = self._run_runtime_tests(code, test_code)
            stages.append(stage_result)
            if not stage_result.passed:
                return self._build_result(stages, start_time, VerifyStage.RUNTIME, stage_result.message)
        
        # 全部通过
        return self._build_result(stages, start_time)
    
    def _run_syntax_check(self, code: str) -> StageResult:
        """运行语法检查"""
        start = time.time()
        result = self.ast_checker.check_syntax(code)
        duration = time.time() - start
        
        if result.success:
            return StageResult(
                stage=VerifyStage.SYNTAX,
                passed=True,
                message="语法检查通过",
                details={"warnings": result.warnings},
                duration=duration
            )
        else:
            errors = [f"Line {e.line}: {e.message}" for e in result.errors]
            return StageResult(
                stage=VerifyStage.SYNTAX,
                passed=False,
                message=f"语法错误: {errors[0]}",
                details=result.to_dict(),
                duration=duration
            )
    
    def _run_type_check(self, code: str) -> StageResult:
        """运行类型检查"""
        start = time.time()
        result = self.type_checker.check_code(code)
        duration = time.time() - start
        
        if result.success:
            return StageResult(
                stage=VerifyStage.TYPE,
                passed=True,
                message=f"类型检查通过 ({len(result.warnings)} 警告)",
                details=result.to_dict(),
                duration=duration
            )
        else:
            errors = [f"Line {e.line}: {e.message}" for e in result.errors[:3]]
            return StageResult(
                stage=VerifyStage.TYPE,
                passed=False,
                message=f"类型错误: {'; '.join(errors)}",
                details=result.to_dict(),
                duration=duration
            )
    
    def _run_lint_check(self, code: str) -> StageResult:
        """运行静态分析"""
        start = time.time()
        result = self.lint_checker.check_code(code)
        duration = time.time() - start
        
        if result.success:
            return StageResult(
                stage=VerifyStage.LINT,
                passed=True,
                message=f"静态分析通过 (评分: {result.score:.1f}/10)",
                details=result.to_dict(),
                duration=duration
            )
        else:
            serious = [i for i in result.issues if i.category in ('error', 'fatal')]
            if serious:
                msg = f"Line {serious[0].line}: {serious[0].message}"
            else:
                msg = f"评分过低: {result.score:.1f}/10"
            return StageResult(
                stage=VerifyStage.LINT,
                passed=False,
                message=msg,
                details=result.to_dict(),
                duration=duration
            )
    
    def _run_symbolic_analysis(self, code: str) -> StageResult:
        """运行符号执行"""
        start = time.time()
        results = self.symbolic_executor.analyze_code(code)
        duration = time.time() - start
        
        # 收集潜在问题
        all_issues = []
        for r in results:
            all_issues.extend(r.issues)
        
        return StageResult(
            stage=VerifyStage.SYMBOLIC,
            passed=True,  # 符号执行只提供警告
            message=f"分析完成 ({len(results)} 函数, {len(all_issues)} 潜在问题)",
            details={"functions": [r.to_dict() for r in results]},
            duration=duration
        )
    
    def _run_z3_verify(self, code: str, spec: Dict[str, Any]) -> StageResult:
        """运行 Z3 验证"""
        start = time.time()
        func_name = spec.get("function", "")
        result = self.z3_verifier.verify_function(code, func_name, spec)
        duration = time.time() - start
        
        return StageResult(
            stage=VerifyStage.Z3,
            passed=result.verified,
            message=result.message,
            details=result.to_dict(),
            duration=duration
        )
    
    def _run_runtime_tests(self, code: str, test_code: str) -> StageResult:
        """运行时测试"""
        start = time.time()
        result = self.runtime_tester.run_tests(test_code, code)
        duration = time.time() - start
        
        return StageResult(
            stage=VerifyStage.RUNTIME,
            passed=result.success,
            message=f"测试 {result.passed}/{result.total} 通过",
            details=result.to_dict(),
            duration=duration
        )
    
    def _build_result(
        self,
        stages: List[StageResult],
        start_time: float,
        failed_stage: Optional[VerifyStage] = None,
        error_message: Optional[str] = None
    ) -> PipelineResult:
        """构建最终结果"""
        return PipelineResult(
            success=failed_stage is None,
            stages=stages,
            total_duration=time.time() - start_time,
            failed_stage=failed_stage,
            error_message=error_message
        )


def verify_code(code: str, **kwargs) -> Tuple[bool, str]:
    """
    便捷函数：验证代码
    
    Args:
        code: 源代码
        **kwargs: 传递给 VerifyPipeline 的参数
        
    Returns:
        (是否通过, 消息)
    """
    pipeline = VerifyPipeline(**kwargs)
    result = pipeline.run(code)
    
    if result.success:
        stages_info = ", ".join(s.stage.value for s in result.stages if s.passed)
        return True, f"验证通过 [{stages_info}]"
    else:
        return False, f"验证失败 [{result.failed_stage.value}]: {result.error_message}"
