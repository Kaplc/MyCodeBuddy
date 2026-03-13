import os

logs_dir = r'c:\Users\v_zhyyzheng\Desktop\MyCodeBuddy\remote-code-editor\backend\logs'
print("Files in logs directory:")
for f in os.listdir(logs_dir):
    print(f" - {f}")
