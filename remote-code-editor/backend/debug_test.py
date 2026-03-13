import requests
import json

BASE_URL = "http://localhost:8001"

# Test 
workflow = {
    "version": "2.0",
    "nodes": [
        {"id": "1", "type": "input", "config": {"key": "input"}},
        {"id": "2", "type": "agent", "config": {
            "name": "general_agent", 
            "task": "你是一个AI助手，请回复用户的消息"
        }},
        {"id": "3", "type": "output", "config": {"key": "result"}}
    ],
    "edges": [
        {"source": "1", "target": "2"},
        {"source": "2", "target": "3"}
    ]
}

print('Testing on port 8001...')
r = requests.post(f'{BASE_URL}/api/workflow/run/', json={'graph': workflow, 'input': '你好'}, timeout=60)
result = r.json()
print(json.dumps(result, indent=2, ensure_ascii=False)[:500])
