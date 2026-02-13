#!/usr/bin/env python
"""
Django管理脚本
"""
import os
import sys


def main():
    """运行管理命令"""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "无法导入Django。请确保已安装Django并且 "
            "PYTHONPATH环境变量中包含Django项目。"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
