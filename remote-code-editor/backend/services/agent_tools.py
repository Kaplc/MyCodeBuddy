"""
AI Agent 工具模块
定义 Agent 可用的工具和执行逻辑
"""
import os
import json
import asyncio
import subprocess
from pathlib import Path
from typing import Dict, List, Any, Optional
from django.conf import settings


# Agent 工具定义（智谱 AI function calling 格式）
AGENT_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "读取指定文件的内容。用于查看代码文件、配置文件等。",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "文件的相对路径（相对于工作区根目录）"
                    }
                },
                "required": ["path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "创建或覆盖文件内容。用于创建新文件或修改现有文件。",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "文件的相对路径（相对于工作区根目录）"
                    },
                    "content": {
                        "type": "string",
                        "description": "要写入的文件内容"
                    }
                },
                "required": ["path", "content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_directory",
            "description": "列出目录下的文件和子目录。用于浏览项目结构。",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "目录的相对路径，空字符串表示工作区根目录"
                    }
                },
                "required": ["path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_content",
            "description": "在工作区文件中搜索指定内容。用于查找代码、配置等。",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "要搜索的文本或正则表达式"
                    },
                    "file_pattern": {
                        "type": "string",
                        "description": "文件名模式，如 *.py, *.js 等（可选）"
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "execute_command",
            "description": "在工作区目录下执行终端命令。用于运行脚本、安装依赖等。注意：只能执行安全的命令。",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "要执行的命令"
                    }
                },
                "required": ["command"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "create_directory",
            "description": "创建新目录。",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "要创建的目录路径（相对于工作区）"
                    }
                },
                "required": ["path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "delete_file",
            "description": "删除指定文件或目录。",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "要删除的文件或目录路径（相对于工作区）"
                    }
                },
                "required": ["path"]
            }
        }
    },
    # ===== 代码验证工具 =====
    {
        "type": "function",
        "function": {
            "name": "generate_tests",
            "description": "为指定代码生成单元测试。用于自动创建测试用例，提高代码质量。",
            "parameters": {
                "type": "object",
                "properties": {
                    "code": {
                        "type": "string",
                        "description": "要生成测试的代码内容"
                    },
                    "language": {
                        "type": "string",
                        "description": "编程语言，如 'python'"
                    },
                    "test_framework": {
                        "type": "string",
                        "description": "测试框架，如 'pytest'（默认 pytest）"
                    }
                },
                "required": ["code"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "run_tests",
            "description": "运行项目的测试套件。用于验证代码修改后是否通过测试。",
            "parameters": {
                "type": "object",
                "properties": {
                    "test_path": {
                        "type": "string",
                        "description": "测试文件或目录的相对路径（可选，默认运行所有测试）"
                    },
                    "verbose": {
                        "type": "boolean",
                        "description": "是否显示详细输出（默认 true）"
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_symbol",
            "description": "在项目中搜索代码符号（函数、类、变量等）。用于理解代码结构或查找定义。",
            "parameters": {
                "type": "object",
                "properties": {
                    "symbol_name": {
                        "type": "string",
                        "description": "要搜索的符号名称"
                    }
                },
                "required": ["symbol_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_code_references",
            "description": "查找代码中某个符号的所有引用位置。用于代码重构或理解代码调用关系。",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "文件相对路径"
                    },
                    "symbol_name": {
                        "type": "string",
                        "description": "符号名称（函数名、类名等）"
                    }
                },
                "required": ["file_path", "symbol_name"]
            }
        }
    },
    # ===== 验证流水线工具 =====
    {
        "type": "function",
        "function": {
            "name": "run_verification_pipeline",
            "description": "运行完整的代码验证流水线。包括语法检查、静态分析、类型检查、运行测试等。用于全面验证代码质量。",
            "parameters": {
                "type": "object",
                "properties": {
                    "code": {
                        "type": "string",
                        "description": "要验证的代码内容"
                    },
                    "language": {
                        "type": "string",
                        "description": "编程语言，如 'python'"
                    },
                    "skip_tests": {
                        "type": "boolean",
                        "description": "是否跳过测试运行（默认 false）"
                    }
                },
                "required": ["code", "language"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "index_workspace",
            "description": "索引工作区代码，建立代码图索引。用于后续的代码搜索、引用查找等功能。首次搜索前需要先运行此工具。",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "要索引的目录路径（相对于工作区）"
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_call_graph",
            "description": "获取函数的调用图（调用了哪些函数、被哪些函数调用）。用于理解代码调用关系。",
            "parameters": {
                "type": "object",
                "properties": {
                    "function_name": {
                        "type": "string",
                        "description": "函数名称"
                    },
                    "depth": {
                        "type": "integer",
                        "description": "调用深度（默认2）"
                    }
                },
                "required": ["function_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_file_outline",
            "description": "获取文件的结构大纲（类、函数、导入等）。用于快速了解文件结构。",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "文件相对路径"
                    }
                },
                "required": ["path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "verify_with_z3",
            "description": "使用 Z3 SMT 求解器验证代码逻辑（形式化验证）。用于验证代码的正确性断言。",
            "parameters": {
                "type": "object",
                "properties": {
                    "code": {
                        "type": "string",
                        "description": "要验证的代码（需要包含断言）"
                    },
                    "property": {
                        "type": "string",
                        "description": "要验证的属性描述"
                    }
                },
                "required": ["code"]
            }
        }
    }
]


class AgentToolExecutor:
    """Agent 工具执行器"""
    
    def __init__(self, workspace_path: str):
        """
        初始化工具执行器
        
        Args:
            workspace_path: 工作区路径
        """
        self.workspace = Path(workspace_path).resolve() if workspace_path else None
        
        # 危险命令黑名单
        self.dangerous_commands = [
            'rm -rf /',
            'format',
            'del /f /s /q',
            'rmdir /s /q',
            ':(){:|:&};:',  # fork bomb
        ]
        
        # 允许的命令白名单前缀
        self.allowed_command_prefixes = [
            'python', 'pip', 'npm', 'node', 'yarn',
            'git', 'ls', 'dir', 'cat', 'type', 'echo',
            'cd', 'mkdir', 'touch', 'cp', 'mv', 'copy',
            'pytest', 'jest', 'vue', 'react', 'ng',
            'docker', 'make', 'cargo', 'go', 'rustc',
        ]
    
    def set_workspace(self, workspace_path: str):
        """
        动态设置工作区路径
        
        Args:
            workspace_path: 新的工作区路径
        """
        if workspace_path:
            self.workspace = Path(workspace_path).resolve()
        else:
            self.workspace = None
    
    def _resolve_path(self, relative_path: str) -> Path:
        """解析相对路径为绝对路径"""
        if not self.workspace:
            raise ValueError("工作区未设置")
        
        # 清理路径
        relative_path = relative_path.lstrip("/\\")
        if not relative_path:
            return self.workspace
        
        abs_path = (self.workspace / relative_path).resolve()
        
        # 安全检查：确保路径在工作区内
        try:
            abs_path.relative_to(self.workspace)
        except ValueError:
            raise ValueError(f"路径越出工作区: {relative_path}")
        
        return abs_path
    
    async def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行工具
        
        Args:
            tool_name: 工具名称
            arguments: 工具参数
        
        Returns:
            执行结果
        """
        try:
            if tool_name == "read_file":
                return await self._read_file(arguments.get("path", ""))
            elif tool_name == "write_file":
                return await self._write_file(
                    arguments.get("path", ""),
                    arguments.get("content", "")
                )
            elif tool_name == "list_directory":
                return await self._list_directory(arguments.get("path", ""))
            elif tool_name == "search_content":
                return await self._search_content(
                    arguments.get("query", ""),
                    arguments.get("file_pattern")
                )
            elif tool_name == "execute_command":
                return await self._execute_command(arguments.get("command", ""))
            elif tool_name == "create_directory":
                return await self._create_directory(arguments.get("path", ""))
            elif tool_name == "delete_file":
                return await self._delete_file(arguments.get("path", ""))
            # 代码验证工具
            elif tool_name == "generate_tests":
                return await self._generate_tests(
                    arguments.get("code", ""),
                    arguments.get("language", "python"),
                    arguments.get("test_framework", "pytest")
                )
            elif tool_name == "run_tests":
                return await self._run_tests(
                    arguments.get("test_path", ""),
                    arguments.get("verbose", True)
                )
            elif tool_name == "search_symbol":
                return await self._search_symbol(arguments.get("symbol_name", ""))
            elif tool_name == "get_code_references":
                return await self._get_code_references(
                    arguments.get("file_path", ""),
                    arguments.get("symbol_name", "")
                )
            # 验证流水线工具
            elif tool_name == "run_verification_pipeline":
                return await self._run_verification_pipeline(
                    arguments.get("code", ""),
                    arguments.get("language", "python"),
                    arguments.get("skip_tests", False)
                )
            elif tool_name == "index_workspace":
                return await self._index_workspace(arguments.get("path", ""))
            elif tool_name == "get_call_graph":
                return await self._get_call_graph(
                    arguments.get("function_name", ""),
                    arguments.get("depth", 2)
                )
            elif tool_name == "get_file_outline":
                return await self._get_file_outline(arguments.get("path", ""))
            elif tool_name == "verify_with_z3":
                return await self._verify_with_z3(
                    arguments.get("code", ""),
                    arguments.get("property", "")
                )
            else:
                return {"success": False, "error": f"未知的工具: {tool_name}"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _read_file(self, path: str) -> Dict[str, Any]:
        """读取文件"""
        try:
            file_path = self._resolve_path(path)
            
            if not file_path.exists():
                return {"success": False, "error": f"文件不存在: {path}"}
            
            if file_path.is_dir():
                return {"success": False, "error": f"路径是目录: {path}"}
            
            # 检查文件大小
            if file_path.stat().st_size > 1024 * 1024:  # 1MB
                return {"success": False, "error": "文件太大，超过 1MB 限制"}
            
            content = file_path.read_text(encoding='utf-8')
            return {
                "success": True,
                "path": path,
                "content": content,
                "size": len(content)
            }
        except UnicodeDecodeError:
            return {"success": False, "error": "无法读取二进制文件"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _write_file(self, path: str, content: str) -> Dict[str, Any]:
        """写入文件"""
        import logging
        logger = logging.getLogger('workflow')
        
        try:
            # 检查工作区是否设置
            if not self.workspace:
                error_msg = "工作区未设置，无法创建文件。请先设置工作区路径。"
                logger.error(f"[Agent Tool] write_file失败: {error_msg}")
                return {"success": False, "error": error_msg, "hint": "请在工作流中设置workspace参数"}
            
            file_path = self._resolve_path(path)
            logger.info(f"[Agent Tool] write_file | 相对路径: {path}, 绝对路径: {file_path}")
            
            # 确保父目录存在
            file_path.parent.mkdir(parents=True, exist_ok=True)
            logger.info(f"[Agent Tool] 父目录已创建/确认: {file_path.parent}")
            
            # 写入文件
            file_path.write_text(content, encoding='utf-8')
            logger.info(f"[Agent Tool] 文件写入成功 | 路径: {file_path}, 大小: {len(content)}字节")
            
            # 验证文件确实被创建
            if not file_path.exists():
                error_msg = f"文件写入后验证失败: {file_path}"
                logger.error(f"[Agent Tool] {error_msg}")
                return {"success": False, "error": error_msg}
            
            return {
                "success": True,
                "path": path,
                "absolute_path": str(file_path),
                "workspace": str(self.workspace),
                "message": f"文件已保存到工作区: {path}",
                "size": len(content)
            }
        except ValueError as e:
            # _resolve_path抛出的错误（如工作区未设置、路径越界）
            error_msg = str(e)
            logger.error(f"[Agent Tool] write_file路径错误: {error_msg}")
            return {"success": False, "error": error_msg, "hint": "请确保工作区已正确设置"}
        except Exception as e:
            error_msg = f"文件写入失败: {str(e)}"
            logger.error(f"[Agent Tool] write_file异常: {error_msg}")
            return {"success": False, "error": error_msg}
    
    async def _list_directory(self, path: str) -> Dict[str, Any]:
        """列出目录"""
        try:
            dir_path = self._resolve_path(path)
            
            if not dir_path.exists():
                return {"success": False, "error": f"目录不存在: {path}"}
            
            if not dir_path.is_dir():
                return {"success": False, "error": f"路径不是目录: {path}"}
            
            items = []
            # 忽略的目录
            ignore_dirs = {'.git', '__pycache__', 'node_modules', '.venv', 'venv', 'dist', 'build'}
            
            for item in sorted(dir_path.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower())):
                if item.name.startswith('.') and item.name != '.env':
                    continue
                if item.is_dir() and item.name in ignore_dirs:
                    continue
                
                items.append({
                    "name": item.name,
                    "type": "directory" if item.is_dir() else "file",
                    "size": item.stat().st_size if item.is_file() else None
                })
            
            return {
                "success": True,
                "path": path or "/",
                "items": items,
                "count": len(items)
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _search_content(self, query: str, file_pattern: Optional[str] = None) -> Dict[str, Any]:
        """搜索内容"""
        import re
        
        try:
            if not query:
                return {"success": False, "error": "搜索内容不能为空"}
            
            results = []
            ignore_dirs = {'.git', '__pycache__', 'node_modules', '.venv', 'venv', 'dist', 'build'}
            
            def should_skip_file(file_path: Path) -> bool:
                """判断是否跳过文件"""
                # 跳过二进制文件
                binary_extensions = {'.pyc', '.exe', '.dll', '.so', '.bin', '.png', '.jpg', '.gif', '.pdf'}
                if file_path.suffix.lower() in binary_extensions:
                    return True
                # 跳过大文件
                if file_path.stat().st_size > 512 * 1024:  # 512KB
                    return True
                return False
            
            def matches_pattern(file_path: Path) -> bool:
                """判断文件是否匹配模式"""
                if not file_pattern:
                    return True
                import fnmatch
                return fnmatch.fnmatch(file_path.name, file_pattern)
            
            for root, dirs, files in os.walk(self.workspace):
                # 过滤目录
                dirs[:] = [d for d in dirs if d not in ignore_dirs and not d.startswith('.')]
                
                for file in files:
                    if file.startswith('.'):
                        continue
                    
                    file_path = Path(root) / file
                    
                    if should_skip_file(file_path):
                        continue
                    
                    if not matches_pattern(file_path):
                        continue
                    
                    try:
                        content = file_path.read_text(encoding='utf-8', errors='ignore')
                        matches = []
                        
                        for i, line in enumerate(content.split('\n'), 1):
                            if re.search(query, line, re.IGNORECASE):
                                matches.append({
                                    "line": i,
                                    "content": line.strip()[:200]
                                })
                                if len(matches) >= 5:  # 每个文件最多5个匹配
                                    break
                        
                        if matches:
                            rel_path = str(file_path.relative_to(self.workspace))
                            results.append({
                                "file": rel_path,
                                "matches": matches
                            })
                            
                            if len(results) >= 20:  # 最多20个文件
                                break
                    except Exception:
                        continue
                
                if len(results) >= 20:
                    break
            
            return {
                "success": True,
                "query": query,
                "results": results,
                "total_files": len(results)
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _execute_command(self, command: str) -> Dict[str, Any]:
        """执行命令"""
        try:
            if not command:
                return {"success": False, "error": "命令不能为空"}
            
            # 安全检查
            command_lower = command.lower().strip()
            
            # 检查危险命令
            for dangerous in self.dangerous_commands:
                if dangerous in command_lower:
                    return {"success": False, "error": f"禁止执行危险命令: {command}"}
            
            # 检查命令是否在白名单中
            first_word = command.split()[0].lower()
            if not any(first_word.startswith(prefix) for prefix in self.allowed_command_prefixes):
                return {
                    "success": False, 
                    "error": f"命令 '{first_word}' 不在允许列表中。允许的命令前缀: {', '.join(self.allowed_command_prefixes)}"
                }
            
            # 在工作区目录下执行
            process = await asyncio.create_subprocess_shell(
                command,
                cwd=str(self.workspace),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=30  # 30秒超时
            )
            
            stdout_text = stdout.decode('utf-8', errors='ignore')
            stderr_text = stderr.decode('utf-8', errors='ignore')
            
            # 限制输出长度
            max_output = 5000
            if len(stdout_text) > max_output:
                stdout_text = stdout_text[:max_output] + "\n... (输出已截断)"
            if len(stderr_text) > max_output:
                stderr_text = stderr_text[:max_output] + "\n... (输出已截断)"
            
            return {
                "success": process.returncode == 0,
                "command": command,
                "return_code": process.returncode,
                "stdout": stdout_text,
                "stderr": stderr_text
            }
        except asyncio.TimeoutError:
            return {"success": False, "error": "命令执行超时（30秒）"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _create_directory(self, path: str) -> Dict[str, Any]:
        """创建目录"""
        try:
            dir_path = self._resolve_path(path)
            
            if dir_path.exists():
                return {"success": False, "error": f"路径已存在: {path}"}
            
            dir_path.mkdir(parents=True, exist_ok=False)
            
            return {
                "success": True,
                "path": path,
                "message": f"目录已创建: {path}"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _delete_file(self, path: str) -> Dict[str, Any]:
        """删除文件或目录"""
        import shutil
        
        try:
            file_path = self._resolve_path(path)
            
            if not file_path.exists():
                return {"success": False, "error": f"路径不存在: {path}"}
            
            if file_path.is_dir():
                shutil.rmtree(file_path)
            else:
                file_path.unlink()
            
            return {
                "success": True,
                "path": path,
                "message": f"已删除: {path}"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    # ===== 代码验证工具方法 =====
    
    async def _generate_tests(self, code: str, language: str = "python", 
                             test_framework: str = "pytest") -> Dict[str, Any]:
        """生成测试代码"""
        try:
            if not code:
                return {"success": False, "error": "代码不能为空"}
            
            if language != "python":
                return {"success": False, "error": f"暂不支持 {language} 的测试生成"}
            
            # 使用 verify 模块的测试生成功能
            from verifier.runtime_test import generate_tests_for_code
            
            test_code = generate_tests_for_code(code, test_framework)
            
            return {
                "success": True,
                "test_code": test_code,
                "message": "测试代码生成成功"
            }
        except ImportError as e:
            return {"success": False, "error": f"测试生成模块导入失败: {str(e)}"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _run_tests(self, test_path: str = "", verbose: bool = True) -> Dict[str, Any]:
        """运行测试"""
        try:
            from verifier.runtime_test import run_pytest
            
            # 如果没有指定测试路径，使用工作区的 tests 目录
            if not test_path:
                test_path = "."
            
            result = run_pytest(self.workspace, test_path, verbose)
            
            return {
                "success": result["success"],
                "output": result.get("output", ""),
                "return_code": result.get("return_code", -1),
                "summary": result.get("summary", "")
            }
        except ImportError as e:
            return {"success": False, "error": f"测试运行模块导入失败: {str(e)}"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _search_symbol(self, symbol_name: str) -> Dict[str, Any]:
        """搜索代码符号"""
        try:
            if not symbol_name:
                return {"success": False, "error": "符号名称不能为空"}
            
            from code_index.searcher import CodeSearcher
            
            searcher = CodeSearcher(self.workspace)
            results = searcher.search(symbol_name)
            
            return {
                "success": True,
                "symbol": symbol_name,
                "results": results,
                "count": len(results)
            }
        except ImportError as e:
            return {"success": False, "error": f"搜索模块导入失败: {str(e)}"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _get_code_references(self, file_path: str, symbol_name: str) -> Dict[str, Any]:
        """获取代码引用"""
        try:
            if not file_path or not symbol_name:
                return {"success": False, "error": "文件路径和符号名称不能为空"}
            
            from code_index.searcher import CodeSearcher
            
            graph = await self._get_code_graph()
            searcher = CodeSearcher(graph)
            references = searcher.search_references(symbol_name)
            
            return {
                "success": True,
                "file": file_path,
                "symbol": symbol_name,
                "references": references,
                "count": len(references)
            }
        except ImportError as e:
            return {"success": False, "error": f"搜索模块导入失败: {str(e)}"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    # ===== 验证流水线工具方法 =====
    
    async def _run_verification_pipeline(self, code: str, language: str = "python", 
                                        skip_tests: bool = False) -> Dict[str, Any]:
        """运行完整验证流水线"""
        try:
            from pipeline.verify_pipeline import VerifyPipeline
            
            # 配置流水线
            pipeline = VerifyPipeline(
                enable_runtime=not skip_tests,
                enable_z3=False,
                enable_symbolic=False
            )
            result = pipeline.run(code)
            
            # 转换为字典格式
            result_dict = result.to_dict() if hasattr(result, 'to_dict') else result
            
            return {
                "success": result_dict.get("success", False),
                "stages": result_dict.get("stages", []),
                "summary": f"验证{'通过' if result_dict.get('success') else '失败'} - {result_dict.get('total_duration', '0s')}",
                "errors": [s for s in result_dict.get("stages", []) if not s.get("passed")]
            }
        except ImportError as e:
            return {"success": False, "error": f"流水线模块导入失败: {str(e)}"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    # 缓存索引图
    _code_graph_cache = None
    
    async def _get_code_graph(self):
        """获取或创建代码图"""
        if self._code_graph_cache is None:
            from code_index.indexer import CodeIndexer
            indexer = CodeIndexer(str(self.workspace))
            self._code_graph_cache = indexer.index()
        return self._code_graph_cache
    
    async def _index_workspace(self, path: str = "") -> Dict[str, Any]:
        """索引工作区"""
        try:
            target_path = self.workspace if not path else self._resolve_path(path)
            
            from code_index.indexer import CodeIndexer
            
            indexer = CodeIndexer(str(target_path))
            graph = indexer.index()
            
            # 更新缓存
            self._code_graph_cache = graph
            
            return {
                "success": True,
                "indexed_files": len(graph.file_symbols),
                "symbols_count": len(graph.symbols),
                "message": f"索引完成，共 {len(graph.symbols)} 个符号"
            }
        except ImportError as e:
            return {"success": False, "error": f"索引模块导入失败: {str(e)}"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _get_call_graph(self, function_name: str, depth: int = 2) -> Dict[str, Any]:
        """获取调用图"""
        try:
            from code_index.searcher import CodeSearcher
            
            graph = await self._get_code_graph()
            searcher = CodeSearcher(graph)
            call_graph = searcher.get_call_graph(function_name, depth)
            
            return {
                "success": True,
                "function": function_name,
                "call_graph": call_graph
            }
        except ImportError as e:
            return {"success": False, "error": f"搜索模块导入失败: {str(e)}"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _get_file_outline(self, path: str) -> Dict[str, Any]:
        """获取文件大纲"""
        try:
            if not path:
                return {"success": False, "error": "文件路径不能为空"}
            
            from code_index.searcher import CodeSearcher
            
            graph = await self._get_code_graph()
            searcher = CodeSearcher(graph)
            outline = searcher.get_file_outline(path)
            
            return {
                "success": True,
                "outline": outline
            }
        except ImportError as e:
            return {"success": False, "error": f"搜索模块导入失败: {str(e)}"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _verify_with_z3(self, code: str, property: str = "") -> Dict[str, Any]:
        """Z3 形式化验证"""
        try:
            from verifier.z3_verify import verify_code_properties
            
            result = verify_code_properties(code, property)
            
            return {
                "success": result["success"],
                "verified": result.get("verified", False),
                "model": result.get("model"),
                "counterexample": result.get("counterexample"),
                "summary": result.get("summary", "")
            }
        except ImportError as e:
            return {"success": False, "error": f"Z3 模块导入失败: {str(e)}"}
        except Exception as e:
            return {"success": False, "error": str(e)}


def get_tools_definition(mode: str = 'agent') -> List[Dict]:
    """
    获取工具定义
    
    Args:
        mode: AI 模式
            - 'agent': Agent 模式，返回所有工具（包括写入工具）
            - 'ask': Ask 模式，只返回只读工具（不能写文件）
    
    Returns:
        工具定义列表
    """
    if mode == 'ask':
        # Ask 模式：只返回只读工具
        readonly_tool_names = ['read_file', 'list_directory', 'search_content']
        return [tool for tool in AGENT_TOOLS 
                if tool['function']['name'] in readonly_tool_names]
    else:
        # Agent 模式：返回所有工具
        return AGENT_TOOLS


def get_tool_names(mode: str = 'agent') -> List[str]:
    """
    获取工具名称列表
    
    Args:
        mode: AI 模式 ('agent' 或 'ask')
    
    Returns:
        工具名称列表
    """
    tools = get_tools_definition(mode)
    return [tool["function"]["name"] for tool in tools]
