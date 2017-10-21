# coding=utf-8

import os
import requests
from requests.adapters import HTTPAdapter
from requests.exceptions import ConnectionError
import json
import struct
import random
import time
import multiprocessing as mp
import math
import asyncio
import threading
from concurrent.futures import ThreadPoolExecutor
import logging
import platform

try:
    import configparser as ConfigParser
except:
    import ConfigParser
import datetime

from celery import Celery
from celery.signals import worker_process_init
from celery.exceptions import MaxRetriesExceededError, SoftTimeLimitExceeded
from celery.utils.log import get_task_logger
import billiard
from sqlalchemy.orm.exc import UnmappedInstanceError, UnmappedClassError
from snap7.snap7exceptions import Snap7Exception
import snap7
import gevent

from models import (eng, Base, Session, YjStationInfo, YjPLCInfo, YjGroupInfo, YjVariableInfo, TransferLog, \
                    Value, serialize, StationAlarm, PLCAlarm)
from celeryconfig import Config

# 初始化celery
app = Celery()
app.config_from_object(Config)

# 获取当前目录位置
here = os.path.abspath(os.path.dirname(__file__))

# 读取snap7 C库
system_str = platform.system()
lib_path = '/plc_connect_lib/snap7'
# Mac os
if system_str == 'Darwin':
    lib_path += '/mac_os/libsnap7.dylib'
elif system_str == 'Linux':
    # raspberry
    if platform.node() == 'raspberrypi':
        lib_path += '/raspberry/libsnap7.so'

    # ubuntu
    elif platform.machine() == 'x86_64':
        lib_path += '/ubuntu/libsnap7.so'

snap7.common.load_library(here + lib_path)

# 读取配置文件
cf = ConfigParser.ConfigParser()
cf.read_file(open(os.path.join(here, 'config.ini'), encoding='utf-8'))

# 从配置表中读取通用变量
BEAT_URL = cf.get(os.environ.get('url'), 'beat_url')
CONFIG_URL = cf.get(os.environ.get('url'), 'config_url')
UPLOAD_URL = cf.get(os.environ.get('url'), 'upload_url')
CONNECT_TIMEOUT = float(cf.get('client', 'connect_timeout'))
REQUEST_TIMEOUT = float(cf.get('client', 'request_timeout'))
MAX_RETRIES = int(cf.get('client', 'max_retries'))
CHECK_DELAY = cf.get('client', 'check_delay')
SERVER_TIMEOUT = cf.get('client', 'server_timeout')
PLC_TIMEOUT = cf.get('client', 'plc_timeout')


def database_reset():
    """
    初始化数据库
    
    :return: 
    """
    Base.metadata.drop_all(bind=eng)
    Base.metadata.create_all(bind=eng)


def get_station_info():
    """
    通过配置表读取本机信息
    
    :return: dict(id_num, version)
    """
    session = Session()
    id_num = cf.get('client', 'id_num')
    try:
        station_model = session.query(YjStationInfo).filter_by(id_num=id_num).first()
        version = station_model.version
    except:
        version = cf.get('client', 'version')

    return dict(id_num=id_num, version=version)


# 获取本机信息
station_info = get_station_info()

# plc连接实例列表
plc_client = list()

from data_collection import variable_size, variable_area, read_value, write_value, PythonPLC
from station_alarm import check_time_err, connect_server_err
from plc_alarm import connect_plc_err

# pool = mp.Pool(3)

# 初始化requests
s = requests.Session()
s.mount('http://', HTTPAdapter(max_retries=3))
s.mount('https://', HTTPAdapter(max_retries=3))


def first_running():
    """
    开机初次运行
    
    :return: 
    """
    logging.debug('first_running')
    Base.metadata.create_all(bind=eng)
    get_config()


def plc_connection(plcs):
    """
    连接plc，将连接实例存入list
    
    :param plcs: sqlalchemy数据库查询对象列表
    :return: snap7 client实例元组 [0]client对象实例 [1]plc ip地址 [2]plc 机架号  [3]plc 插槽号 [4]plc 配置数据主键 [5]plc 名称
    """
    plc_client = list()
    for plc in plcs:
        client = snap7.client.Client()
        client.connect(plc.ip, plc.rack, plc.slot)
        if client.get_connected():
            plc_client.append((client, plc.ip, plc.rack, plc.slot, plc.id, plc.plc_name))
    return plc_client


def before_running():
    """
    运行前设置
    
    :return: 
    """
    logging.debug('运行前初始化')

    # 建立数据库连接
    session = Session()

    # 设定服务开始运行时间
    current_time = int(time.time())
    start_time = current_time + int(cf.get('client', 'START_TIMEDELTA'))

    # 获取站信息
    global station_info
    station_info = get_station_info()

    # 获取该终端所有PLC信息
    plcs = session.query(YjPLCInfo)

    # 建立PLC连接池
    global plc_client
    plc_client = plc_connection(plcs)
    logging.debug("PLC连接池： " + str(plc_client))

    for plc in plcs:

        # 获得该PLC的信息
        ip = plc.ip
        # rack = plc.rack
        # slot = plc.slot

        # 从PLC连接池中获得该PLC的连接
        plc_cli = None
        for client in plc_client:
            if client[1] == ip:
                plc_cli = client
                break

        # 获取该PLC下所有组信息
        groups = plc.groups

        # 设定变量组信息
        for g in groups:
            # 设定变量组初始上传时间
            g.upload_time = start_time + g.upload_cycle

            # 获取该变量组下所有变量信息
            variables = g.variables

            # 设定变量信息
            for v in variables:

                # 获取变量读写类型
                rw_type = v.rw_type
                value = v.write_value

                # 判断变量存在写操作
                if rw_type == 2 or rw_type == 3 and value is not None:

                    # 获取写入变量值所需信息
                    data_type = v.data_type
                    db = v.db_num
                    area = variable_area(v)
                    address = int(math.modf(v.address)[1])
                    bool_index = round(math.modf(v.address)[0] * 10)

                    # todo 获取整个字节，将布尔值所在位插入到字节中
                    if data_type == 'BOOL':

                        # 获取当前字节
                        try:
                            # 只读，没插
                            byte = plc_cli.read_area(area=area, dbnumber=db, start=address, size=1)
                        except ValueError as e:
                            logging.error(e)
                            # todo plc连接问题日志记录
                            byte = None
                    else:
                        byte = None

                    # 将写入数据转为字节码
                    byte_value = write_value(v.data_type, v.write_value, bool_index, byte)

                    # print(area, variable_db, address, byte_value)

                    # 数据写入
                    plc_cli.write_area(area=area, dbnumber=db, start=address, data=byte_value)
                    # byte = db.read_area(area=area, dbnumber=variable_db, start=address, size=2)
                    # from data_collection import get_bool, read_value
                    # from snap7.util import get_int
                    # if v.data_type=='INT':
                    #     print(address, get_int(byte, 0), 'after')
                    # print(address, get_bool(byte, 0, 0), 'after_write')

                # 判断变量存在读操作
                if rw_type == 1 or rw_type == 3:
                    # 设定变量初始读取时间
                    v.acquisition_time = start_time + v.acquisition_cycle

    # 数据库写入操作后，关闭数据库连接
    session.commit()
    session.close()


@app.task()
def self_check():
    """
    celery任务
    定时自检
    
    :return: 
    """
    logging.debug('自检')

    # 建立数据库连接
    session = Session()
    current_time = int(time.time())

    # 获取站点配置信息
    station_model = session.query(YjStationInfo).first()

    # 获取上次检查时间并检查时间间隔，判断程序运行状态
    check_time = station_model.check_time
    if current_time - check_time > CHECK_DELAY:
        alarm = check_time_err()
        session.add(alarm)
    station_model.check_time = current_time

    # 检查与服务器通讯状态
    if current_time - station_model.con_time > SERVER_TIMEOUT:
        alarm = connect_server_err()
        session.add(alarm)

    # 检查PLC通讯状态
    global plc_client
    if not plc_client:
        plcs = session.query(YjPLCInfo)
        plc_client = plc_connection(plcs)

    for plc in plc_client:
        plc_model = session.query(YjPLCInfo).filter_by(id=plc[4]).first()

        # 连接成功，记录时间
        if plc[0].get_connected():
            plc_model.con_time = current_time
        else:
            # 连接失败，重新连接并记录
            plc[0].connect(plc[1], plc[2], plc[3])

            # 超过一定时间的上传服务器
            if current_time - plc_model.con_time > PLC_TIMEOUT:
                level = 2

            # 发现连接失败
            else:
                level = 1
            alarm = connect_plc_err(level=level, plc_id=plc[4], plc_name=plc[5])
            session.add(alarm)

    # 数据库写入，关闭连接
    session.commit()
    session.close()


# todo 多进程没用上
@worker_process_init.connect
def fix_mutilprocessing(**kwargs):
    try:
        mp.current_process()._authkey
    except AttributeError:
        mp.current_process()._authkey = mp.current_process().authkey


@app.task(rate_limit='5/s', max_retries=MAX_RETRIES)
def beats():
    """
    celery任务
    与服务器的心跳连接
    
    :param self: 
    :return: 
    """
    logging.debug('beats')

    # 建立数据库连接
    session = Session()

    current_time = int(time.time())

    # 从数据库获取站点信息 todo 缓存中取
    station_model = session.query(YjStationInfo).first()

    # 获取上次心跳时间 todo 存入缓存，从缓存中获取
    last_beat_time = station_model.con_time

    # 获取心跳间隔时间内产生的报警
    if last_beat_time:
        station_alarms = session.query(StationAlarm).filter(last_beat_time <= StationAlarm.time < current_time).all()
        plc_alarms = session.query(PLCAlarm).filter(PLCAlarm.level >= 2). \
            filter(last_beat_time <= PLCAlarm.time < current_time).all()
    else:
        station_alarms = None
        plc_alarms = None

    # todo 缓存
    data = dict(
        id_num=station_model.id_num,
        version=station_model.version,
        station_alarms=station_alarms,
        plc_alarms=plc_alarms
    )

    # data = encryption(data)
    # todo 报警变量加到data里

    # 发送心跳包
    try:
        rv = s.post(BEAT_URL, json=data, timeout=(CONNECT_TIMEOUT, REQUEST_TIMEOUT))

    # 连接服务器失败
    except (ConnectionError, MaxRetriesExceededError) as e:
        logging.warning('心跳连接错误：' + str(e))

        status = 'error'
        note = '无法连接服务器，检查网络状态。重试。'

        # 重试celery任务
        # try:
        #     raise self.retry(exc=e)
        # except ConnectionError:
        #     pass

    # 连接成功
    else:
        # data = decryption(rv)
        data = rv.json()
        # print(data)

        status = 'OK'

        station_model.con_time = current_time

        # 配置有更新
        if data["modification"] == 1:
            logging.info('发现配置有更新，准备获取配置')
            get_config()
            note = '完成一次心跳连接，时间:{},发现配置信息有更新.'.format(datetime.datetime.fromtimestamp(current_time))

        # 配置无更新
        else:
            note = '完成一次心跳连接，时间:{}.'.format(datetime.datetime.fromtimestamp(current_time))

    log = TransferLog(
        trans_type='beats',
        time=current_time,
        status=status,
        note=note
    )
    session.add(log)

    session.commit()
    session.close()


@app.task(max_retries=MAX_RETRIES)
def get_config():
    """
    连接服务器接口，获取本机变量信息
    
    :param self: 
    :return: 
    """
    logging.debug('连接服务器,获取数据')

    # 建立数据库连接
    session = Session()

    current_time = int(time.time())
    # data = encryption(data)
    data = station_info
    logging.info('获取配置，发送请求：' + str(data))

    # 连接服务器
    try:
        response = requests.post(CONFIG_URL, json=data, timeout=(CONNECT_TIMEOUT, REQUEST_TIMEOUT))

    # 连接失败
    except ConnectionError as e:
        logging.warning('获取配置错误：' + str(e))

        status = 'error'
        note = '无法连接服务器，检查网络状态。'
        log = TransferLog(
            trans_type='config',
            time=current_time,
            status=status,
            note=note
        )
        session.add(log)

        # try:
        #     raise self.retry(exc=e)
        # except ConnectionError:
        #     pass
        # return 1
    # 连接成功
    else:
        if response.status_code == 404:
            status = 'error'
            note = '获取配置信息失败'

        elif response.status_code == 200:
            data = response.json()['data']

            print(data)

            # 配置更新，删除现有表
            try:
                session.delete(session.query(YjStationInfo).filter_by(id_num=station_info['id_num']).first())
            # YjStationInfo.__table__.drop(eng, checkfirst=True)
            # YjPLCInfo.__table__.drop(eng, checkfirst=True)
            # YjGroupInfo.__table__.drop(eng, checkfirst=True)
            # YjVariableInfo.__table__.drop(eng, checkfirst=True)
            # Value.__table__.drop(eng, checkfirst=True)
            # Base.metadata.create_all(bind=eng)
            except UnmappedInstanceError:
                session.rollback()
            else:
                session.commit()

            version = data["YjStationInfo"]["version"]

            station = YjStationInfo(
                model_id=data["YjStationInfo"]["id"],
                station_name=data["YjStationInfo"]["station_name"],
                mac=data["YjStationInfo"]["mac"],
                ip=data["YjStationInfo"]["ip"],
                note=data["YjStationInfo"]["note"],
                id_num=data["YjStationInfo"]["id_num"],
                plc_count=data["YjStationInfo"]["plc_count"],
                ten_id=data["YjStationInfo"]["ten_id"],
                item_id=data["YjStationInfo"]["item_id"],
                version=version
            )
            session.add(station)

            for plc in data["YjPLCInfo"]:
                p = YjPLCInfo(
                    model_id=plc["id"],
                    plc_name=plc["plc_name"],
                    station_id=plc["station_id"],
                    note=plc["note"],
                    ip=plc["ip"],
                    mpi=plc["mpi"],
                    type=plc["type"],
                    plc_type=plc["plc_type"],
                    ten_id=plc["ten_id"],
                    item_id=plc["item_id"],
                    rack=plc['rack'],
                    slot=plc['slot'],
                    tcp_port=plc['tcp_port']
                )

                session.add(p)

            for group in data["YjGroupInfo"]:
                g = YjGroupInfo(
                    model_id=group["id"],
                    group_name=group["group_name"],
                    plc_id=group["plc_id"],
                    note=group["note"],
                    upload_cycle=group["upload_cycle"],
                    ten_id=group["ten_id"],
                    item_id=group["item_id"]
                )
                session.add(g)

            for variable in data["YjVariableInfo"]:
                v = YjVariableInfo(
                    model_id=variable["id"],
                    variable_name=variable["variable_name"],
                    group_id=variable["group_id"],
                    db_num=variable['db_num'],
                    address=variable["address"],
                    data_type=variable["data_type"],
                    rw_type=variable["rw_type"],
                    upload=variable["upload"],
                    acquisition_cycle=variable["acquisition_cycle"],
                    server_record_cycle=variable["server_record_cycle"],
                    note=variable["note"],
                    ten_id=variable["ten_id"],
                    item_id=variable["item_id"],
                    write_value=variable["write_value"],
                    area=variable['area']
                )
                session.add(v)

            status = 'OK'
            note = '成功将配置从version: {} 升级到 version: {}.'.format(
                station_info['version'], version)
        else:
            status = 'error'
            note = '获取配置时发生未知问题，检查服务器代码。 {}'.format(
                response.status_code)

        # 记录服务器连接状况
        log = TransferLog(
            trans_type='config',
            time=current_time,
            status=status,
            note=note
        )
    session.add(log)

    session.commit()
    session.close()

    before_running()


def upload_data(group_model, current_time):
    """
    查询该组内需要上传的变量，从数据库中取出变量对应的数值
    
    :param group_model: 上传组数据库数据对象
    :param current_time: 当前时间
    :param session: 数据库连接会话
    :return: 变量值列表
    """

    # 建立数据库连接
    session = Session()

    # 获取该组信息
    group_id = group_model.id
    group_name = group_model.group_name

    # print(type(group_name))

    # 准备本次上传的数据
    variables = group_model.variables
    variable_list = []
    # print(variables)

    for variable in variables:

        # 判断该变量是否需要上传
        if variable.upload:

            # 获取上次传输时间,没有上次时间就往前推一个上传周期
            get_time = current_time - group_model.upload_cycle

            # 读取需要上传的值,所有时间大于上次上传的值
            # all_values = variable.values.filter(get_time <= Value.time < upload_time)
            all_values = session.query(Value).filter_by(variable_id=variable.id).filter(
                get_time <= Value.time).filter(Value.time < current_time)

            # # test
            # for a in all_values:
            #     print a.id

            # 循环从上次读取时间开始计算，每个一个记录周期提取一个数值
            while get_time < current_time:
                upload_value = all_values.filter(
                    get_time + variable.server_record_cycle > Value.time).filter(Value.time >= get_time).first()
                # 当上传时间小于采集时间时，会出现取值时间节点后无采集数据，得到None，使得后续语句报错。
                # print(upload_value)
                try:
                    value_dict = serialize(upload_value)
                    variable_list.append(value_dict)
                except UnmappedClassError:
                    pass

                get_time += variable.server_record_cycle

    # 上传日志记录
    log = TransferLog(
        trans_type='upload',
        time=current_time,
        status='OK',
        note='group_id: {} group_name:{} 将要上传.'.format(group_id, group_name)
    )
    # 记录本次传输
    session.add(log)

    session.commit()
    session.close()

    return variable_list


@app.task(max_retries=MAX_RETRIES, default_retry_delay=30)
def upload(variable_list, group_model, current_time):
    """
    数据上传
    :param self: 
    :param variable_list: 
    :param group_model: 
    :param current_time: 
    :return: 
    """

    # 建立数据库连接
    session = Session()

    # 获取变量组基本信息
    group_id = group_model.id
    group_name = group_model.group_name.encode('utf-8')

    # 包装数据
    data = {
        "id_num": station_info["id_num"],
        "version": station_info["version"],
        "group_id": group_id,
        "value": variable_list
    }
    print(data)
    # data = encryption(data)

    # 连接服务器，准备上传数据
    try:
        response = requests.post(UPLOAD_URL, json=data, timeout=(CONNECT_TIMEOUT, REQUEST_TIMEOUT))
    except ConnectionError as e:
        logging.warning('上传数据错误：' + str(e))

        status = 'error'
        note = '无法连接服务器，检查网络状态。'
        log = TransferLog(
            trans_type='upload_call_back',
            time=current_time,
            status=status,
            note=note
        )
        session.add(log)

    else:
        data = response.json()
        # data = decryption(data)

        # 日志记录
        # 正常传输
        if response.status_code == 200:
            note = 'group_id: {} group_name:{} 成功上传.'.format(group_id, group_name)

        # 版本错误
        elif response.status_code == 403:
            note = 'group_id: {} group_name:{} 上传的数据不是在最新版本配置下采集的.'.format(group_id, group_name)

        # 未知错误
        else:
            note = 'group_id: {} group_name:{} 无法识别服务端反馈。'.format(group_id, group_name)
        log = TransferLog(
            trans_type='upload_call_back',
            time=current_time,
            status=data["status"],
            note=note
        )
        session.add(log)

    session.commit()
    session.close()


@app.task(bind=True, rate_limit='1/s', max_retries=MAX_RETRIES, default_retry_delay=3)
def check_group_upload_time(self):
    """
    检查变量组上传时间，将满足条件的变量组数据打包上传
    
    :param self: 
    :return: 
    """

    logging.debug('检查变量组上传时间')

    # 建立数据库连接
    session = Session()

    current_time = int(time.time())

    try:

        # try:
        # groups = session.query(YjGroupInfo).filter(current_time >= YjGroupInfo.upload_time).all()
        group_models = session.query(YjGroupInfo).filter(current_time >= YjGroupInfo.upload_time).filter(
            YjGroupInfo.uploading is not True).all()
        # print(groups)
        # except:
        #     return 'skip'

        # poll = multiprocessing.Pool(4)

        # 修改下次组传输时间
        # for group_model in group_models:
        #     print 'b'
        #     group_model.upload_time = current_time + group_model.upload_cycle
        # session.merge(group_model)
        # try:
        # session.commit()
        # except:
        #     session.rollback()

        for group_model in group_models:
            print('a')
            group_model.upload_time = current_time + group_model.upload_cycle
            value_list = upload_data(group_model, current_time)
            upload(value_list, group_model, current_time)

        session.commit()
        # curr_proc = mp.current_process()
        # curr_proc.daemon = False
        # p = mp.Pool(mp.cpu_count())
        # curr_proc.daemon = True
        # for g in groups:
        #     print 'a'
        #     p.apply_async(upload, args=(g,))  # todo 多线程
        # p.close()
        # p.join()
        # #
        # return 1
        # poll.apply_async(upload, (g,))
    except SoftTimeLimitExceeded as exc:
        session.rollback()
        self.retry(exc=exc, max_retries=MAX_RETRIES, countdown=5)
        # session.commit()
    finally:
        session.close()


@app.task(bind=True, rate_limit='1/s', max_retries=MAX_RETRIES, default_retry_delay=3)
def check_variable_get_time(self):
    """
    检查变量采集时间，采集满足条件的变量值
    
    :param self: 
    :return: 
    """

    logging.debug('检查变量采集时间')

    # 建立数据库连接
    session = Session()

    current_time = int(time.time())
    # try:
    variables = session.query(YjVariableInfo).filter(current_time >= YjVariableInfo.acquisition_time).all()
    # print(variables)
    # if variables and not plc_client:
    #     plcs = session.query(YjPLCInfo).all()
    #     for plc in plcs:
    #         plc_connection(plc)


    # variables = session.execute(variables)
    # print(variables)
    # if variables.return_rows:
    #     print json.dumps([dict(r) for r in variables])
    # except:
    #     session.rollback()
    #     return 'skip'

    # task = signature('task.get_value', args=(v, ))
    # sig = group
    # (get_value.sub for v in variables)()
    # sig.delay()
    # poll = billiard.context.BaseContext
    # poll = poll.Pool(poll)
    # # poll = mp.Pool(4)
    # poll.map(get_value, [(v, )
    #                      for v in variables])
    # result = poll.map(get_value, [(v,)
    #                               for v in variables])
    # try:
    # print('v_t')
    # for v in variables:
    # 保证一段时间内不会产生两个task采集同一个变量
    # v.acquisition_time = current_time + v.acquisition_cycle
    # session.merge(v)
    # session.commit()
    # print('v_g')
    # from multiprocessing import Pool as ThreadPool
    # if not variables:
    #     return
    # p_list = []
    # pool = ThreadPool(5)
    # pool.map(get_value, variables)
    # pool.close()
    # pool.join()

    # pool = mp.Pool(4)
    # gevent_list = list()


    for var in variables:
        #     print('var')
        get_value2(var, session, current_time)
    # print 'variable'
    # print 'get value'
    # p = mp.Process(target=get_value_var, args=(var,))
    # p.start()
    # p_list.append(p)
    # t_list = list()
    # for var in variables:
    #     t = threading.Thread(target=get_value, args=(var,))

    #     t.start()
    # t.join()
    # t_list.append(t)

    # for t in t_list:
    #     t.join()
    '''
    if not variables:
        return
    loop = asyncio.get_event_loop()
    executor = ThreadPoolExecutor(5)
    loop.set_default_executor(executor)

    tasks = [asyncio.Task(get_value(var, session, current_time)) for var in variables]
    try:
        loop.run_until_complete(asyncio.wait(tasks))
    except ValueError:
        pass
    executor.shutdown(wait=True)
    '''

    # loop.close()
    # pool.apply_async(func=get_value, args=(var,))
    # gevent_list.append(gevent.spawn(get_value_var(var)))
    # gevent.joinall(gevent_list)
    # pool.close()
    # pool.join()
    # for res in p_list:
    #     res.join()
    # get_value.apply_async((var, session))
    # poll.apply_async(get_value, (v,))
    try:
        session.commit()
        # except:
        #     session.rollback()
    except SoftTimeLimitExceeded as exc:
        session.rollback()
        self.retry(exc=exc, max_retries=MAX_RETRIES, countdown=5)
    finally:
        session.close()


# @asyncio.coroutine
# @app.task
# async def get_value(variable_model, session, current_time):
#     print('get_value')
#     loop = asyncio.get_event_loop()
#
#     # session = Session()
#     # current_time = int(time.time())
#     variable_model.acquisition_time = current_time + variable_model.acquisition_cycle
#     # 获得变量信息
#     # 变量所属plc的信息
#     ip = variable_model.ip
#     # print(plc_client)
#     for plc in plc_client:
#         # print(plc)
#         if plc[1] == ip:
#
#             if not plc[0].get_connected():
#                 plc[0].connect(plc.ip, plc.rack, plc.slot)
#
#             area = variable_area(variable_model)
#             variable_db = variable_model.db_num
#             size = variable_size(variable_model)
#             address = int(math.modf(variable_model.address)[1])
#             bool_index = round(math.modf(variable_model.address)[0] * 10)
#
#             result = ''
#             # while plc[0].library.Cli_WaitAsCompletion(plc[0].pointer, 2000):
#             while result == '':
#                 # print('fffff')
#                 # byte_array = plc[0].db_read(db_number=variable_db, start=address, size=size)
#
#                 while plc[0].library.Cli_WaitAsCompletion(plc[0].pointer, 100):
#                     await asyncio.sleep(random.randint(1, 3) / 100)
#                 try:
#                     # result = plc[0].db_read(db_number=variable_db, start=address, size=size)
#
#                     result = await loop.run_in_executor(None, plc[0].read_area, area, variable_db, address, size)
#
#                 except Snap7Exception:
#                     pass
#                 else:
#                     break
#
#                     # else:
#                     #     break
#
#             # print('1')
#             # while not plc[0].library.Cli_WaitAsCompletion(plc[0].pointer, 2000):
#             #     print('2')
#             #     time.sleep(0.01)
#             # print('3')
#             # result = plc[0].as_db_read(db_number=variable_db, start=address, size=size)
#
#             # await asyncio.sleep(0.015)
#             # result = plc[0].db_read(db_number=variable_db, start=address, size=size)
#             # await asyncio.sleep(0.5)
#
#             # g.send((plc, area, variable_db, address, size, variable_model, bool_index, current_time, session))
#             # result =  await loop.run_in_executor(None, plc[0].read_area(area=area, dbnumber=variable_db, start=address, size=size))
#             value = read_value(variable_model.data_type, result, bool_index)
#             # time.sleep(0.2)
#             # value = 2
#             print(value)
#
#             value = Value(variable_id=variable_model.id, time=current_time, value=value)
#             session.add(value)
#
#             # session.commit()
#             break
#     return


def get_value2(variable_model, session, current_time):
    """
    采集数据
    
    :param variable_model: 
    :param session: 
    :param current_time: 
    :return: 
    """
    print('get_value')
    # loop = asyncio.get_event_loop()

    # session = Session()
    # current_time = int(time.time())
    variable_model.acquisition_time = current_time + variable_model.acquisition_cycle
    # 获得变量信息
    # 变量所属plc的信息
    ip = variable_model.ip
    print(plc_client)
    for plc in plc_client:
        print(plc)
        if plc[1] == ip:

            if not plc[0].get_connected():
                plc[0].connect(plc[1], plc[2], plc[3])

            area = variable_area(variable_model)
            variable_db = variable_model.db_num
            size = variable_size(variable_model)
            address = int(math.modf(variable_model.address)[1])
            bool_index = round(math.modf(variable_model.address)[0] * 10)

            result = plc[0].read_area(area, variable_db, address, size)

            value = read_value(variable_model.data_type, result, bool_index)
            print(variable_model.id)
            print(value, 'value')

            value = Value(variable_id=variable_model.id, time=current_time, value=value)
            session.add(value)

            # session.commit()
            break
    return


def get():
    r = ''
    while True:
        n = yield r
        plc, area, variable_db, address, size, variable_model, bool_index, current_time, session = n
        if not n:
            return
        result = plc[0].read_area(area=area, dbnumber=variable_db, start=address, size=size)
        value = read_value(variable_model.data_type, result, bool_index)
        print(value)
        value = Value(variable_id=variable_model.id, time=current_time, value=value)
        session.add(value)
