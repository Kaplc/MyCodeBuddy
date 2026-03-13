#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Agent 功能测试脚本（简化版）
"""
import os
import sys
import json
from pathlib import Path

# 添加 backend 目录到 Python 路径
backend_dir = Path(__file__).parent / 'remote-code-editor' / 'backend'
sys.path.insert(0, str(backend_dir))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()

from config.ai_config import get_models, get_model_by_id
from services.ai_service import AIService


def test_1_ai_config():
    """测试 1: AI 配置读取"""
    print("\n" + "="*60)
    print("  测试 1: AI 配置读取")
    print("="*60)
    
    try:
        models = get_models()
        print(f"[OK] 成功读取 {len(models)} 个模型:")
        for model in models:
            print(f"  - {model.get('name')} ({model.get('id')})")
        
        # 检查 GLM4.7-Flash 是否存在
        glm_4_7 = get_model_by_id('glm-4.7-flash')
        if glm_4_7:
            print(f"\n[OK] GLM4.7-Flash 模型已配置")
            print(f"  描述: {glm_4_7.get('description')}")
            return True
        else:
            print(f"\n[FAIL] GLM4.7-Flash 模型未找到")
            return False
            
    except Exception as e:
        print(f"[FAIL] 配置读取失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_2_ai_service():
    """测试 2: AI 服务基础对话"""
    print("\n" + "="*60)
    print("  测试 2: AI 服务基础对话")
    print("="*60)
    
    import asyncio
    
    try:
        from django.conf import settings
        
        if not settings.ZHIPU_API_KEY:
            print("[FAIL] ZHIPU_API_KEY 未配置")
            return False
        
        api_service = AIService(settings.ZHIPU_API_KEY)
        
        # 设置模型
        api_service.set_model('glm-4.7-flash')
        print(f"[OK] AI 服务初始化成功，模型: glm-4.7-flash")
        
        # 同步对话测试
        messages = [{"role": "user", "content": "你好，请用一句话介绍自己"}]
        
        print("正在发送测试请求...")
        response = asyncio.run(api_service.chat_sync(messages))
        
        if response:
            print(f"[OK] AI 响应成功")
            print(f"  响应: {response[:100]}...")
            return True
        else:
            print("[FAIL] AI 响应为空")
            return False
            
    except Exception as e:
        print(f"[FAIL] AI 服务测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_3_agent_tools():
    """测试 3: Agent 工具定义"""
    print("\n" + "="*60)
    print("  测试 3: Agent 工具定义")
    print("="*60)
    
    try:
        from services.agent_tools import AGENT_TOOLS, get_tools_definition
        
        print(f"[OK] 成功加载 {len(AGENT_TOOLS)} 个工具:")
        
        # 显示前5个工具
        for tool in AGENT_TOOLS[:5]:
            func = tool.get('function', {})
            print(f"  - {func.get('name')}: {func.get('description')[:50]}...")
        
        if len(AGENT_TOOLS) > 5:
            print(f"  ... 还有 {len(AGENT_TOOLS) - 5} 个工具")
        
        # 测试获取不同模式的工具
        agent_tools = get_tools_definition('agent')
        ask_tools = get_tools_definition('ask')
        
        print(f"\n[OK] Agent 模式工具数: {len(agent_tools)}")
        print(f"[OK] Ask 模式工具数: {len(ask_tools)} (只读)")
        
        return True
        
    except Exception as e:
        print(f"[FAIL] 工具定义测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_4_agent_executor():
    """测试 4: Agent 工具执行器"""
    print("\n" + "="*60)
    print("  测试 4: Agent 工具执行器")
    print("="*60)
    
    import asyncio
    
    try:
        from services.agent_tools import AgentToolExecutor
        
        # 设置临时测试目录
        test_workspace = backend_dir / 'workspaces' / 'test_workspace'
        test_workspace.mkdir(parents=True, exist_ok=True)
        
        executor = AgentToolExecutor(str(test_workspace))
        print(f"[OK] 工具执行器初始化成功")
        print(f"  工作区: {test_workspace}")
        
        # 测试 create_directory
        result = asyncio.run(executor.execute_tool('create_directory', {'path': 'test_dir'}))
        if result.get('success'):
            print(f"[OK] create_directory 工具执行成功")
        else:
            print(f"[FAIL] create_directory 失败: {result}")
            return False
        
        # 测试 write_file
        test_file = 'test_dir/test.txt'
        test_content = 'Hello, Agent!'
        result = asyncio.run(executor.execute_tool('write_file', {
            'path': test_file,
            'content': test_content
        }))
        if result.get('success'):
            print(f"[OK] write_file 工具执行成功")
        else:
            print(f"[FAIL] write_file 失败: {result}")
            return False
        
        # 测试 read_file
        result = asyncio.run(executor.execute_tool('read_file', {'path': test_file}))
        if result.get('success') and result.get('content') == test_content:
            print(f"[OK] read_file 工具执行成功")
            print(f"  读取内容: {result.get('content')}")
        else:
            print(f"[FAIL] read_file 失败: {result}")
            return False
        
        # 测试 list_directory
        result = asyncio.run(executor.execute_tool('list_directory', {'path': ''}))
        if result.get('success'):
            print(f"[OK] list_directory 工具执行成功")
            print(f"  发现 {result.get('count')} 项")
        else:
            print(f"[FAIL] list_directory 失败: {result}")
            return False
        
        return True
        
    except Exception as e:
        print(f"[FAIL] 工具执行器测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主测试函数"""
    print("="*60)
    print("  Agent 功能测试套件")
    print("="*60)
    
    results = {}
    
    # 运行测试
    results['配置读取'] = test_1_ai_config()
    results['AI服务'] = test_2_ai_service()
    results['工具定义'] = test_3_agent_tools()
    results['工具执行'] = test_4_agent_executor()
    
    # 汇总结果
    print("\n" + "="*60)
    print("  测试结果汇总")
    print("="*60)
    
    passed = sum(1 for v in results.values() if v is True)
    failed = sum(1 for v in results.values() if v is False)
    
    for test_name, result in results.items():
        if result is True:
            status = "[OK]"
        else:
            status = "[FAIL]"
        print(f"{status:10} {test_name}")
    
    print(f"\n总计: {passed} 通过, {failed} 失败")
    
    if failed == 0:
        print("\n所有核心测试通过！Agent 功能正常。")
    else:
        print(f"\n有 {failed} 个测试失败，请检查相关配置和服务状态。")


if __name__ == '__main__':
    main()
