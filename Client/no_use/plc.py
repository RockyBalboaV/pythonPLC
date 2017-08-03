# coding=utf-8
import struct
import re
import snap7
from snap7 import util
import MySQLdb
from consts import *
from models import *

# 设置PLC的连接地址
ip = '192.168.18.17'  # PLC的ip地址
rack = 0  # 机架号
slot = 2  # 插槽号
tcpport = 102  # TCP端口号


class Client():

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

    def __init__(self, address, tagname, serverrecordcycle):
        # 建立连接
        self.client = snap7.client.Client()
        self.client.connect(ip, rack, slot, tcpport)
        self.address = address
        self.variable_name = tagname
        self.serverrecordcycle = serverrecordcycle

    @classmethod
    def get_value(self):
        result = self.client.db_read(db_number=11, start=self.address, size=12)
        self.print_row(result)
        b=''.join(chr(i)for i in result)
        db1_tuple = struct.unpack('>????if', b)
        time = datetime.datetime.now()
        value = Value(variable_name=self.variable_name, get_time=time, up_time=self.serverrecordcycle, value=db1_tuple[0])
        session.add(value)
        session.commit()

        result = self.client.db_read(db_number=11, start=0, size=24)
        self.print_row(result)
        b=''.join(chr(i)for i in result)
        db1_tuple = struct.unpack('>ffhhfhhi', b)          #ffipfipl
        with db as cur:
            for a in range(len(db1_tuple)):
                print str(db1_tuple)
                sql = "insert into test(str, variable) values(%s, %s)"
                cur.execute(sql, (str(db1_tuple[a]), 'DB11'))