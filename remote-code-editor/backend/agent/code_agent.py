"""
代码生成 Agent
负责生成代码并进行自动修复
"""
import re
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass

from .agent_core import AgentCore
from pipeline.verify_pipeline import VerifyPipeline, PipelineResult


@dataclass
class CodeGenerationResult:
    """代码生成结果"""
    success: bool
    code: str
    iterations: int
    verification_result: Optional[PipelineResult] = None
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "code": self.code,
            "iterations": self.iterations,
            "verification": self.verification_result.to_dict() if self.verification_result else None,
            "error": self.error
        }


class CodeAgent(AgentCore):
    """
    代码生成 Agent
    
    功能：
    1. 根据需求生成代码
    2. 自动验证生成的代码
    3. 自动修复验证失败的代码
    4. 支持多轮迭代优化
    """
    
    # 系统提示词
    SYSTEM_PROMPT = """你是一个专业的 Python 代码生成 Agent。

职责：
1. 根据用户需求生成高质量的 Python 代码
2. 代码需要符合 PEP8 规范
3. 需要添加适当的类型注解
4. 需要添加文档字符串
5. 需要考虑错误处理

输出格式：
- 只输出代码，不要输出其他解释
- 代码用 ```python 和 ``` 包裹
- 如果需要多个文件，用 # === filename.py === 分隔
"""
    
    FIX_PROMPT = """请修复以下代码中的错误：

原始代码：
```python
{code}
```

错误信息：
{error}

请输出修复后的完整代码（用 ```python 和 ``` 包裹）。
只修复错误，不要改变代码的逻辑功能。
"""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "glm-4.7-flash",
        max_fix_iterations: int = 5,
        enable_type_check: bool = True,
        enable_lint: bool = True
    ):
        """
        初始化代码生成 Agent
        
        Args:
            api_key: API 密钥
            model: 模型名称
            max_fix_iterations: 最大修复迭代次数
            enable_type_check: 是否启用类型检查
            enable_lint: 是否启用 Lint 检查
        """
        super().__init__(api_key, model)
        self.max_fix_iterations = max_fix_iterations
        
        # 初始化验证流水线
        self.pipeline = VerifyPipeline(
            enable_type_check=enable_type_check,
            enable_lint=enable_lint,
            enable_symbolic=True,
            enable_z3=False,
            enable_runtime=False
        )
    
    def generate_code(self, prompt: str) -> str:
        """
        生成代码
        
        Args:
            prompt: 需求描述
            
        Returns:
            生成的代码
        """
        response = self.llm(prompt, self.SYSTEM_PROMPT)
        return self._extract_code(response)
    
    def fix_code(self, code: str, error: str) -> str:
        """
        修复代码
        
        Args:
            code: 原始代码
            error: 错误信息
            
        Returns:
            修复后的代码
        """
        prompt = self.FIX_PROMPT.format(code=code, error=error)
        response = self.llm(prompt)
        return self._extract_code(response)
    
    def run(self, task: str, **kwargs) -> CodeGenerationResult:
        """
        执行代码生成任务（带自动验证和修复）
        
        Args:
            task: 任务描述
            **kwargs: 额外参数
                - test_code: 测试代码
                - z3_spec: Z3 验证规约
                
        Returns:
            CodeGenerationResult: 生成结果
        """
        # 1. 生成初始代码
        code = self.generate_code(task)
        
        if not code:
            return CodeGenerationResult(
                success=False,
                code="",
                iterations=0,
                error="代码生成失败：LLM 未返回有效代码"
            )
        
        # 2. 验证和修复循环
        test_code = kwargs.get("test_code")
        z3_spec = kwargs.get("z3_spec")
        
        for i in range(self.max_fix_iterations):
            # 运行验证
            result = self.pipeline.run(code, test_code, z3_spec)
            
            if result.success:
                return CodeGenerationResult(
                    success=True,
                    code=code,
                    iterations=i + 1,
                    verification_result=result
                )
            
            # 获取错误信息
            error_msg = result.error_message or "验证失败"
            
            # 尝试修复
            code = self.fix_code(code, error_msg)
            
            if not code:
                return CodeGenerationResult(
                    success=False,
                    code="",
                    iterations=i + 1,
                    verification_result=result,
                    error="代码修复失败"
                )
        
        # 达到最大迭代次数
        final_result = self.pipeline.run(code, test_code, z3_spec)
        return CodeGenerationResult(
            success=final_result.success,
            code=code,
            iterations=self.max_fix_iterations,
            verification_result=final_result,
            error=None if final_result.success else "达到最大修复次数"
        )
    
    def _extract_code(self, response: str) -> str:
        """从 LLM 响应中提取代码"""
        # 尝试提取 ```python ... ``` 块
        pattern = r'```python\s*(.*?)\s*```'
        matches = re.findall(pattern, response, re.DOTALL)
        
        if matches:
            return "\n\n".join(matches)
        
        # 尝试提取 ``` ... ``` 块
        pattern = r'```\s*(.*?)\s*```'
        matches = re.findall(pattern, response, re.DOTALL)
        
        if matches:
            return "\n\n".join(matches)
        
        # 如果没有代码块，返回整个响应（可能就是纯代码）
        return response.strip()
    
    def generate_tests(self, code: str) -> str:
        """
        为代码生成测试用例
        
        Args:
            code: 源代码
            
        Returns:
            测试代码
        """
        prompt = f"""为以下 Python 代码生成 pytest 测试用例：

```python
{code}
```

要求：
1. 覆盖所有公开函数和方法
2. 包含正常情况和边界情况测试
3. 使用 pytest 框架
4. 添加适当的断言

只输出测试代码。
"""
        response = self.llm(prompt, self.SYSTEM_PROMPT)
        return self._extract_code(response)
    
    def improve_code(self, code: str, suggestions: List[str]) -> str:
        """
        根据建议改进代码
        
        Args:
            code: 原始代码
            suggestions: 改进建议列表
            
        Returns:
            改进后的代码
        """
        prompt = f"""请根据以下建议改进代码：

原始代码：
```python
{code}
```

改进建议：
{chr(10).join(f"- {s}" for s in suggestions)}

请输出改进后的完整代码。
"""
        response = self.llm(prompt)
        return self._extract_code(response)


def solve_task(task: str, max_iterations: int = 5) -> str:
    """
    便捷函数：解决编程任务
    
    Args:
        task: 任务描述
        max_iterations: 最大迭代次数
        
    Returns:
        生成的代码
    """
    agent = CodeAgent(max_fix_iterations=max_iterations)
    result = agent.run(task)
    return result.code
