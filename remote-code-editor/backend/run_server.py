#!/usr/bin/env python
"""
Django后端启动脚本
"""
import os
import sys
from pathlib import Path

# 添加当前目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.resolve()))

# 确保工作目录存在
from dotenv import load_dotenv
load_dotenv()

WORKSPACE_PATH = os.getenv('WORKSPACE_PATH') or str(Path.home() / 'code-editor-workspace')
Path(WORKSPACE_PATH).mkdir(parents=True, exist_ok=True)

print("Remote Code Editor starting...")
print(f"Workspace: {WORKSPACE_PATH}")

# 设置Django设置模块
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

if __name__ == '__main__':
    # 使用daphne ASGI服务器（支持WebSocket）
    try:
        from daphne.cli import CommandLineInterface
        from daphne.endpoints import build_endpoint_description_strings
        print("使用 daphne ASGI 服务器启动（支持WebSocket）...")
        
        # 构建daphne命令参数
        sys.argv = ['daphne', '-b', '0.0.0.0', '-p', '8000', 'config.asgi:application']
        
        # 启动daphne服务器
        CommandLineInterface().entrypoint()
    except ImportError:
        print("错误：未找到 daphne，请先安装: pip install daphne")
        sys.exit(1)
    except Exception as e:
        print(f"启动失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
