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

from celery import Celery
from celery.exceptions import MaxRetriesExceededError
from sqlalchemy.orm.exc import UnmappedClassError
from sqlalchemy.exc import IntegrityError
from snap7.snap7exceptions import Snap7Exception
import snap7
from snap7.snap7types import S7DataItem, S7WLByte

from models import eng, Base, Session, YjStationInfo, YjPLCInfo, YjGroupInfo, YjVariableInfo, \
    Value, serialize, VarGroups, AlarmInfo
import celeryconfig
from data_collection import variable_size, variable_area, read_value, write_value, snap7_path, analog2digital
from utils.station_alarm import check_time_err, connect_server_err, server_return_err, db_commit_err
from utils.plc_alarm import connect_plc_err, read_err
from util import encryption_client, decryption_client
from param import (ID_NUM, BEAT_URL, CONFIG_URL, UPLOAD_URL, CONFIRM_CONFIG_URL, CONNECT_TIMEOUT, REQUEST_TIMEOUT,
                   MAX_RETRIES, CHECK_DELAY, SERVER_TIMEOUT, PLC_TIMEOUT, START_TIMEDELTA, NTP_SERVER)
from data_collection_2 import readsuan
from utils.redis_middle_class import ConnDB
from utils.station_data import redis_add_alarm_variables, beats_data

# 初始化celery
app = Celery()
app.config_from_object(celeryconfig)

# 日志
logging.basicConfig(level=logging.INFO)
# logging.basicConfig(filename='logger.log', level=logging.INFO)
logging.getLogger(__name__).addHandler(logging.NullHandler())

# 获取当前目录位置
here = os.path.abspath(os.path.dirname(__file__))

# 读取snap7 C库
lib_path = snap7_path()

snap7.common.load_library(here + lib_path)

r = ConnDB()

# 初始化requests
req_s = requests.Session()
req_s.mount('http://', HTTPAdapter(max_retries=5))
req_s.mount('https://', HTTPAdapter(max_retries=5))


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


def plc_connection(plcs):
    """
    连接plc，将连接实例存入list
    
    :param plcs: sqlalchemy数据库查询对象列表
    :return: snap7 client实例元组 [0]plc ip地址 [1]plc 机架号  [2]plc 插槽号 [3]plc 配置数据主键 [4]plc 名称 [5]plc 连接时间
    """

    current_time = int(time.time())
    plc_client = list()
    for plc in plcs:
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

    # 获取该终端所有PLC信息
    plcs = session.query(YjPLCInfo)

    # 建立group信息
    group_upload_data = []
    r.set('group_upload', group_upload_data)
    group_read_data = []
    r.set('group_read', group_read_data)

    # 建立variable信息
    variable_data = []
    r.set('variable', variable_data)

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
            )
            session.add(alarm)

        else:
            # 获取该PLC下所有组信息
            groups = plc.groups

            # 设定变量组信息
            for g in groups:
                # 变量组参数
                upload_cycle = g.upload_cycle if isinstance(g.upload_cycle, int) else 30
                acquisition_cycle = g.acquisition_cycle if isinstance(g.acquisition_cycle, int) else 30
                plc_id = g.plc_id
                variable_id = [model.variable.id for model in g.variables]
                group_id = g.id
                server_record_cycle = g.server_record_cycle
                group_name = g.group_name
                print('acquisition_cycle', acquisition_cycle)

                # 设定变量组初始上传时间,
                group_upload_info = {
                    'id': group_id,
                    'plc_id': plc_id,
                    'upload_time': start_time + upload_cycle,
                    'is_uploading': False,
                    'upload_cycle': upload_cycle,
                    'server_record_cycle': server_record_cycle,
                    'variable_id': variable_id,
                    'group_name': group_name
                }
                group_upload_data = r.get('group_upload')
                if isinstance(group_upload_data, list):
                    group_upload_data.append(group_upload_info)
                else:
                    group_upload_data = [group_upload_info]
                r.set('group_upload', group_upload_data)

                # 设定变量组读取时间
                group_read_info = {
                    'id': group_id,
                    'plc_id': plc_id,
                    'variable_id': variable_id,
                    'read_time': start_time + acquisition_cycle,
                    'read_cycle': acquisition_cycle
                }
                group_read_data = r.get('group_read')
                if isinstance(group_read_data, list):
                    group_read_data.append(group_read_info)
                else:
                    group_read_data = [group_read_info]
                r.set('group_read', group_read_data)

                # 设定变量信息
                variable_info = {
                    'group_id': g.id,
                    'variables': []
                }
                for var in g.variables:
                    variable = var.variable
                    var_info = {
                        'id': variable.id,
                        'db_num': variable.db_num,
                        'address': variable.address,
                        'data_type': variable.data_type,
                        'area': variable.area,
                        'is_analog': variable.is_analog,
                        'analog_low_range': variable.analog_low_range,
                        'analog_high_range': variable.analog_high_range,
                        'digital_low_range': variable.digital_low_range,
                        'digital_high_range': variable.digital_high_range,
                        'offset': variable.offset
                    }
                    variable_info['variables'].append(var_info)

                variable_data = r.get('variable')
                if isinstance(variable_data, list):
                    variable_data.append(variable_info)
                else:
                    variable_data = [variable_info]
                r.set('variable', variable_data)

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
    
    :param : 
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
    data = encryption_client(data)

    # 发送心跳包
    try:
        rv = req_s.post(BEAT_URL, data=data, timeout=(CONNECT_TIMEOUT, REQUEST_TIMEOUT))

    # 连接服务器失败
    except (ConnectionError, MaxRetriesExceededError) as e:
        logging.warning('心跳连接错误：' + str(e))
        log = connect_server_err(id_num)
        session.add(log)
        session.commit()

    # 连接成功
    else:
        # data = decryption_client(rv.json())
        print(rv.status_code)
        data = rv.json()
        print(data)

        # 更新服务器通讯时间
        r.set('con_time', current_time)

        # 配置有更新
        if data['is_modify'] == 1:
            logging.info('发现配置有更新，准备获取配置')
            get_config()
            before_running()


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

    # 获取本机信息
    id_num = r.get('id_num')

    post_data = {
        'id_num': id_num
    }

    logging.info('获取配置，发送请求：' + str(post_data))

    # 连接服务器
    try:
        rv = req_s.post(CONFIG_URL, json=post_data, timeout=(CONNECT_TIMEOUT, REQUEST_TIMEOUT))

    # 连接失败
    except ConnectionError as e:
        logging.warning('获取配置错误：' + str(e))

        log = connect_server_err(id_num)
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

        if rv.status_code == 200:
            rp = rv.json()

            # data = rp['data']
            data = decryption_client(rp['data'])

            print(data)

            # 配置更新，删除现有表
            try:
                session.query(VarGroups).delete()
                session.query(AlarmInfo).delete()
                session.query(YjVariableInfo).delete()
                session.query(YjStationInfo).delete()
                session.query(YjPLCInfo).delete()
                session.query(YjGroupInfo).delete()

            except IntegrityError as e:
                session.rollback()
                logging.error('更新配置时，删除旧表出错: ' + str(e))
                alarm = db_commit_err(id_num, 'get_config')
                session.add(alarm)
                session.commit()

            else:
                session.flush()

            # 添加'sqlalchemy' class数据
            session.bulk_insert_mappings(YjStationInfo, [data['stations']])
            session.bulk_insert_mappings(YjPLCInfo, data['plcs'])
            session.bulk_insert_mappings(YjGroupInfo, data['groups'])
            session.bulk_insert_mappings(YjVariableInfo, data['variables'])
            session.bulk_insert_mappings(VarGroups, data['variables_groups'])
            session.bulk_insert_mappings(AlarmInfo, data['alarm'])

            # todo 发送获取配置完成的信息
            result = server_confirm(CONFIRM_CONFIG_URL, session)
            if result:
                logging.info('配置获取完成')

        else:
            log = server_return_err(id_num, 'get_config')
            session.add(log)
    finally:
        session.commit()
        session.close()

        # 记录服务器连接状况


def upload_data(group, current_time):
    """
    查询该组内需要上传的变量，从数据库中取出变量对应的数值
    
    :param group: 上传组参数字典
    :param current_time: 当前时间
    :return: 变量值列表
    """

    logging.debug('上传数据打包')

    # 建立数据库连接
    session = Session()

    # 获取该组信息
    print(group)
    server_record_cycle = group['server_record_cycle']

    # 准备本次上传的数据
    variables = group['variable_id']
    variable_list = list()

    for variable in variables:

        # 获取上次传输时间,没有上次时间就往前推一个上传周期
        get_time = current_time - group['upload_cycle']

        # 读取需要上传的值,所有时间大于上次上传的值
        all_values = session.query(Value).filter_by(variable_id=variable).filter(
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

    session.commit()
    session.close()

    return variable_list


def upload(variable_list, group):
    """
    数据上传
    :param variable_list: 
    :param group: 
    :return: 
    """

    logging.debug('上传数据')

    # 建立数据库连接
    session = Session()

    # 获取本机信息
    id_num = r.get('id_num')

    # 获取变量组基本信息
    group_id = group['id']
    group_name = group['group_name'].encode('utf-8')

    # 包装数据
    data = {
        'id_num': id_num,
        'group_id': group_id,
        'value': variable_list
    }
    # print(data)
    data = encryption_client(data)

    # 上传日志记录
    logging.info('group_id: {} group_name:{} 将要上传.'.format(group_id, group_name))

    # 连接服务器，准备上传数据
    try:
        rv = req_s.post(UPLOAD_URL, data=data, timeout=(CONNECT_TIMEOUT, REQUEST_TIMEOUT))
    except ConnectionError as e:
        logging.warning('上传数据错误：' + str(e))

        alarm = connect_server_err(id_num)
        session.add(alarm)

    else:
        # 日志记录
        # 正常传输
        if rv.status_code == 200:
            logging.info('group_id: {} group_name:{} 成功上传.'.format(group_id, group_name))

        # 未知错误
        else:
            logging.error('upload无法识别服务端反馈 group_id: {} group_name:{}'.format(group_id, group_name))
            log = server_return_err(id_num, 'upload group_id: {} group_name:{}'.format(group_id, group_name))
            session.add(log)

    session.commit()
    session.close()


@app.task(rate_limit='6/m', max_retries=MAX_RETRIES, default_retry_delay=3)
def check_group_upload_time():
    """
    检查变量组上传时间，将满足条件的变量组数据打包上传
    
    :return: 
    """
    upload_time1 = time.time()
    logging.debug('检查变量组上传时间')
    print('上传')

    # 建立数据库连接
    session = Session()

    current_time = int(time.time())

    # 在redis中查询需要上传的变量组id
    group_upload_data = r.get('group_upload')

    print(group_upload_data)
    group_id = []
    for g in group_upload_data:
        if current_time >= g['upload_time']:
            group_id.append(g['id'])
            g['upload_time'] = current_time + g['upload_cycle']
            g['is_uploading'] = True

    r.set('group_upload', group_upload_data)

    print(group_id)

    for group in group_upload_data:
        # todo 多线程
        value_list = upload_data(group, current_time)
        print('上传数据')
        # print(value_list)
        upload(value_list, group)

    # 设置为不在上传的状态
    group_data = r.get('group')
    for g in group_data:
        if g['id'] in group_id:
            g['is_uploading'] = False
    r.set('group', group_data)

    try:
        session.commit()
    except IntegrityError as e:
        session.rollback()
        logging.error('提交数据库修改出错: ' + str(e))
        id_num = r.get('id_num')
        alarm = db_commit_err(id_num, 'check_group')
        session.add(alarm)
        session.commit()
    else:
        session.flush()
    finally:
        session.close()
        upload_time2 = time.time()
        print('上传时间', upload_time2-upload_time1)


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
    # print(plc_client)

    group_read_data = r.get('group_read')

    for plc in plc_client:
        # todo 循环内部 使用并发

        group_id = []
        for v in group_read_data:
            if v['plc_id'] == plc[3] and current_time >= v['read_time']:
                group_id.append(v['id'])
                v['read_time'] = current_time + v['read_cycle']
        r.set('group_read', group_read_data)

        group_data = r.get('variable')
        groups = [group for group in group_data if group['group_id'] in group_id]

        for group in groups:
            variables = group['variables']

            if variables:
                # print(variables)
                # readsuan(variables)
                while len(variables) > 0:
                    variable_group = variables[:18]
                    variables = variables[18:]

                    # print(len(variables))

                    try:

                        read_multi(plc, variable_group, current_time)
                    except Exception as e:
                        logging.error('plc读取数据错误' + str(e))
                        continue
                    else:
                        plc[5] = current_time

            else:
                # 没有变量需要采集时，进行一次连接来测试通信状态

                check_plc_connected(plc, current_time)

    time2 = time.time()
    print('采集时间' + str(time2 - time1))
    r.set('plc', plc_client)

    session.close()


def read_multi(plc, variables, current_time):
    time1 = time.time()
    # print('采集')
    session = Session()
    value_list = list()

    var_num = len(variables)
    # print('采集数量：{}'.format(var_num))
    bool_indexes = list()
    data_items = (S7DataItem * var_num)()

    for num in range(var_num):
        area = variable_area(variables[num]['area'])
        db_number = variables[num]['db_num']
        size = variable_size(variables[num]['data_type'])
        address = int(math.modf(variables[num]['address'])[1])
        bool_index = round(math.modf(variables[num]['address'])[0] * 10)
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
        )
        session.add(plc_alarm)
        session.commit()
        assert False
    else:
        result, data_items = client.read_multi_vars(data_items)

        for num in range(0, var_num):
            di = data_items[num]

            raw_value = read_value(
                variables[num]['data_type'],
                di.pData,
                bool_index=bool_indexes[num]
            )

            # 数模转换
            if variables[num]['is_analog']:
                raw_value = analog2digital(
                    raw_value,
                    variables[num]['analog_low_range'],
                    variables[num]['analog_high_range'],
                    variables[num]['digital_low_range'],
                    variables[num]['digital_high_range']
                )

            # 数据量修改
            offset = variables[num]['offset'] if isinstance(variables[num]['offset'], float) else 0
            # 限制小数位数
            value = round(raw_value, 2) + offset
            # print(value)

            value_model = {
                'variable_id': variables[num]['id'],
                'time': current_time,
                'value': value
            }

            value_list.append(value_model)

        session.bulk_insert_mappings(Value, value_list)

    try:
        session.commit()
    except IntegrityError as e:
        session.rollback()
        logging.error('提交数据库修改出错: ' + str(e))
        id_num = r.get('id_num')
        alarm = db_commit_err(id_num, 'read_multi')
        session.add(alarm)
        session.commit()
    else:
        session.flush()
    finally:
        session.close()

    time2 = time.time()
    # print(time2 - time1)


# def read(plc, variables, current_time):

@app.task()
def ntpdate():
    # todo 待测试 使用supervisor启动时用户为root 不需要sudo输入密码 不安全
    pw = 'touhou'

    cmd2 = 'echo {} | sudo -S ntpdate {}'.format(pw, NTP_SERVER)
    ntp = subprocess.Popen(
        cmd2,
        shell=True,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    ntp.wait()  # 判断进程执行状态
    stdout, stderr = ntp.communicate()

    print(stdout.decode('utf-8'))
    print(stderr.decode('utf-8'))
    # todo 日志写入


@app.task
def server_confirm(url, session):
    """
    发送请求后，收到服务器回执的确认
    
    :param url: 具体确认某个功能的地址
    :param session:
    :return: 
    """

    id_num = r.get('id_num')
    post_data = {
        'id_num': id_num
    }

    try:
        rp = req_s.post(url, json=post_data, timeout=(CONNECT_TIMEOUT, REQUEST_TIMEOUT))
    except ConnectionError as e:
        logging.warning('确认请求发送失败: ' + str(e))
        alarm = connect_server_err(id_num, 'confirm')
        session.add(alarm)
        return False
    else:
        http_code = rp.status_code
        if http_code == 200:
            return True
        else:
            return False


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


def check_plc_connected(plc, current_time):
    # 没有变量需要采集时，进行一次连接来测试通信状态

    client = snap7.client.Client()
    client.connect(plc[0], plc[1], plc[2])
    if client.get_connected():
        plc[5] = current_time


@app.task()
def check_alarm():
    alarm_variables = r.get('alarm_variables')

    if not alarm_variables:
        alarm_variables = redis_add_alarm_variables()
        if not alarm_variables:
            return
        r.set('alarm_variables', alarm_variables)

    # 循环报警变量，查看最近采集的数值是否满足报警条件
    current_time = time.time()
    session = Session()
    alarm_data = list()

    for alarm in alarm_variables:
        # 获取需要判断的采集数据
        if alarm['delay']:
            values = session.query(Value).filter_by(variable_id=alarm['variable_id']). \
                filter(Value.time > current_time - alarm['delay'] - 1).all()
        else:
            values = session.query(Value).filter_by(variable_id=alarm['variable_id']). \
                order_by(Value.time.desc()).limit(1).all()

        is_alarm = False
        if alarm['type'] == 1:
            for v in values:
                if v.value == alarm['bool']:
                    is_alarm = True
                else:
                    is_alarm = False
                    break

        elif alarm['type'] == 2:
            if alarm['symbol'] == 1:
                for v in values:
                    if v.value > alarm['limit']:
                        is_alarm = True
                    else:
                        is_alarm = False
                        break

            elif alarm['symbol'] == 2:
                for v in values:
                    if v.value >= alarm['limit']:
                        is_alarm = True
                    else:
                        is_alarm = False
                        break

            elif alarm['symbol'] == 3:
                for v in values:
                    if v.value < alarm['limit']:
                        is_alarm = True
                    else:
                        is_alarm = False
                        break

            elif alarm['symbol'] == 4:
                for v in values:
                    if v.value <= alarm['limit']:
                        is_alarm = True
                    else:
                        is_alarm = False
                        break

            else:
                is_alarm = False

        else:
            is_alarm = False

        if is_alarm:
            alarm_data.append({
                'variable_id': alarm['vairable_id'],
                'is_alarm': is_alarm
            })

    if alarm_data:
        alarm_info = {'time': current_time, 'data': alarm_data}
        old_alarm = r.get('alarm_info')
        if old_alarm:
            old_alarm.append(alarm_info)
            r.set('alarm_info', old_alarm)
        else:
            r.set('alarm_info', list(alarm_info))

        print(alarm_info)
    print(alarm_variables)

    return
