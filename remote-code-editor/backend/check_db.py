import sqlite3

conn = sqlite3.connect('db.sqlite3')
cursor = conn.cursor()

print('检查数据库表结构...')
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
print('\n所有表:', tables)

if tables:
    cursor.execute('PRAGMA table_info(ai_message)')
    print('\nai_message 表结构:')
    for col in cursor.fetchall():
        print(f'  {col}')
else:
    print('数据库中没有表，需要先运行 migrate')

conn.close()
