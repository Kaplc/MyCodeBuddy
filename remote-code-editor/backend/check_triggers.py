import sqlite3

conn = sqlite3.connect('db.sqlite3')
cursor = conn.cursor()

print('=== 检查触发器 ===')
cursor.execute('SELECT name, sql FROM sqlite_master WHERE type="trigger"')
triggers = cursor.fetchall()
if triggers:
    for name, sql in triggers:
        print(f'触发器名: {name}')
        print(f'SQL: {sql}\n')
else:
    print('无触发器\n')

print('=== 检查ai_message表结构 ===')
cursor.execute('SELECT sql FROM sqlite_master WHERE type="table" AND name="ai_message"')
result = cursor.fetchone()
if result:
    print(result[0])
else:
    print('未找到ai_message表')

conn.close()
