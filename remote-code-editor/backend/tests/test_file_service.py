"""
文件服务单元测试
"""
import os
import tempfile
import pytest
import asyncio
from pathlib import Path

# 添加父目录到路径
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.file_service import FileService


@pytest.fixture
def temp_workspace():
    """创建临时工作目录"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def file_service(temp_workspace):
    """创建文件服务实例"""
    return FileService(temp_workspace)


class TestFileService:
    """文件服务测试类"""
    
    @pytest.mark.asyncio
    async def test_list_directory_empty(self, file_service):
        """测试列出空目录"""
        items = await file_service.list_directory("")
        assert items == []
    
    @pytest.mark.asyncio
    async def test_create_file(self, file_service, temp_workspace):
        """测试创建文件"""
        result = await file_service.create("test.txt", is_dir=False)
        assert result == "test.txt"
        
        # 验证文件存在
        file_path = Path(temp_workspace) / "test.txt"
        assert file_path.exists()
        assert file_path.is_file()
    
    @pytest.mark.asyncio
    async def test_create_directory(self, file_service, temp_workspace):
        """测试创建目录"""
        result = await file_service.create("test_dir", is_dir=True)
        assert result == "test_dir"
        
        # 验证目录存在
        dir_path = Path(temp_workspace) / "test_dir"
        assert dir_path.exists()
        assert dir_path.is_dir()
    
    @pytest.mark.asyncio
    async def test_create_nested_file(self, file_service, temp_workspace):
        """测试创建嵌套文件"""
        result = await file_service.create("subdir/nested/file.txt", is_dir=False)
        
        # 验证文件存在
        file_path = Path(temp_workspace) / "subdir" / "nested" / "file.txt"
        assert file_path.exists()
    
    @pytest.mark.asyncio
    async def test_read_file(self, file_service, temp_workspace):
        """测试读取文件"""
        # 创建测试文件
        test_file = Path(temp_workspace) / "test.txt"
        test_file.write_text("Hello, World!", encoding='utf-8')
        
        content = await file_service.read_file("test.txt")
        assert content == "Hello, World!"
    
    @pytest.mark.asyncio
    async def test_read_nonexistent_file(self, file_service):
        """测试读取不存在的文件"""
        with pytest.raises(FileNotFoundError):
            await file_service.read_file("nonexistent.txt")
    
    @pytest.mark.asyncio
    async def test_save_file(self, file_service, temp_workspace):
        """测试保存文件"""
        await file_service.save_file("new_file.txt", "New content")
        
        # 验证内容
        file_path = Path(temp_workspace) / "new_file.txt"
        assert file_path.read_text(encoding='utf-8') == "New content"
    
    @pytest.mark.asyncio
    async def test_rename_file(self, file_service, temp_workspace):
        """测试重命名文件"""
        # 创建测试文件
        test_file = Path(temp_workspace) / "old_name.txt"
        test_file.write_text("content", encoding='utf-8')
        
        new_path = await file_service.rename("old_name.txt", "new_name.txt")
        assert new_path == "new_name.txt"
        
        # 验证旧文件不存在，新文件存在
        assert not test_file.exists()
        assert (Path(temp_workspace) / "new_name.txt").exists()
    
    @pytest.mark.asyncio
    async def test_delete_file(self, file_service, temp_workspace):
        """测试删除文件"""
        # 创建测试文件
        test_file = Path(temp_workspace) / "to_delete.txt"
        test_file.write_text("content", encoding='utf-8')
        
        await file_service.delete("to_delete.txt")
        
        # 验证文件不存在
        assert not test_file.exists()
    
    @pytest.mark.asyncio
    async def test_delete_directory(self, file_service, temp_workspace):
        """测试删除目录"""
        # 创建测试目录
        test_dir = Path(temp_workspace) / "to_delete_dir"
        test_dir.mkdir()
        (test_dir / "file.txt").write_text("content", encoding='utf-8')
        
        await file_service.delete("to_delete_dir")
        
        # 验证目录不存在
        assert not test_dir.exists()
    
    @pytest.mark.asyncio
    async def test_path_traversal_prevention(self, file_service):
        """测试路径遍历攻击防护"""
        with pytest.raises(ValueError, match="路径越出工作目录"):
            await file_service.read_file("../../../etc/passwd")
        
        with pytest.raises(ValueError, match="路径越出工作目录"):
            await file_service._resolve_path("..\\..\\windows\\system32")
    
    @pytest.mark.asyncio
    async def test_exists(self, file_service, temp_workspace):
        """测试检查文件存在"""
        # 创建测试文件
        test_file = Path(temp_workspace) / "exists.txt"
        test_file.write_text("content", encoding='utf-8')
        
        assert await file_service.exists("exists.txt") is True
        assert await file_service.exists("not_exists.txt") is False
    
    @pytest.mark.asyncio
    async def test_list_directory_with_files(self, file_service, temp_workspace):
        """测试列出包含文件的目录"""
        # 创建一些文件和目录
        (Path(temp_workspace) / "file1.txt").write_text("content", encoding='utf-8')
        (Path(temp_workspace) / "file2.py").write_text("print('hello')", encoding='utf-8')
        (Path(temp_workspace) / "subdir").mkdir()
        
        items = await file_service.list_directory("")
        
        # 验证结果
        assert len(items) == 3
        names = [item["name"] for item in items]
        assert "file1.txt" in names
        assert "file2.py" in names
        assert "subdir" in names
        
        # 验证目录标记正确
        for item in items:
            if item["name"] == "subdir":
                assert item["is_dir"] is True
            else:
                assert item["is_dir"] is False
