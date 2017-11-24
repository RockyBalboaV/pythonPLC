# coding=utf-8

import os
import requests
from requests.adapters import HTTPAdapter
from requests.exceptions import ConnectionError
import ctypes
import time
import subprocess
import math
import logging

import configparser

import datetime
from utils.redis_middle_class import Conn_db
from celery import Celery
from celery.signals import worker_process_init
from celery.exceptions import MaxRetriesExceededError, SoftTimeLimitExceeded
from celery.utils.log import get_task_logger
import billiard
from sqlalchemy.orm.exc import UnmappedInstanceError, UnmappedClassError
from snap7.snap7exceptions import Snap7Exception
import snap7
from snap7.snap7types import S7DataItem, S7WLByte
import gevent

from models import eng, Base, Session, YjStationInfo, YjPLCInfo, YjGroupInfo, YjVariableInfo, TransferLog, \
    Value, serialize, StationAlarm, PLCAlarm
from celeryconfig import Config
from data_collection import variable_size, variable_area, read_value, write_value, snap7_path, analog2digital
from station_alarm import check_time_err, connect_server_err
from plc_alarm import connect_plc_err, read_err
from util import encryption_client, decryption_client
from param import (ID_NUM, BEAT_URL, CONFIG_URL, UPLOAD_URL, CONFIRM_CONFIG_URL, CONNECT_TIMEOUT, REQUEST_TIMEOUT,
                   MAX_RETRIES, CHECK_DELAY, SERVER_TIMEOUT, PLC_TIMEOUT, START_TIMEDELTA)

from data_collection_3 import readsuan

# 初始化celery
app = Celery()
app.config_from_object(Config)

# 日志
logging.basicConfig(level=logging.DEBUG)
# logging.basicConfig(filename='logger.log', level=logging.INFO)
logging.getLogger(__name__).addHandler(logging.NullHandler())

# 获取当前目录位置
here = os.path.abspath(os.path.dirname(__file__))

# 读取snap7 C库
lib_path = snap7_path()

snap7.common.load_library(here + lib_path)

r = Conn_db()

# 初始化requests
req_s = requests.Session()
req_s.mount('http://', HTTPAdapter(max_retries=3))
req_s.mount('https://', HTTPAdapter(max_retries=3))


def database_reset():
    """
    初始化数据库
    
    :return: 
    """

    Base.metadata.drop_all(bind=eng)
    Base.metadata.create_all(bind=eng)


def first_running():
    """
    开机初次运行
    
    :return: 
    """

    logging.debug('first_running')

    Base.metadata.create_all(bind=eng)

    r.set('id_num', ID_NUM)

    get_config()

    before_running()


def plc_connection(plcs):
    """
    连接plc，将连接实例存入list
    
    :param plcs: sqlalchemy数据库查询对象列表
    :return: snap7 client实例元组 [0]plc ip地址 [1]plc 机架号  [2]plc 插槽号 [3]plc 配置数据主键 [4]plc 名称 [5]plc 连接时间
    """

    current_time = int(time.time())
    plc_client = list()
    for plc in plcs:
        # client = snap7.client.Client()
        # client.connect(plc.ip, plc.rack, plc.slot)
        # if client.get_connected():
        plc_client.append([plc.ip, plc.rack, plc.slot, plc.id, plc.plc_name, current_time])
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
    start_time = current_time + START_TIMEDELTA

    # 获取站信息
    id_num = r.get('id_num')
    # station_info = get_station_info()
    # r.set('station_info', station_info)

    # 获取该终端所有PLC信息
    plcs = session.query(YjPLCInfo)

    # 建立PLC连接池
    plc_client = plc_connection(plcs)
    print(plc_client)
    r.set('plc', plc_client)
    logging.info('PLC连接池： ' + str(plc_client))
    print('PLC连接池： ' + str(plc_client))

    for plc in plcs:

        # 获得该PLC的信息
        ip = plc.ip
        rack = plc.rack
        slot = plc.slot

        plc_cli = snap7.client.Client()

        print(ip, rack, slot)

        try:
            print('plc连接尝试')
            plc_cli.connect(ip, rack, slot)
        except Snap7Exception as e:
            logging.error(e)
            alarm = connect_plc_err(
                id_num=id_num,
                level=0,
                plc_id=plc.id,
                plc_name=plc.plc_name
            )
            session.add(alarm)

        else:
            # 获取该PLC下所有组信息
            groups = plc.groups

            # 设定变量组信息
            for g in groups:
                upload_cycle = g.upload_cycle if isinstance(g.upload_cycle, int) else 30
                acquisition_cycle = g.acquisition_cycle if isinstance(g.acquisition_cycle, int) else 30

                print('acquisition_cycle', acquisition_cycle)
                # 设定变量组初始上传时间
                g.upload_time = start_time + upload_cycle

                # 设定变量初始读取时间
                g.acquisition_time = start_time + acquisition_cycle

                # 变量写入
                # 获取该变量组下所有变量信息
                # variables = g.variables

                # if variables:
                #     for v in variables:
                #         plc_write(v, plc_cli, plc)

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
    id_num = r.get('id_num')

    # 获取上次检查时间并检查时间间隔，判断程序运行状态
    check_time = r.get('check_time')
    print(check_time)
    if check_time:
        if current_time - int(check_time) > CHECK_DELAY:
            alarm = check_time_err(id_num)
            session.add(alarm)
    r.set('check_time', current_time)

    # 检查与服务器通讯状态
    con_time = r.get('con_time')
    if con_time:
        if current_time - int(con_time) > SERVER_TIMEOUT:
            alarm = connect_server_err(id_num)
            session.add(alarm)

    # 检查PLC通讯状态
    plc_client = r.get('plc')
    if not plc_client:
        plcs = session.query(YjPLCInfo)
        plc_client = plc_connection(plcs)
        r.set('plc', plc_client)

    for plc in plc_client:
        plc_connect_time = plc[5]

        # 超过一定时间的上传服务器
        if current_time - plc_connect_time > PLC_TIMEOUT:
            alarm = connect_plc_err(
                id_num,
                level=1,
                plc_id=plc[3],
                plc_name=plc[4]
            )
            session.add(alarm)

    # 数据库写入，关闭连接
    session.commit()
    session.close()


@app.task(rate_limit='2/m', max_retries=MAX_RETRIES)
def beats():
    """
    celery任务
    与服务器的心跳连接
    
    :param self: 
    :return: 
    """

    logging.debug('心跳连接')

    # 建立数据库连接
    session = Session()

    current_time = int(time.time())

    # 从数据库获取站点信息
    id_num = ID_NUM

    # 获取上次心跳时间
    con_time = r.get('con_time')

    # 获取心跳时上传的数据
    data = beats_data(id_num, session, con_time, current_time)
    print(data)
    # data = encryption(data)

    # 发送心跳包
    try:
        rv = req_s.post(BEAT_URL, json=data, timeout=(CONNECT_TIMEOUT, REQUEST_TIMEOUT))

    # 连接服务器失败
    except (ConnectionError, MaxRetriesExceededError) as e:
        logging.warning('心跳连接错误：' + str(e))

        status = 'error'
        note = '无法连接服务器，检查网络状态。重试。'

    # 连接成功
    else:
        # data = decryption_client(rv.json())
        data = rv.json()
        # print(data)

        status = 'OK'

        # 记录本次服务器通讯时间
        r.set('con_time', current_time)

        # 配置有更新
        if data['modification'] == 1:
            logging.info('发现配置有更新，准备获取配置')
            get_config()
            before_running()
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
    
    :return: 
    """
    logging.debug('连接服务器,获取数据')

    # 建立数据库连接
    session = Session()

    current_time = int(time.time())

    time1 = time.time()
    # 获取本机信息
    id_num = r.get('id_num')

    time2 = time.time()
    print('读取redis时间: ' + str(time2 - time1))

    post_data = {
        'id_num': id_num
    }
    logging.info('获取配置，发送请求：' + str(post_data))

    # 连接服务器
    try:
        response = requests.post(CONFIG_URL, json=post_data, timeout=(CONNECT_TIMEOUT, REQUEST_TIMEOUT))

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
        # 记录本次服务器通讯时间
        r.set('con_time', current_time)

        if response.status_code == 404:
            status = 'error'
            note = '获取配置信息失败'

        elif response.status_code == 200:
            rp = response.json()

            data = rp['data']
            # data = decryption_client(rp['data'])

            print(data)

            # 配置更新，删除现有表
            try:
                session.query(YjStationInfo).delete()
                session.query(YjPLCInfo).delete()
                session.query(YjGroupInfo).delete()
                session.query(YjVariableInfo).delete()

            except Exception as e:
                logging.error('更新配置时，删除旧表出错: ' + str(e))
                session.rollback()
            else:
                session.flush()

            # 添加'sqlalchemy' class数据
            session.bulk_insert_mappings(YjStationInfo, [data['stations']])
            session.bulk_insert_mappings(YjPLCInfo, data['plcs'])
            session.bulk_insert_mappings(YjGroupInfo, data['groups'])
            session.bulk_insert_mappings(YjVariableInfo, data['variables'])
            # session.bulk_insert_mappings(YjVariableInfo, data['variables'])

            # # todo 速度测试
            # time1 = time.time()
            #
            # # 添加'sqlalchemy' table数据
            # print('*********', data['groups_variables'], '**********')
            # relation_dict = {
            #     'group': {},
            #     'var': {}
            # }
            #
            # i = 0
            # for model in data['groups_variables']:
            #     if relation_dict['var'].__contains__(str(model['variable_id'])):
            #         variable_model = relation_dict['var'][str(model['variable_id'])]
            #     else:
            #         variable_model = session.query(YjVariableInfo).filter_by(id=model['variable_id']).first()
            #         relation_dict['var'][str(model['variable_id'])] = variable_model
            #
            #     if relation_dict['group'].__contains__(str(model['variable_id'])):
            #         group_model = relation_dict['group'][str(model['group_id'])]
            #     else:
            #         group_model = session.query(YjGroupInfo).filter_by(id=model['group_id']).first()
            #         relation_dict['group'][str(model['group_id'])] = group_model
            #
            #     if group_model and variable_model:
            #         group_model.variables.append(variable_model)
            #     else:
            #         i += 1
            #         a = model
            #
            # print(relation_dict)
            # time2 = time.time()
            # print(time2 - time1)
            # print(i, a)

            status = 'OK'
            note = '成功更新配置信息.'

            # todo 发送获取配置完成的信息
            # result = server_confirm('http://fdslaf')
            result = server_confirm(CONFIRM_CONFIG_URL)


        else:
            status = 'error'
            note = '获取配置时发生未知问题，检查服务器代码。 状态码：{}'.format(
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


def upload_data(group_model, current_time):
    """
    查询该组内需要上传的变量，从数据库中取出变量对应的数值
    
    :param group_model: 上传组数据库数据对象
    :param current_time: 当前时间
    :return: 变量值列表
    """

    logging.debug('上传数据打包')

    # 建立数据库连接
    session = Session()

    # 获取该组信息
    group_id = group_model.id
    group_name = group_model.group_name
    server_record_cycle = group_model.server_record_cycle

    # print(type(group_name))

    # 准备本次上传的数据
    variables = group_model.variables
    variable_list = list()

    for variable in variables:

        # 判断该变量是否需要上传
        if variable.is_upload:

            # 获取上次传输时间,没有上次时间就往前推一个上传周期
            get_time = current_time - group_model.upload_cycle

            # 读取需要上传的值,所有时间大于上次上传的值
            all_values = session.query(Value).filter_by(variable_id=variable.id).filter(
                get_time <= Value.time).filter(Value.time < current_time)

            # 循环从上次读取时间开始计算，每个一个记录周期提取一个数值
            while get_time < current_time:
                upload_value = all_values.filter(
                    get_time + server_record_cycle > Value.time).filter(Value.time >= get_time).first()
                # 当上传时间小于采集时间时，会出现取值时间节点后无采集数据，得到None，使得后续语句报错。
                try:
                    value_dict = serialize(upload_value)
                    variable_list.append(value_dict)
                except UnmappedClassError:
                    pass

                get_time += server_record_cycle

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
    :param variable_list: 
    :param group_model: 
    :param current_time: 
    :return: 
    """

    logging.debug('上传数据')

    # 建立数据库连接
    session = Session()

    # 获取本机信息
    id_num = r.get('id_num')

    # 获取变量组基本信息
    group_id = group_model.id
    group_name = group_model.group_name.encode('utf-8')

    # 包装数据
    data = {
        'id_num': id_num,
        'group_id': group_id,
        'value': variable_list
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
            status=data['status'],
            note=note
        )
        session.add(log)

    session.commit()
    session.close()


@app.task(bind=True, rate_limit='6/m', max_retries=MAX_RETRIES, default_retry_delay=3)
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

        group_models = session.query(YjGroupInfo).filter(current_time >= YjGroupInfo.upload_time).filter(
            YjGroupInfo.is_upload is True).filter(
            YjGroupInfo.uploading is not True).all()

        for group_model in group_models:
            group_model.upload_time = current_time + group_model.upload_cycle
            value_list = upload_data(group_model, current_time)
            upload(value_list, group_model, current_time)

        session.commit()
    except SoftTimeLimitExceeded as e:
        pass
    finally:
        session.close()


@app.task(rate_limit='6/m', max_retries=MAX_RETRIES, default_retry_delay=3)
def check_variable_get_time():
    """
    检查变量采集时间，采集满足条件的变量值

    :return: 
    """

    time1 = time.time()
    logging.debug('检查变量采集时间')

    # 建立数据库连接
    session = Session()

    current_time = int(time.time())

    plc_client = r.get('plc')
    print(plc_client)
    for plc in plc_client:
        # todo 循环内部 使用并发
        groups = session.query(YjGroupInfo).filter(YjGroupInfo.plc_id == plc[3]).filter(
            current_time >= YjGroupInfo.acquisition_time).all()
        for group in groups:

            # 更新变量下次获取时间
            group.acquisition_time = group.acquisition_cycle + current_time
            variables = group.variables
            session.commit()

            if variables:
                print(variables)
                readsuan(variables)
                # while len(variables) > 0:
                #     variable_group = variables[:18]
                #     variables = variables[18:]
                #
                #     print(variables)
                #
                #     try:
                #
                #         read_multi(plc, variable_group, current_time)
                #     except Exception as e:
                #         logging.error('plc读取数据错误' + str(e))
                #         continue
                #     else:
                #         plc[5] = current_time

            else:
                # 没有变量需要采集时，进行一次连接来测试通信状态

                check_plc_connected(plc, current_time)

    time2 = time.time()
    print('采集时间' + str(time2 - time1))
    r.set('plc', plc_client)

    session.close()


def read_multi(plc, variables, current_time):
    time1 = time.time()
    print('采集')
    session = Session()
    value_list = list()

    var_num = len(variables)
    print('采集数量：{}'.format(var_num))
    bool_indexes = list()
    data_items = (S7DataItem * var_num)()

    for num in range(var_num):
        area = variable_area(variables[num].area)
        db_number = variables[num].db_num
        size = variable_size(variables[num].data_type)
        address = int(math.modf(variables[num].address)[1])
        bool_index = round(math.modf(variables[num].address)[0] * 10)
        bool_indexes.append(bool_index)

        data_items[num].Area = ctypes.c_int32(area)
        data_items[num].WordLen = ctypes.c_int32(S7WLByte)
        data_items[num].Result = ctypes.c_int32(0)
        data_items[num].DBNumber = ctypes.c_int32(db_number)
        data_items[num].Start = ctypes.c_int32(address)
        data_items[num].Amount = ctypes.c_int32(size)  # reading a REAL, 4 bytes

    for di in data_items:
        # create the buffer
        buffer = ctypes.create_string_buffer(di.Amount)

        # cast the pointer to the buffer to the required type
        pBuffer = ctypes.cast(ctypes.pointer(buffer),
                              ctypes.POINTER(ctypes.c_uint8))
        di.pData = pBuffer

    client = snap7.client.Client()
    try:
        client.connect(plc[0], plc[1], plc[2])
    except Exception as e:
        logging.warning('PLC连接失败' + str(e))
        id_num = r.get('id_num')
        plc_alarm = connect_plc_err(
            id_num,
            level=0,
            plc_id=plc[3],
            plc_name=plc[4]
        )
        session.add(plc_alarm)
        session.commit()
        assert False
    else:
        result, data_items = client.read_multi_vars(data_items)

        # print(result, data_items)
        # for di in data_items:
        #     check_error(di.Result)

        for num in range(0, var_num):
            di = data_items[num]

            raw_value = read_value(
                variables[num].data_type,
                di.pData,
                bool_index=bool_indexes[num]
            )

            # 数模转换
            if variables[num].is_analog:
                raw_value = analog2digital(variables[num], raw_value)

            offset = variables[num].offset if isinstance(variables[num].offset, float) else 0
            value = round(raw_value + offset, 2)
            print(value)

            # value_model = Value(
            #     variable_id=variables[num].id,
            #     time=current_time,
            #     value=value
            # )
            value_model = {
                'variable_id': variables[num].id,
                'time': current_time,
                'value': value
            }
            # session.add(value_model)
            value_list.append(value_model)

        # session.bulk_save_objects(value_list)
        session.bulk_insert_mappings(Value, value_list)

    session.commit()
    session.close()

    time2 = time.time()
    print(time2 - time1)


# def read(plc, variables, current_time):

@app.task()
def ntpdate():
    ntp = subprocess.call('ntpdate cn.ntp.org.cn', shell=True)
    print(ntp)


@app.task
def server_confirm(url):
    """
    发送请求后，收到服务器回执的确认
    
    :param url: 具体确认某个功能的地址
    :return: 
    """

    id_num = r.get('id_num')
    post_data = {
        'id_num': id_num
    }

    try:
        rp = requests.post(url, json=post_data)
    except ConnectionError as e:
        logging.warning('确认请求发送失败: ' + str(e))
    else:
        http_code = rp.status_code
        if http_code == 200:
            # todo 成功确认
            pass
        else:
            # todo 失败 重试请求
            print('1')
            pass

    print('complete')
    return 'app'


def plc_write(variable_model, plc_cli, plc_model):
    id_num = r.get('id_num')
    # 获取变量读写类型
    rw_type = variable_model.rw_type
    value = variable_model.write_value

    # 判断变量存在写操作
    if rw_type == 2 or rw_type == 3 and value is not None:

        # 获取写入变量值所需信息
        data_type = variable_model.data_type
        db = variable_model.db_num
        area = variable_area(variable_model)
        address = int(math.modf(variable_model.address)[1])
        bool_index = round(math.modf(variable_model.address)[0] * 10)
        size = variable_size(data_type)

        # 获取当前字节
        try:
            result = plc_cli.read_area(
                area=area,
                dbnumber=db,
                start=address,
                size=size
            )
        except Exception as e:
            logging.error(e)

            session = Session()
            alarm = read_err(
                id_num=id_num,
                plc_id=plc_model.id,
                plc_name=plc_model.plc_name,
                area=area,
                db_num=db,
                start=address,
                data_type=data_type
            )
            session.add(alarm)
            session.commit()

        else:

            # 将写入数据转为字节码
            byte_value = write_value(
                data_type,
                result,
                value,
                bool_index=bool_index
            )

            # 数据写入
            plc_cli.write_area(
                area=area,
                dbnumber=db,
                start=address,
                data=byte_value
            )


def beats_data(id_num, session, con_time, current_time):
    # 获取心跳间隔时间内产生的报警
    station_alarms = list()
    plc_alarms = list()
    if con_time:
        station = session.query(StationAlarm).filter(con_time <= StationAlarm.time). \
            filter(StationAlarm.time < current_time).all()
        for s in station:
            station_alarms.append(serialize(s))

        plc = session.query(PLCAlarm).filter(PLCAlarm.level >= 2). \
            filter(con_time <= PLCAlarm.time).filter(PLCAlarm.time < current_time).all()
        for p in plc:
            plc_alarms.append(serialize(p))

    data = dict(
        id_num=id_num,
        station_alarms=station_alarms,
        plc_alarms=plc_alarms
    )

    return data


def check_plc_connected(plc, current_time):
    # 没有变量需要采集时，进行一次连接来测试通信状态

    client = snap7.client.Client()
    client.connect(plc[0], plc[1], plc[2])
    if client.get_connected():
        plc[5] = current_time
