# coding=utf-8
import struct
import datetime
import snap7
import MySQLdb
from consts import *
from models import *

db = MySQLdb.connect(HOSTNAME, USERNAME, PASSWORD, DATABASE)
# 设置PLC的连接地址
ip = '192.168.18.17'
rack = 0
slot = 2
tcpport = 102

# 建立连接
client = snap7.client.Client()
client.connect(ip, rack, slot, tcpport)

# 从测试用test表里获取数据
# result = client.db_read(db_number=10, start=0, size=12)
# b=''.join(chr(i)for i in result)
# db1_tuple = struct.unpack('=????if', b)
# with db as cur:
#     for a in range(len(db1_tuple)):
#         print '1'
#         sql = "insert into test(str, variable) values(%s, %s)"
#         print (db1_tuple[a], datetime.datetime.now(), '2', 'DB10')
#         cur.execute(sql, (db1_tuple[a], 'DB10'))

result = client.db_read(db_number=10, start=0, size=12)
b=''.join(chr(i)for i in result)
db1_tuple = struct.unpack('=????if', b)
for a in range(len(db1_tuple)):
    time = datetime.datetime.now()
    value = Value(variable_name='DB10', get_time=time, up_time=5, value=db1_tuple[a])
    session.add(value)
session.commit()


# result = client.db_read(db_number=1, start=0, size=8)
# b=''.join(chr(i)for i in result)
# print struct.unpack('=ff', b)

# result = client.ab_read(start=1, size=10)
# b=''.join(chr(i)for i in result)
# print struct.unpack('', b)


client.db_get(db_number=10)


# 断开连接
client.disconnect()
client.destroy()