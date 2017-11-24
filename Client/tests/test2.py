import struct
import snap7
from snap7.util import set_bool
from data_collection import read_value, get_bool, write_value
import time
import multiprocessing as mp
import random
# while True:
# print(random.randint(1, 5)/100 )
import unittest


class TestClient(unittest.TestCase):

    ip = '192.168.18.17'
    rack = 0
    slot = 2
    tcpport = 102

    # 建立连接
    def setUp(self):
        self.client = snap7.client.Client()
        self.client.connect(self.ip, self.rack, self.slot, self.tcpport)

    # 断开连接
    def tearDown(self):
        self.client.disconnect()
        self.client.destroy()


    def db_get(self):
        time1 = time.time()
        byte = self.client.db_get(1)
        time2 = time.time()
        print(time2 - time1)
        print(byte)

    # db_get()

    def as_db_get(self):
        time1 = time.time()
        # byte = client.as_db_read(1, 0, 1000)
        print(self.client.library.Cli_GetAgBlockInfo())
        # client.library.Cli_WaitAsCompletion()
        # print(byte)
        # time.sleep(15)

        # print(client.library.Cli_CheckAsCompletion())
        time2 = time.time()
        print(time2 - time1)
        # print(byte)

    def test_get_float(self):
        byte = self.client.db_read(1, 0, 4)
        print(byte)
        print(struct.unpack('!f', byte))
        data = read_value('FLOAT', byte)
        print(data)

a = TestClient()
a.setUp()
a.test_get_float()
# as_db_get()
# time.sleep(15)
# as_db_get()
# c_l = list()
# for i in range(1):
#     client = snap7.client.Client()
#     c_l.append(client)
#
# print(len(c_l))

# print(c_l)
# def create_connect(a):
    # client = snap7.client.Client()
    # print(a, 'c')
    # client = c_l[a]
    # print(client)
    # client.connect('192.168.18.17', 0, 2)
    # byte = client.db_read(1, 0, 1)
    # print(byte)
    # print(a, 'a')
    # client.disconnect()
    # client.destroy()
    # return byte

# client = create_connect()
# print(client)
# while True:
#     client.db_get(1)

# time.sleep(100)

# p_list = list()
# pool = mp.Pool(10)
# pool.map(create_connect, range(1))
# time.sleep(100)
# pool.close()
# pool.join()

# for i in range(10):
#     p = mp.Process(target=create_connect)
#     p.start()
#     print(i)
#     p_list.append(p)
#
# print(2)
# for p in p_list:
#     p.join()



# byte = client.db_read(1, 5666, 1)
# data = get_bool(byte, 0, 0)
# print(data)
# set_bool(byte, 0, 0, 1)
# client.db_write(1, 5666, byte)
# byte = client.db_read(1, 5666, 1)
# data = get_bool(byte, 0, 0)
# print(data)
#
# # set_bool()
# data = client.db_read(1, 5555, 2)
# b = struct.unpack('!h', data)
# print(b, 'data')
# b = struct.pack('!h', 10)
# print(b)
# client.db_write(1, 5555, b)
# b = client.db_read(1, 5555, 2)
# print(struct.unpack('!h', b))
# c = bytearray(1)
# print(c)
# b = struct.pack('!?', 0)
# print(b)
# data = client.db_read(1, 0, 2)
# print(data)
# set_bool(data, 0, 0, 1)
# print(data[0:], '?')
# print(data, 'write_data')
# client.db_write(1, 0, data)
# print(data)
# result = client.db_read(1, 0, 2)
# print(result)
# print(get_bool(result, 0, 1))
# # print(struct.unpack('!h', result)[0])
#     # print(1)
#     # print(client.library.Cli_WaitAsCompletion(client.pointer, 100))
#     # print(result)
#
# time1 = time.time()
# # data, size = client.full_upload('DB', 1)
# # print(data, size)
#
# # data = client.db_read(3, 0, 200)
# # print(data)
# data = client.as_db_read(1, 0, 200)
# print(data)
# time2 = time.time()
# print(time2 - time1, 'db_read')
# print(len(data))
#
# time1 = time.time()
# data = client.db_get(1)
# time2 = time.time()
# print(time2 - time1)
# print(len(data))