#!/usr/bin/env python
"""
Django后端启动脚本
"""
import os
import sys
from pathlib import Path
import shutil

# 添加当前目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.resolve()))

# 检查并创建 .env 文件
env_file = Path(__file__).parent / '.env'
env_example_file = Path(__file__).parent / '.env.example'

if not env_file.exists():
    if env_example_file.exists():
        print(f"[提示] 未找到 .env 文件，正在从模板创建...")
        shutil.copy(env_example_file, env_file)
        print(f"[成功] 已创建 .env 文件: {env_file}")
        print(f"[警告] 请编辑 .env 文件并填入真实的 API 密钥后重新启动服务器")
        print(f"       文件位置: {env_file.absolute()}")
    else:
        print(f"[警告] 未找到 .env 文件和 .env.example 模板文件")
        print(f"       请手动创建 .env 文件: {env_file.absolute()}")

# 加载环境变量
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
