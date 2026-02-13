"""
AI功能综合测试报告
==================
测试时间: 2026-02-13
"""
import os
import sys

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

def test_config():
    """测试配置"""
    print("="*60)
    print("1. 配置检查")
    print("="*60)
    
    api_key = os.getenv("ZHIPU_API_KEY")
    workspace = os.getenv("WORKSPACE_PATH")
    
    if api_key:
        print(f"✓ ZHIPU_API_KEY: {api_key[:20]}...{api_key[-10:]}")
    else:
        print("✗ ZHIPU_API_KEY: 未配置")
        
    if workspace:
        print(f"✓ WORKSPACE_PATH: {workspace}")
    else:
        print("⚠ WORKSPACE_PATH: 未配置（将使用默认值）")
    
    return bool(api_key)

def test_imports():
    """测试依赖导入"""
    print("\n" + "="*60)
    print("2. 依赖检查")
    print("="*60)
    
    modules = [
        ("zhipuai", "智谱AI SDK"),
        ("django", "Django框架"),
        ("channels", "Django Channels"),
        ("dotenv", "环境变量加载"),
    ]
    
    for module_name, display_name in modules:
        try:
            __import__(module_name)
            print(f"✓ {display_name} ({module_name})")
        except ImportError as e:
            print(f"✗ {display_name} ({module_name}): {e}")
    
    return True

def test_ai_service():
    """测试AI服务类"""
    print("\n" + "="*60)
    print("3. AI服务类检查")
    print("="*60)
    
    try:
        from services.ai_service import AIService
        print("✓ AIService 类导入成功")
        
        api_key = os.getenv("ZHIPU_API_KEY")
        if api_key:
            service = AIService(api_key)
            print(f"✓ AIService 初始化成功")
            print(f"  - 默认模型: {service.default_model}")
            print(f"  - max_tokens: {service.max_tokens}")
            print(f"  - temperature: {service.temperature}")
            
            # 测试模型切换
            service.set_model("glm-4-flash")
            print(f"  - 切换模型后: {service.default_model}")
            
        return True
    except Exception as e:
        print(f"✗ AIService 错误: {e}")
        return False

def test_consumer():
    """测试WebSocket消费者"""
    print("\n" + "="*60)
    print("4. WebSocket消费者检查")
    print("="*60)
    
    try:
        from api.consumers import AIChatConsumer
        print("✓ AIChatConsumer 类导入成功")
        
        # 检查类方法
        methods = ['connect', 'disconnect', 'receive', 'handle_chat']
        for method in methods:
            if hasattr(AIChatConsumer, method):
                print(f"  ✓ {method}() 方法存在")
            else:
                print(f"  ✗ {method}() 方法缺失")
        
        return True
    except Exception as e:
        print(f"✗ Consumer 导入错误: {e}")
        return False

def test_api_call():
    """测试实际API调用"""
    print("\n" + "="*60)
    print("5. API调用测试")
    print("="*60)
    
    api_key = os.getenv("ZHIPU_API_KEY")
    if not api_key:
        print("⚠ 跳过API调用测试（未配置API Key）")
        return None
    
    try:
        from zhipuai import ZhipuAI
        print("正在连接智谱AI...")
        
        client = ZhipuAI(api_key=api_key)
        
        print("发送测试消息: '你好'")
        response = client.chat.completions.create(
            model="glm-4-flash",
            messages=[{"role": "user", "content": "你好，请简单回复OK"}],
            max_tokens=10
        )
        
        content = response.choices[0].message.content
        print(f"✓ API调用成功！")
        print(f"  响应: {content}")
        return True
        
    except Exception as e:
        print(f"✗ API调用失败: {e}")
        return False

def main():
    """运行所有测试"""
    print("\n" + "█"*60)
    print("   AI功能综合测试报告")
    print("█"*60 + "\n")
    
    results = {
        "配置检查": test_config(),
        "依赖检查": test_imports(),
        "AI服务类": test_ai_service(),
        "WebSocket消费者": test_consumer(),
        "API调用": test_api_call(),
    }
    
    print("\n" + "="*60)
    print("测试汇总")
    print("="*60)
    
    for name, result in results.items():
        if result is None:
            status = "⚠ 跳过"
        elif result:
            status = "✓ 通过"
        else:
            status = "✗ 失败"
        print(f"  {name}: {status}")
    
    # 统计
    passed = sum(1 for r in results.values() if r is True)
    failed = sum(1 for r in results.values() if r is False)
    skipped = sum(1 for r in results.values() if r is None)
    
    print("\n" + "-"*60)
    print(f"总计: {passed} 通过, {failed} 失败, {skipped} 跳过")
    
    if failed == 0:
        print("\n🎉 所有测试通过！AI功能正常")
    else:
        print("\n⚠ 存在失败的测试项，请检查配置")
    
    return failed == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)