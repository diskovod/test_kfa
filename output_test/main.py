

import os

import MySQLdb

db_conn = MySQLdb.connect(host = 'localhost', user = 'root', passwd = '123456', db = 'kfa_auto')
cursor = db_conn.cursor()
dev_data = cursor.execute("Select * from device_group")
data = cursor.fetchone()

print(data)

