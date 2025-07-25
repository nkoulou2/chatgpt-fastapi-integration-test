import sqlite3

connection = sqlite3.connect('LoginData.db')
cursor = connection.cursor()

cmd1 = """
    CREATE TABLE IF NOT EXISTS USERS ( 
        first_name varchar(50),
       last_name varchar(50),
       email text primary key,
       password blob not null
)
"""

ans = cursor.execute('select * from USERS').fetchall()

for i in ans:
    print(i)
