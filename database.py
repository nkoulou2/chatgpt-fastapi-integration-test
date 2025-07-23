import sqlite3

connection = sqlite3.connect('LoginData.db')
cursor = connection.cursor()

cmd1 = """CREATE TABLE IF NOT EXISTS USERS(first_name varchar(50),' \
'                                       last_name varchar(50),' \
'                                       email varchar(50) primary key,' \
'                                       password varchar(50) not null)"""


ans = cursor.execute('select * from USERS').fetchall()

for i in ans:
    print(i)