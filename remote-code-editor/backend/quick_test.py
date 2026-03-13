import requests
import json
import time

# Test with explicit task
workflow = {
    'version': '2.0',
    'nodes': [
        {'id': '1', 'type': 'input', 'config': {'key': 'input'}},
        {'id': '2', 'type': 'agent', 'config': {
            'name': 'general_agent', 
            'task': '你是一个AI助手，请回复用户的消息'
        }},
        {'id': '3', 'type': 'output', 'config': {'key': 'result'}}
    ],
    'edges': [
        {'source': '1', 'target': '2'},
        {'source': '2', 'target': '3'}
    ]
}

print('Testing workflow with explicit task...')
start = time.time()
try:
    r = requests.post('http://localhost:8000/api/workflow/run/', json={'graph': workflow, 'input': '你好，请介绍一下自己'}, timeout=60)
    print(f'Status: {r.status_code}')
    print(f'Time: {time.time()-start:.1f}s')
    result = r.json()
    print(f'Response: {json.dumps(result, indent=2, ensure_ascii=False)[:500]}')
except Exception as e:
    print(f'Error: {e}')
