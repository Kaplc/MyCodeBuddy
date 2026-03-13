"""
符号执行器
基于 AST 分析代码的执行路径和约束条件
"""
import ast
from typing import List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class PathConstraint:
    """路径约束"""
    condition: str
    negated: bool = False
    line: int = 0
    
    def __str__(self):
        return f"not ({self.condition})" if self.negated else self.condition


@dataclass
class ExecutionPath:
    """执行路径"""
    constraints: List[PathConstraint]
    variables: Dict[str, str]
    return_value: Optional[str] = None


@dataclass
class SymbolicResult:
    """符号分析结果"""
    function_name: str
    paths: List[ExecutionPath]
    issues: List[Dict[str, Any]]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "function": self.function_name,
            "path_count": len(self.paths),
            "constraints": [[str(c) for c in p.constraints] for p in self.paths[:10]],
            "issues": self.issues
        }


class SymbolicExecutor(ast.NodeVisitor):
    """符号执行器 - 分析代码执行路径"""
    
    def __init__(self, max_paths: int = 100):
        self.max_paths = max_paths
        self.paths: List[ExecutionPath] = []
        self.issues: List[Dict[str, Any]] = []
    
    def analyze_code(self, code: str) -> List[SymbolicResult]:
        """分析代码中所有函数"""
        try:
            tree = ast.parse(code)
            results = []
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    results.append(self.analyze_function(node))
            return results
        except:
            return []
    
    def analyze_function(self, func: ast.FunctionDef) -> SymbolicResult:
        """分析单个函数"""
        self.paths = []
        self.issues = []
        
        # 初始化参数为符号变量
        variables = {arg.arg: f"sym_{arg.arg}" for arg in func.args.args}
        
        # 遍历函数体，收集路径约束
        self._analyze_body(func.body, [], variables)
        
        # 检测潜在问题
        self._detect_issues(func)
        
        return SymbolicResult(
            function_name=func.name,
            paths=self.paths[:self.max_paths],
            issues=self.issues
        )
    
    def _analyze_body(self, body: List[ast.stmt], constraints: List[PathConstraint], variables: Dict[str, str]):
        """分析语句体"""
        if len(self.paths) >= self.max_paths:
            return
        
        current_constraints = constraints.copy()
        current_vars = variables.copy()
        
        for stmt in body:
            if isinstance(stmt, ast.If):
                # 分支：true 路径
                cond = ast.unparse(stmt.test)
                true_constraint = PathConstraint(cond, False, stmt.lineno)
                self._analyze_body(stmt.body, current_constraints + [true_constraint], current_vars)
                
                # 分支：false 路径
                if stmt.orelse:
                    false_constraint = PathConstraint(cond, True, stmt.lineno)
                    self._analyze_body(stmt.orelse, current_constraints + [false_constraint], current_vars)
            
            elif isinstance(stmt, ast.Assign):
                # 赋值语句
                for target in stmt.targets:
                    if isinstance(target, ast.Name):
                        current_vars[target.id] = ast.unparse(stmt.value)
            
            elif isinstance(stmt, ast.Return):
                # 返回语句 - 记录完整路径
                ret_val = ast.unparse(stmt.value) if stmt.value else "None"
                self.paths.append(ExecutionPath(current_constraints, current_vars, ret_val))
                return
        
        # 隐式返回
        self.paths.append(ExecutionPath(current_constraints, current_vars, "None"))
    
    def _detect_issues(self, func: ast.FunctionDef):
        """检测潜在问题"""
        for node in ast.walk(func):
            # 检测除零
            if isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Div, ast.FloorDiv, ast.Mod)):
                if isinstance(node.right, ast.Name):
                    self.issues.append({
                        "type": "potential_division_by_zero",
                        "line": node.lineno,
                        "variable": node.right.id
                    })
            
            # 检测空值访问
            if isinstance(node, ast.Subscript):
                if isinstance(node.value, ast.Name):
                    self.issues.append({
                        "type": "potential_index_error",
                        "line": node.lineno,
                        "variable": node.value.id
                    })
    
    def get_z3_constraints(self, func_name: str = None) -> List[str]:
        """获取 Z3 格式的约束条件"""
        z3_constraints = []
        for path in self.paths:
            if path.constraints:
                cond = " and ".join(str(c) for c in path.constraints)
                z3_constraints.append(cond)
        return z3_constraints


def symbolic_analyze(code: str) -> Dict[str, Any]:
    """便捷函数：符号分析代码"""
    executor = SymbolicExecutor()
    results = executor.analyze_code(code)
    return {
        "functions": [r.to_dict() for r in results],
        "total_functions": len(results)
    }
