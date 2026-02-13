"""
AI功能测试脚本
直接测试智谱AI API连接和响应
"""
import asyncio
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 加载环境变量
from dotenv import load_dotenv
load_dotenv()

from services.ai_service import AIService

async def test_ai_service():
    """测试AI服务"""
    api_key = os.getenv("ZHIPU_API_KEY")
    
    if not api_key:
        print("❌ 错误: 未找到 ZHIPU_API_KEY 环境变量")
        return False
    
    print(f"✓ 找到 API Key: {api_key[:20]}...")
    
    # 初始化服务
    try:
        service = AIService(api_key)
        print(f"✓ AI服务初始化成功，默认模型: {service.default_model}")
    except Exception as e:
        print(f"❌ AI服务初始化失败: {e}")
        return False
    
    # 测试简单对话
    print("\n" + "="*50)
    print("测试1: 简单对话（流式）")
    print("="*50)
    
    messages = [{"role": "user", "content": "请用一句话介绍一下Python语言"}]
    
    try:
        full_response = ""
        async for chunk in service.chat_stream(messages):
            if chunk.get("type") == "content":
                content = chunk.get("content", "")
                full_response += content
                print(content, end="", flush=True)
            elif chunk.get("type") == "error":
                print(f"\n❌ 错误: {chunk.get('message')}")
                return False
        
        print()  # 换行
        if full_response:
            print(f"✓ 流式对话测试成功，响应长度: {len(full_response)} 字符")
        else:
            print("⚠ 响应为空")
            
    except Exception as e:
        print(f"\n❌ 流式对话测试失败: {e}")
        return False
    
    # 测试同步对话
    print("\n" + "="*50)
    print("测试2: 同步对话")
    print("="*50)
    
    messages = [{"role": "user", "content": "1+1等于多少？只回答数字"}]
    
    try:
        result = await service.chat_sync(messages)
        print(f"响应: {result}")
        if result:
            print(f"✓ 同步对话测试成功")
        else:
            print("⚠ 响应为空")
    except Exception as e:
        print(f"❌ 同步对话测试失败: {e}")
        return False
    
    # 测试不同模型
    print("\n" + "="*50)
    print("测试3: 切换模型测试")
    print("="*50)
    
    models = ["glm-4-flash", "glm-4.7-flash"]
    for model in models:
        try:
            service.set_model(model)
            print(f"\n使用模型: {model}")
            messages = [{"role": "user", "content": "你好"}]
            result = await service.chat_sync(messages)
            if result:
                print(f"✓ 模型 {model} 测试成功")
            else:
                print(f"⚠ 模型 {model} 响应为空")
        except Exception as e:
            print(f"❌ 模型 {model} 测试失败: {e}")
    
    print("\n" + "="*50)
    print("🎉 所有测试完成!")
    print("="*50)
    return True

if __name__ == "__main__":
    asyncio.run(test_ai_service())