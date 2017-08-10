# coding=utf-8
import os
import argparse
import subprocess
import time

parser = argparse.ArgumentParser()
parser.add_argument('--reset', action='store_true')
parser.add_argument('--start', action='store_true')
parser.add_argument('--config')
parser.add_argument('--url')
args = parser.parse_args()


# 根据环境变量选择配置,或者启动时添加参数
if not os.environ.get('env'):
    if args.config == 'dev':
        os.environ['env'] = 'dev'
    elif args.config == 'prod':
        os.environ['env'] = 'prod'
    else:
        os.environ['env'] = 'dev'
        # raise EnvironmentError('option --config no value, choose from "dev" or "prod"')

if not os.environ.get('url'):
    if args.url == 'server':
        os.environ['url'] = 'server'
    else:
        os.environ['url'] = 'dev-server'

# app中import了model，model创建时需要获取mysql数据地址，地址根据环境变量从ini文件中读取，导入app放在输入环境变量后
from app import database_reset, first_running

if args.reset:
    database_reset()

if args.start:
    first_running()
    os.environ['pythonoptimize'] = '1'
    subprocess.call('celery -B -A app worker -l info', shell=True)
    # database_reset()
    # first_running()
    # print app.conf['BEAT_URL']
    # mp.doc.main()
    # beats()
    # get_config()
    # get_value()
    # upload()
# from app import beats, get_config, check_variable_get_time, check_group_upload_time
# beats()
# get_config()
# check_variable_get_time()
# check_group_upload_time()
# database_reset()

# from snap7 import snap7types
# from data_collection import PythonPLC
# import struct
# with PythonPLC('192.168.18.17', 0, 2, 102) as db:
#     # data = struct.pack('!i', 4)
#     # r = db.db_write(1, 0, data)
#     # v = db.db_read(1, 0, 4)
#     # v = db.ab_read(0, 4)
#     # db.plc_stop()
#     # d = db.write_area(snap7types.S7AreaP, 1, 0, data)
#     v = db.read_area(snap7types.S7AreaDB, 100, 0, 4)
#     print struct.unpack('!i', v)

# from models import session, YjStationInfo
#
# def a(b):
#     m = YjStationInfo(model_id=b)
#     session.add(m)
# time1 = time.time()
# for b in range(50, 70):
#     a(b)
# session.commit()
# time2 = time.time()
# print(time2 - time1)
# print('a')

import snap7, struct
from data_collection import PythonPLC
from snap7.util import get_bool, get_int
# with PythonPLC('192.168.18.17', 0, 2) as db:
#     print(db)
#     result = db.read_area(area=snap7.snap7types.S7AreaDB, dbnumber=3, start=18, size=1)
# time1 = time.time()
# value = struct.unpack('!?', result)[0]
# time2 = time.time()
# print(time1 - time2)
# print(value)

# print(result)
# time1 = time.time()
# print(get_bool(result, 0, 1))
# print(get_int(result, 0))
# time2 = time.time()
# print(time2-time1)
# print(bin(result[7]))

# temp = 7
# buffer1 = []
# for x in result:
#     buffer1.extend(bin(x).replace('0b', '').rjust(8, '0'))
# print(buffer1)
# print(buffer1[abs(temp - 7)])
# print(value)
# print(db)

# try:
#     print('a')
#     assert ('a' == 'b')
# except:
#     print('b')
# else:
#     print('c')

from models import Value, session, YjPLCInfo, YjVariableInfo
from data_collection import variable_area, variable_size
# import multiprocessing as mp
# def get(client):
#     result = client.db_read(3,0,18)
#     print(result)
#
# b = list()
# c = 1
# for a in range(7):
#     time1 = time.time()
client = snap7.client.Client()
#     time2 = time.time()
#     print(time2 - time1)
#     # client = snap7.client.Client()
#     time1 = time.time()
client.connect('192.168.18.17', 0, 2)
#     time2 = time.time()
#     print(time2 - time1)
#     b.append(client)
#     print(c)
#     c += 1
# d = list()
# while True:
#     for client in b:
#         p = mp.Process(target=get, args=(client, ))
#         p.start()
#         d.append(p)
#     for process in d:
#         process.join()
#
# print(snap7.util.get_bool(result, 0, 2))
# client.disconnect()

# time1 = time.time()
# result = client.list_blocks()
# print(result)
# print(len(result))
# time2 = time.time()
# print(time2 - time1)
# v = Value(22, 2, 122)
# v.value = 3
# print(v.value)
# session.add(v)
# session.commit()
#
# time1 = time.time()
# plc_client = list()
# for plc in session.query(YjPLCInfo):
#     client = snap7.client.Client()
#     print(plc.ip, plc.slot, plc.rack)
#     client.connect(plc.ip, plc.rack, plc.slot)
#     if client.get_connected():
#         plc_client.append((client, plc.ip, plc.rack, plc.slot))
#
# time2 = time.time()
# print(time2 - time1)
#
# for variable in session.query(YjVariableInfo):
#     time1 = time.time()
#     ip = variable.group.plc.ip
#     time2 = time.time()
#     print(time2 - time1, '获取ip')
#     for plc in plc_client:
#         if plc[1] == ip:
#
#             time1 = time.time()
#
#             if not plc[0].get_connected():
#                 plc[0].connect(plc.ip, plc.rack, plc.slot)
#             time2 = time.time()
#             print(time2 - time1, '测试连接')
#
#             area = variable_area(variable)
#             variable_db = variable.db_num
#             size = variable_size(variable)
#             address = variable.address
#
#             result = plc[0].read_area(area=area, dbnumber=variable_db, start=address, size=size)
#             value = get_value(variable, result)
#             print(value)