# coding=utf-8
import struct
import re
import datetime
import time
import ctypes

from subprocess import Popen
from os import path, kill
import snap7
from snap7.snap7types import *
from snap7.snap7exceptions import Snap7Exception
from snap7 import util
import MySQLdb
from consts import *
from models import *


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

# result = client.db_read(db_number=10, start=0, size=12)
# print_row(result)
# b=''.join(chr(i)for i in result)
# db1_tuple = struct.unpack('>????if', b)
# for a in range(len(db1_tuple)):
#     time = datetime.datetime.now()
#     value = Value(variable_name='DB10', get_time=time, up_time=5, value=db1_tuple[a])
#     session.add(value)
# session.commit()


def test():
    result = client.db_read(db_number=11, start=0, size=24)
    print_row(result)
    b=''.join(chr(i)for i in result)
    db1_tuple = struct.unpack('>ffhhfhhi', b)          #ffipfipl
    with db as cur:
        for a in range(len(db1_tuple)):
            print str(db1_tuple)
            sql = "insert into test(str, variable) values(%s, %s)"
            cur.execute(sql, (str(db1_tuple[a]), 'DB11'))

# result = client.db_read(db_number=1, start=0, size=8)
# b=''.join(chr(i)for i in result)
# print struct.unpack('=ff', b)

# result = client.ab_read(start=1, size=10)
# b=''.join(chr(i)for i in result)
# print struct.unpack('', b)






if __name__ == '__main__':
    db = MySQLdb.connect(HOSTNAME, USERNAME, PASSWORD, DATABASE)
    # 设置PLC的连接地址
    ip = '192.168.18.17'  # PLC的ip地址
    rack = 0  # 机架号
    slot = 2  # 插槽号
    tcpport = 102  # TCP端口号

    # 建立连接
    client = snap7.client.Client()
    client.connect(ip, rack, slot, tcpport)

    test()

    a = client.db_read(11, 0, 24)
    db1_tuple = struct.unpack('>ffhhfhhi', a)
    print db1_tuple
    a = client.db_get(11)

    db = 11
    data_items = (S7DataItem * 3)()
    print data_items

    data_items[0].Area = ctypes.c_int32(S7AreaDB)
    data_items[0].WordLen = ctypes.c_int32(S7WLByte)
    data_items[0].Result = ctypes.c_int32(0)
    data_items[0].DBNumber = ctypes.c_int32(db)
    data_items[0].Start = ctypes.c_int32(0)
    data_items[0].Amount = ctypes.c_int32(4)  # reading a REAL, 4 bytes

    data_items[1].Area = ctypes.c_int32(S7AreaDB)
    data_items[1].WordLen = ctypes.c_int32(S7WLByte)
    data_items[1].Result = ctypes.c_int32(0)
    data_items[1].DBNumber = ctypes.c_int32(db)
    data_items[1].Start = ctypes.c_int32(4)
    data_items[1].Amount = ctypes.c_int32(4)  # reading a REAL, 4 bytes

    data_items[2].Area = ctypes.c_int32(S7AreaDB)
    data_items[2].WordLen = ctypes.c_int32(S7WLByte)
    data_items[2].Result = ctypes.c_int32(0)
    data_items[2].DBNumber = ctypes.c_int32(db)
    data_items[2].Start = ctypes.c_int32(8)
    data_items[2].Amount = ctypes.c_int32(2)  # reading an INT, 2 bytes

    # create buffers to receive the data
    # use the Amount attribute on each item to size the buffer
    for di in data_items:
        # create the buffer
        dataBuffer = ctypes.create_string_buffer(di.Amount)
        # get a pointer to the buffer
        pBuffer = ctypes.cast(ctypes.pointer(dataBuffer),
                              ctypes.POINTER(ctypes.c_uint8))
        di.pData = pBuffer

    result, data_items = client.read_multi_vars(data_items)

    result_values = []
    # function to cast bytes to match data_types[] above
    byte_to_value = [util.get_real, util.get_real, util.get_int]

    # unpack and test the result of each read
    for i in range(0, len(data_items)):
        btv = byte_to_value[i]
        di = data_items[i]
        value = btv(di.pData, 0)
        result_values.append(value)

    print result_values
    # test()

    area = snap7.snap7types.areas.DB
    dbnumber = 11
    amount = 24
    start = 0
    a = client.read_area(area, dbnumber, start, amount)
    print print_row(a)

    blockList = client.list_blocks()
    print blockList

    print client.list_blocks_of_type('DB', 11)
    print client.get_block_info('DB', 11)
    print client.get_cpu_state()

    client.set_connection_params("192.168.18.17", 10, 10)
    print client.get_connected()

    a = client.ab_read(start=0, size=10)
    print_row(a)

    result = client.as_db_read(db_number=11, start=0, size=24)
    print_row(result)

    print client.get_pdu_length()
    for i in range(5, 10):
        pduRequested = client.get_param(i)
        pduSize = client.get_pdu_length()
        print pduRequested, pduSize

    print client.get_cpu_info()


    # 断开连接
    client.disconnect()
    client.destroy()