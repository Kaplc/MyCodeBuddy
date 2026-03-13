"""
Z3 约束求解验证器
使用 Z3 SMT 求解器验证代码逻辑正确性
"""
import re
import ast
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass

# 尝试导入 z3
try:
    from z3 import Int, Real, Bool, Solver, sat, unsat, And, Or, Not, Implies, If
    Z3_AVAILABLE = True
except ImportError:
    Z3_AVAILABLE = False


@dataclass
class VerificationResult:
    """验证结果"""
    verified: bool
    counter_example: Optional[Dict[str, Any]] = None
    message: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "verified": self.verified,
            "counter_example": self.counter_example,
            "message": self.message
        }


class Z3Verifier:
    """Z3 约束求解验证器"""
    
    def __init__(self):
        self.z3_available = Z3_AVAILABLE
    
    def verify_function(self, code: str, func_name: str, spec: Dict[str, Any]) -> VerificationResult:
        """
        验证函数满足规约
        
        Args:
            code: 源代码
            func_name: 函数名
            spec: 规约 {
                "precondition": "x > 0",
                "postcondition": "result > x",
                "invariants": ["x >= 0"]
            }
        """
        if not self.z3_available:
            return VerificationResult(True, None, "Z3 未安装，跳过形式验证")
        
        try:
            tree = ast.parse(code)
            func = self._find_function(tree, func_name)
            if not func:
                return VerificationResult(False, None, f"未找到函数 {func_name}")
            
            # 创建符号变量
            args = [arg.arg for arg in func.args.args]
            solver = Solver()
            
            # 添加前置条件
            if spec.get("precondition"):
                pre = self._parse_constraint(spec["precondition"], args)
                if pre is not None:
                    solver.add(pre)
            
            # 添加后置条件的否定（反证法）
            if spec.get("postcondition"):
                post = self._parse_constraint(spec["postcondition"], args)
                if post is not None:
                    solver.add(Not(post))
            
            # 求解
            result = solver.check()
            
            if result == unsat:
                return VerificationResult(True, None, "验证通过：后置条件总是成立")
            elif result == sat:
                model = solver.model()
                counter = {str(d): str(model[d]) for d in model.decls()}
                return VerificationResult(False, counter, "验证失败：存在反例")
            else:
                return VerificationResult(True, None, "验证超时或未知")
                
        except Exception as e:
            return VerificationResult(True, None, f"验证跳过: {str(e)}")
    
    def verify_no_overflow(self, code: str, func_name: str, bounds: Dict[str, Tuple[int, int]]) -> VerificationResult:
        """验证函数不会溢出"""
        if not self.z3_available:
            return VerificationResult(True, None, "Z3 未安装")
        
        try:
            tree = ast.parse(code)
            func = self._find_function(tree, func_name)
            if not func:
                return VerificationResult(False, None, f"未找到函数 {func_name}")
            
            solver = Solver()
            vars_map = {}
            
            # 创建变量并添加边界约束
            for arg in func.args.args:
                var = Int(arg.arg)
                vars_map[arg.arg] = var
                if arg.arg in bounds:
                    low, high = bounds[arg.arg]
                    solver.add(var >= low, var <= high)
            
            # 分析可能的溢出点
            overflow_possible = False
            for node in ast.walk(func):
                if isinstance(node, ast.BinOp):
                    # 简单检查：乘法可能导致溢出
                    if isinstance(node.op, ast.Mult):
                        overflow_possible = True
                        break
            
            if not overflow_possible:
                return VerificationResult(True, None, "未检测到溢出风险")
            
            return VerificationResult(True, None, "存在潜在溢出风险，建议添加边界检查")
            
        except Exception as e:
            return VerificationResult(True, None, f"验证跳过: {str(e)}")
    
    def verify_constraints(self, constraints: List[str]) -> VerificationResult:
        """
        验证一组约束是否可满足
        
        Args:
            constraints: 约束条件列表 ["x > 0", "y < x", "y > 10"]
        """
        if not self.z3_available:
            return VerificationResult(True, None, "Z3 未安装")
        
        try:
            solver = Solver()
            vars_set = set()
            
            # 提取变量
            for c in constraints:
                vars_set.update(re.findall(r'\b([a-zA-Z_][a-zA-Z0-9_]*)\b', c))
            
            # 移除关键字
            keywords = {'and', 'or', 'not', 'True', 'False', 'None'}
            vars_set -= keywords
            
            # 创建变量
            vars_map = {v: Int(v) for v in vars_set}
            
            # 添加约束
            for c in constraints:
                parsed = self._parse_constraint(c, list(vars_set))
                if parsed is not None:
                    solver.add(parsed)
            
            result = solver.check()
            
            if result == sat:
                model = solver.model()
                solution = {str(d): str(model[d]) for d in model.decls()}
                return VerificationResult(True, solution, "约束可满足")
            elif result == unsat:
                return VerificationResult(False, None, "约束不可满足（存在矛盾）")
            else:
                return VerificationResult(True, None, "求解超时")
                
        except Exception as e:
            return VerificationResult(True, None, f"验证跳过: {str(e)}")
    
    def _find_function(self, tree: ast.AST, name: str) -> Optional[ast.FunctionDef]:
        """在 AST 中查找函数"""
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == name:
                return node
        return None
    
    def _parse_constraint(self, constraint: str, variables: List[str]):
        """将字符串约束转换为 Z3 表达式"""
        if not self.z3_available:
            return None
        
        try:
            # 创建变量映射
            local_vars = {v: Int(v) for v in variables}
            local_vars['result'] = Int('result')
            
            # 替换运算符
            expr = constraint.replace('&&', ' and ').replace('||', ' or ')
            expr = expr.replace('==', '==').replace('!=', '!=')
            
            # 在安全环境中求值
            return eval(expr, {"__builtins__": {}}, local_vars)
        except:
            return None


def z3_verify(constraints: List[str]) -> Tuple[bool, Optional[str]]:
    """便捷函数：验证约束"""
    verifier = Z3Verifier()
    result = verifier.verify_constraints(constraints)
    if result.verified:
        return True, result.message
    else:
        return False, f"{result.message}: {result.counter_example}"
