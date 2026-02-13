"""快速AI测试"""
import os
import sys

# 加载环境变量
from dotenv import load_dotenv
load_dotenv()

print("="*50)
print("AI API 连接测试")
print("="*50)

# 1. 检查API Key
api_key = os.getenv("ZHIPU_API_KEY")
print(f"\n1. API Key检查:")
if api_key:
    print(f"   ✓ 存在 (长度: {len(api_key)})")
else:
    print("   ✗ 未找到")
    sys.exit(1)

# 2. 初始化客户端
print(f"\n2. 初始化智谱AI客户端:")
try:
    from zhipuai import ZhipuAI
    client = ZhipuAI(api_key=api_key)
    print("   ✓ 初始化成功")
except Exception as e:
    print(f"   ✗ 初始化失败: {e}")
    sys.exit(1)

# 3. 发送请求
print(f"\n3. 发送测试请求 (模型: glm-4-flash):")
try:
    response = client.chat.completions.create(
        model="glm-4-flash",
        messages=[{"role": "user", "content": "你好，请用一句话介绍你自己"}],
        max_tokens=50
    )
    
    content = response.choices[0].message.content
    print(f"   ✓ 请求成功!")
    print(f"\n   AI响应: {content}")
    
except Exception as e:
    print(f"   ✗ 请求失败: {e}")
    sys.exit(1)

print("\n" + "="*50)
print("✅ AI功能测试通过!")
print("="*50)