with open(r'c:\Users\v_zhyyzheng\Desktop\MyCodeBuddy\remote-code-editor\backend\logs\api.log', 'r', encoding='utf-8') as f:
    lines = f.readlines()
    print(''.join(lines[-10:]))
