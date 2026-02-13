"""简单的AI测试"""
import os
from dotenv import load_dotenv
load_dotenv()

api_key = os.getenv("ZHIPU_API_KEY")
print(f"API Key: {api_key[:20]}...")

from zhipuai import ZhipuAI
client = ZhipuAI(api_key=api_key)

print("发送测试消息...")
response = client.chat.completions.create(
    model="glm-4-flash",
    messages=[{"role": "user", "content": "你好，请用一句话回复"}],
    max_tokens=50
)

print(f"AI回复: {response.choices[0].message.content}")
print("测试成功!")