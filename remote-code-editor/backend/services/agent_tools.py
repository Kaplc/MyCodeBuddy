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
        try:
            file_path = self._resolve_path(path)
            
            # 确保父目录存在
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 写入文件
            file_path.write_text(content, encoding='utf-8')
            
            return {
                "success": True,
                "path": path,
                "message": f"文件已保存: {path}",
                "size": len(content)
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
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
