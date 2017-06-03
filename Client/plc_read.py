# coding=utf-8
import struct
import snap7


# 设置PLC的连接地址
ip = '192.168.18.17'  # PLC的ip地址
rack = 0  # 机架号
slot = 2  # 插槽号
tcpport = 102  # TCP端口号

client = snap7.client.Client()
client.connect(ip, rack, slot, tcpport)

db4 = client.db_read(4, 0, 8)
db4_data = struct.unpack('!8?', db4)
print db4_data

db = []
db4 = client.db_get(4)
print db4
for b in db4:
    db4_data = struct.unpack('!?', b)
    db.append(db4_data)
print db

client.disconnect()
client.destroy()