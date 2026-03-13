import os

logs_dir = r'c:\Users\v_zhyyzheng\Desktop\MyCodeBuddy\remote-code-editor\backend\logs'
for f in ['django.log', 'api.log', 'frontend.log', 'server_stdout.log']:
    path = os.path.join(logs_dir, f)
    if os.path.exists(path):
        size = os.path.getsize(path)
        mtime = os.path.getmtime(path)
        print(f"{f}: {size} bytes, modified: {mtime}")
    else:
        print(f"{f}: NOT FOUND")
