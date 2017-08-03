# coding=utf-8
import os
import argparse
import subprocess
import ConfigParser
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
        raise EnvironmentError('option --config no value, choose from "dev" or "prod"')

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
    subprocess.call('celery -B -A app worker -l info', shell=True)
    # database_reset()
    # first_running()
    # print app.conf['BEAT_URL']
    # mp.doc.main()
    # beats()
    # get_config()
    # get_value()
    # upload()

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
with PythonPLC('192.168.18.17', 0, 2, 102) as db:
    print(db.ip)
    result = db.read_area(area=snap7.snap7types.S7AreaDB, dbnumber=1, start=0, size=4)
value = struct.unpack('!i', result)[0]
print value