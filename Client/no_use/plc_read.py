# coding=utf-8
import time
import re
import struct
import snap7
from snap7 import util


def print_row(data):
    """print a single db row in chr and str
    """
    index_line = ""
    pri_line1 = ""
    chr_line2 = ""
    asci = re.compile('[a-zA-Z0-9 ]')

    for i, xi in enumerate(data):
        # index
        if not i % 5:
            diff = len(pri_line1) - len(index_line)
            i = str(i)
            index_line += diff * ' '
            index_line += i
            # i = i + (ws - len(i)) * ' ' + ','

        # byte array line
        str_v = str(xi)
        pri_line1 += str(xi) + ','
        # char line
        c = chr(xi)
        c = c if asci.match(c) else ' '
        # align white space
        w = len(str_v)
        c = c + (w - 1) * ' ' + ','
        chr_line2 += c

    print(index_line)
    print(pri_line1)
    print(chr_line2)

# 设置PLC的连接地址
ip = '192.168.18.17'  # PLC的ip地址
rack = 0  # 机架号
slot = 2  # 插槽号
tcpport = 102  # TCP端口号


class PythonPLC(object):

    # 设置PLC的连接地址
    ip = '192.168.18.17'  # PLC的ip地址
    rack = 0  # 机架号
    slot = 2  # 插槽号
    tcpport = 102  # TCP端口号

    def __init__(self):
        pass

    def __enter__(self):
        self.client = snap7.client.Client()
        self.client.connect(ip, rack, slot, tcpport)
        return self.client

    def __exit__(self, *args):
        self.client.disconnect()
        self.client.destroy()


# db4_data = struct.unpack('8?', db4)
# print db4_data
# time_read_s = time.time()
# db = client.db_get(1)
# time_read_e = time.time()
# print time_read_e - time_read_s

# time1 = time.time()
# db4 = client.db_read(1, 0, 4)
# print util.get_real(db4, 0)
# time2 = time.time()
# print time2-time1

# db = []
# db4 = client.db_get(4)
# print db4
# for b in db4:
#     db4_data = struct.unpack('!?', b)
#     db.append(db4_data)
# print db

with PythonPLC() as db:
    db = db.db_read(1, 0, 4)
value = struct.unpack('!{}'.format('f'), db)[0]
print value
print util.get_real(db, 0)


