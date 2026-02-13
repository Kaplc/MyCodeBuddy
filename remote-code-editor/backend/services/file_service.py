"""
文件服务模块
提供文件系统操作的核心逻辑
"""
import os
import aiofiles
import asyncio
from pathlib import Path
from datetime import datetime
from typing import List, Optional
from pathvalidate import sanitize_filename


class FileService:
    """文件服务类"""
    
    def __init__(self, workspace_path: str):
        """
        初始化文件服务
        
        Args:
            workspace_path: 工作目录根路径
        """
        self.workspace = Path(workspace_path).resolve() if workspace_path else None
        self._locks: dict = {}  # 文件锁，用于处理并发
        self._global_lock: Optional[asyncio.Lock] = None  # 延迟创建全局锁
    
    def _get_global_lock(self) -> asyncio.Lock:
        """获取或创建全局锁（延迟创建，避免在非事件循环线程中创建）"""
        if self._global_lock is None:
            self._global_lock = asyncio.Lock()
        return self._global_lock
    
    def _resolve_path(self, relative_path: str) -> Path:
        """
        解析相对路径为绝对路径，并验证安全性
        
        Args:
            relative_path: 相对于工作目录的路径
        
        Returns:
            解析后的绝对路径
        
        Raises:
            ValueError: 如果路径尝试越出工作目录或工作区未设置
        """
        # 检查工作区是否设置
        if not self.workspace:
            raise ValueError("工作区未设置，请先选择工作区")
        
        # 清理路径，防止路径遍历攻击
        relative_path = relative_path.lstrip("/\\")
        
        # 如果路径为空，返回工作区根目录
        if not relative_path:
            return self.workspace
        
        # 解析绝对路径
        abs_path = (self.workspace / relative_path).resolve()
        
        # 验证路径在工作目录内
        try:
            abs_path.relative_to(self.workspace)
        except ValueError:
            raise ValueError(f"路径越出工作目录: {relative_path}")
        
        return abs_path
    
    def _get_file_lock(self, path: Path) -> asyncio.Lock:
        """获取或创建文件锁"""
        path_str = str(path)
        if path_str not in self._locks:
            self._locks[path_str] = asyncio.Lock()
        return self._locks[path_str]
    
    async def list_directory(self, relative_path: str) -> List[dict]:
        """
        列出目录内容
        
        Args:
            relative_path: 相对路径
        
        Returns:
            文件和目录信息列表
        """
        # 检查工作区是否设置
        if not self.workspace:
            return []
        
        path = self._resolve_path(relative_path)
        
        if not path.exists():
            raise FileNotFoundError(f"目录不存在: {relative_path}")
        
        if not path.is_dir():
            raise NotADirectoryError(f"路径不是目录: {relative_path}")
        
        items = []
        for item in sorted(path.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower())):
            # 跳过隐藏文件
            if item.name.startswith('.'):
                continue
            
            item_info = {
                "name": item.name,
                "path": str(item.relative_to(self.workspace)),
                "is_dir": item.is_dir()
            }
            
            if item.is_file():
                stat = item.stat()
                item_info["size"] = stat.st_size
                item_info["modified"] = datetime.fromtimestamp(stat.st_mtime).isoformat()
            
            items.append(item_info)
        
        return items
    
    async def read_file(self, relative_path: str) -> str:
        """
        读取文件内容
        
        Args:
            relative_path: 相对路径
        
        Returns:
            文件内容
        """
        if not self.workspace:
            raise FileNotFoundError("工作区未设置")
        
        path = self._resolve_path(relative_path)
        
        if not path.exists():
            raise FileNotFoundError(f"文件不存在: {relative_path}")
        
        if path.is_dir():
            raise IsADirectoryError(f"路径是目录: {relative_path}")
        
        # 使用文件锁
        lock = self._get_file_lock(path)
        async with lock:
            async with aiofiles.open(path, mode='r', encoding='utf-8') as f:
                content = await f.read()
        
        return content
    
    async def save_file(self, relative_path: str, content: str) -> None:
        """
        保存文件内容
        
        Args:
            relative_path: 相对路径
            content: 文件内容
        """
        if not self.workspace:
            raise PermissionError("工作区未设置")
        
        path = self._resolve_path(relative_path)
        
        # 确保父目录存在
        path.parent.mkdir(parents=True, exist_ok=True)
        
        # 使用文件锁
        lock = self._get_file_lock(path)
        async with lock:
            async with aiofiles.open(path, mode='w', encoding='utf-8') as f:
                await f.write(content)
    
    async def create(self, relative_path: str, is_dir: bool = False) -> str:
        """
        创建文件或目录
        
        Args:
            relative_path: 相对路径
            is_dir: 是否创建目录
        
        Returns:
            创建的路径
        """
        if not self.workspace:
            raise PermissionError("工作区未设置")
        
        # 验证文件名
        name = Path(relative_path).name
        safe_name = sanitize_filename(name)
        if safe_name != name:
            raise ValueError(f"文件名包含非法字符: {name}")
        
        path = self._resolve_path(relative_path)
        
        if path.exists():
            raise FileExistsError(f"文件或目录已存在: {relative_path}")
        
        if is_dir:
            path.mkdir(parents=True, exist_ok=False)
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.touch()
        
        return str(path.relative_to(self.workspace))
    
    async def rename(self, old_relative_path: str, new_name: str) -> str:
        """
        重命名文件或目录
        
        Args:
            old_relative_path: 原相对路径
            new_name: 新名称
        
        Returns:
            新的相对路径
        """
        if not self.workspace:
            raise PermissionError("工作区未设置")
        
        # 验证新文件名
        safe_name = sanitize_filename(new_name)
        if safe_name != new_name:
            raise ValueError(f"文件名包含非法字符: {new_name}")
        
        old_path = self._resolve_path(old_relative_path)
        
        if not old_path.exists():
            raise FileNotFoundError(f"文件或目录不存在: {old_relative_path}")
        
        new_path = old_path.parent / new_name
        
        if new_path.exists():
            raise FileExistsError(f"目标名称已存在: {new_name}")
        
        old_path.rename(new_path)
        
        return str(new_path.relative_to(self.workspace))
    
    async def delete(self, relative_path: str) -> None:
        """
        删除文件或目录
        
        Args:
            relative_path: 相对路径
        """
        if not self.workspace:
            raise PermissionError("工作区未设置")
        
        import shutil
        
        path = self._resolve_path(relative_path)
        
        if not path.exists():
            raise FileNotFoundError(f"文件或目录不存在: {relative_path}")
        
        if path.is_dir():
            shutil.rmtree(path)
        else:
            path.unlink()
    
    async def exists(self, relative_path: str) -> bool:
        """
        检查文件或目录是否存在
        
        Args:
            relative_path: 相对路径
        
        Returns:
            是否存在
        """
        if not self.workspace:
            return False
        
        path = self._resolve_path(relative_path)
        return path.exists()
