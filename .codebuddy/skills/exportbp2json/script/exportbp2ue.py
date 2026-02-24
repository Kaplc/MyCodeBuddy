#!/usr/bin/env python3
"""
Unreal Engine 4.18 Python 命令执行脚本
适配UE4.18版本的API和功能
Author: UE Python Assistant
Version: 1.0.0
Description: 在Unreal Engine 4.18编辑器中执行Python命令和脚本
"""

import sys
import os
import subprocess
import argparse
import json
import time
from pathlib import Path
from typing import List, Optional, Dict, Any

class UE418PythonExecutor:
    """Unreal Engine 4.18 Python命令执行器"""
    
    def __init__(self, unreal_path: str = None, project_path: str = None):
        """
        初始化UE4.18 Python执行器
        
        参数:
            unreal_path: Unreal Engine 4.18可执行文件路径
            project_path: UE4.18项目文件路径(.uproject)
        """
        self.unreal_path = unreal_path
        self.project_path = project_path
        self.setup_paths()
    
    def setup_paths(self):
        """自动检测Unreal Engine 4.18和项目路径"""
        if not self.unreal_path:
            # 尝试自动查找Unreal Engine 4.18路径
            self.unreal_path = self.find_unreal_editor_418()
        
        if not self.project_path:
            # 尝试在当前目录或上级目录查找项目文件
            self.project_path = self.find_uproject_file()
    
    def find_unreal_editor_418(self) -> Optional[str]:
        """查找Unreal Engine 4.18编辑器可执行文件"""
        # UE4.18常见安装路径
        common_paths = [
            # Windows
            r"..\..\..\..\..\..\..\UE4181\Engine\Binaries\Win64\UE4Editor-Cmd.exe",
        ]
            
        # 检查注册表或常见安装位置
        for path in common_paths:
            abspath = os.path.abspath(path)
            print(abspath)
            if os.path.exists(abspath):
                return abspath
        return None
    
    def find_uproject_file(self, start_dir: str = None) -> Optional[str]:
        """查找.uproject文件"""
        if not start_dir:
            start_dir = os.getcwd()
        
        # 在当前目录查找
        for file in os.listdir(start_dir):
            if file.endswith('.uproject'):
                return os.path.join(start_dir, file)
        
        # 在父目录查找
        parent_dir = os.path.dirname(start_dir)
        if parent_dir and parent_dir != start_dir:
            return self.find_uproject_file(parent_dir)
        
        return None
    
    def execute_script(self, script_content: str, wait_for_exit: bool = True) -> bool:
        """
        执行多行Python脚本
        
        参数:
            script_content: Python脚本内容
            wait_for_exit: 是否等待脚本执行完成
            
        返回:
            执行是否成功
        """
        # 将脚本保存到临时文件
        temp_script = os.path.join(os.getcwd(), "temp_ue418_script.py")
        
        try:
            with open(temp_script, 'w', encoding='utf-8') as f:
                f.write(script_content)
            
            # 执行脚本文件
            return self.execute_file(temp_script, [], wait_for_exit)
        finally:
            # 清理临时文件
            if os.path.exists(temp_script):
                os.remove(temp_script)
    
    def execute_file(self, script_path: str, argv: [], wait_for_exit: bool = True) -> bool:
        """
        执行Python脚本文件
        
        参数:
            script_path: Python脚本文件路径
            wait_for_exit: 是否等待脚本执行完成
            
        返回:
            执行是否成功
        """
        if not os.path.exists(script_path):
            print(f"错误: 脚本文件不存在: {script_path}")
            return False
        
        # UE4.18可以直接执行脚本文件
        cmd = [self.unreal_path]
        
        if self.project_path:
            cmd.append(self.project_path)
        
        cmd.extend(["-run=py", os.path.abspath(script_path)])
        cmd.extend(argv)
        
        cmd.extend([
            "-SkipCompile",
            "-NoSimplygon",
            "-NoPAScan",
            "-NoInitAsset",
            "-miltiprocess",
            "-UTF8Output",
            "-stdout",
            "-FullStdOutLogOutput"
        ])
        
        if wait_for_exit:
            cmd.append("-unattended")
            cmd.append("-nologtimes")
            cmd.append("-nosplash")
        
        print(f"执行脚本文件: {' '.join(cmd)}")
        
        try:
            if wait_for_exit:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    encoding='utf-8',
                    check=False
                )
                
                if result.returncode == 0:
                    print("脚本执行成功")
                    #if result.stdout:
                    #    print(f"输出:\n{result.stdout}")
                    return True
                else:
                    print(f"脚本执行失败，返回码: {result.returncode}")
                    if result.stderr:
                        print(f"错误:\n{result.stderr}")
                    return False
            else:
                subprocess.Popen(
                    cmd,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                print("脚本已在后台执行")
                return True
                
        except Exception as e:
            print(f"执行脚本时发生错误: {str(e)}")
            return False
    
    def execute_repl(self):
        """启动交互式Python REPL"""
        if not self.unreal_path:
            print("错误: 未找到Unreal Engine 4.18编辑器路径")
            return False
        
        if not self.project_path:
            print("警告: 未找到项目文件，将以空项目启动")
        
        # 启动UE4.18 Editor但不执行特定命令
        cmd = [self.unreal_path]
        
        if self.project_path:
            cmd.append(self.project_path)
        
        cmd.extend([
            "-SkipCompile",
            "-NoSimplygon",
            "-NoPAScan",
            "-NoInitAsset",
            "-miltiprocess",
            "-stdout",
            "-FullStdOutLogOutput"
        ])
        
        print(f"启动UE4.18 Editor交互模式: {' '.join(cmd)}")
        
        try:
            subprocess.Popen(cmd)
            print("UE4.18 Editor已启动，请在编辑器中打开Python交互模式")
            print("注意: UE4.18可能需要手动启用Python插件")
            return True
        except Exception as e:
            print(f"启动UE4.18 Editor时发生错误: {str(e)}")
            return False
    
    def list_plugins(self) -> bool:
        """列出已安装的Python插件 - UE4.18版本"""
        command = """
try:
    import unreal
    print("=== Unreal Engine 4.18 Python 插件列表 ===")
    
    # UE4.18中获取插件信息的方式可能不同
    # 这里使用文件系统方式查找Python相关插件
    import os
    engine_plugins_dir = os.path.join(os.path.dirname(unreal.Paths.engine_dir()), "Plugins")
    project_plugins_dir = os.path.join(unreal.Paths.project_dir(), "Plugins")
    
    python_plugins = []
    
    # 查找引擎插件目录
    if os.path.exists(engine_plugins_dir):
        for plugin in os.listdir(engine_plugins_dir):
            plugin_path = os.path.join(engine_plugins_dir, plugin)
            if os.path.isdir(plugin_path):
                # 检查是否是Python插件
                if "python" in plugin.lower() or "Python" in plugin:
                    python_plugins.append(("Engine", plugin, plugin_path))
    
    # 查找项目插件目录
    if os.path.exists(project_plugins_dir):
        for plugin in os.listdir(project_plugins_dir):
            plugin_path = os.path.join(project_plugins_dir, plugin)
            if os.path.isdir(plugin_path):
                # 检查是否是Python插件
                if "python" in plugin.lower() or "Python" in plugin:
                    python_plugins.append(("Project", plugin, plugin_path))
    
    if python_plugins:
        for plugin_type, plugin_name, plugin_path in python_plugins:
            print(f"{plugin_type} 插件: {plugin_name}")
            print(f"  路径: {plugin_path}")
    else:
        print("未找到Python插件")
        print("请确保已安装Python插件: https://github.com/20tab/UnrealEnginePython")
        
except Exception as e:
    print(f"获取插件信息时出错: {str(e)}")
        """
        
        return self.execute_script(command)
    
    def check_python_plugin(self) -> bool:
        """检查Python插件是否已安装和启用"""
        command = """
try:
    import unreal
    print("✓ Python插件已正确安装和启用")
    print("✓ 可以正常导入unreal模块")
    
    # 测试基本功能
    actors = unreal.EditorLevelLibrary.get_all_level_actors()
    print(f"✓ 当前关卡中有 {len(actors)} 个Actor")
    
    return True
except ImportError:
    print("✗ 无法导入unreal模块")
    print("请确保已安装Python插件: https://github.com/20tab/UnrealEnginePython")
    return False
except Exception as e:
    print(f"✗ Python插件测试失败: {str(e)}")
    return False
        """
        
        return self.execute_script(command)

def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='Unreal Engine 4.18 Python命令执行脚本',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s -c "import unreal; print('Hello UE4.18')"
  %(prog)s -f "my_script.py"
  %(prog)s -e "print('Hello UE')"
  %(prog)s -a "WidgetBlueprint'/Game/UMG/WebViewTestUI.WebViewTestUI'"
  %(prog)s --repl
  %(prog)s --list-plugins
  %(prog)s --check-plugin
        """
    )
    
    parser.add_argument('--ue-path', help='Unreal Engine 4.18编辑器路径')
    parser.add_argument('--project', help='UE4.18项目文件路径(.uproject)')
    parser.add_argument('--no-wait', action='store_true', help='不等待命令执行完成')
    parser.add_argument('-a', '--asset', help='蓝图路径')
    
    # 执行模式
    mode_group = parser.add_mutually_exclusive_group(required=True)
    mode_group.add_argument('-f', '--file', help='执行Python脚本文件')
    mode_group.add_argument('-e', '--execute', help='执行多行Python代码')
    mode_group.add_argument('--repl', action='store_true', help='启动交互式Python REPL')
    mode_group.add_argument('--list-plugins', action='store_true', help='列出已安装的Python插件')
    mode_group.add_argument('--check-plugin', action='store_true', help='检查Python插件状态')
    
    args, unknown = parser.parse_known_args()
    unknown.insert(1, args.asset)
    
    # 创建执行器
    executor = UE418PythonExecutor(args.ue_path, args.project)
    
    if not executor.unreal_path:
        print("错误: 未找到Unreal Engine 4.18编辑器")
        print("请通过--ue-path参数指定编辑器路径，例如:")
        print(r'  --ue-path "C:\Program Files\Epic Games\UE_4.18\Engine\Binaries\Win64\UE4Editor-Cmd.exe"')
        print("或确保已正确安装Unreal Engine 4.18")
        return 1
    
    # 根据参数执行相应操作
    wait_for_exit = not args.no_wait
    
    if args.file:
        return 0 if executor.execute_file(args.file, unknown, wait_for_exit) else 1
    elif args.execute:
        return 0 if executor.execute_script(args.execute, wait_for_exit) else 1
    elif args.repl:
        return 0 if executor.execute_repl() else 1
    elif args.list_plugins:
        return 0 if executor.list_plugins() else 1
    elif args.check_plugin:
        return 0 if executor.check_python_plugin() else 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())