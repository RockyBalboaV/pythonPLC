# coding=utf-8

import os
import requests
import ctypes
import time
import subprocess
import math
import logging
import datetime
import json

from requests.adapters import HTTPAdapter
from requests.exceptions import ConnectionError
from celery import Celery
from celery.exceptions import MaxRetriesExceededError, SoftTimeLimitExceeded
from sqlalchemy.orm.exc import UnmappedClassError
from sqlalchemy.exc import IntegrityError
from snap7.client import Client
from snap7.snap7exceptions import Snap7Exception
from snap7.snap7types import S7DataItem, S7WLByte

from models import eng, Base, YjStationInfo, YjPLCInfo, YjGroupInfo, YjVariableInfo, \
    Value, VarGroups, AlarmInfo, value_serialize, session, Session
from data_collection import variable_size, variable_area, read_value, write_value, load_snap7, analog2digital
from utils.station_alarm import check_time_err, connect_server_err, server_return_err, db_commit_err, ntpdate_err
from utils.plc_alarm import connect_plc_err, read_err
from util import encryption_client, decryption_client
from param import (ID_NUM, BEAT_URL, CONFIG_URL, UPLOAD_URL, CONFIRM_CONFIG_URL, CONNECT_TIMEOUT, REQUEST_TIMEOUT,
                   MAX_RETRIES, CHECK_DELAY, SERVER_TIMEOUT, PLC_TIMEOUT, START_TIMEDELTA, NTP_SERVER)
from utils.redis_middle_class import ConnDB
from utils.station_data import redis_alarm_variables, beats_data, plc_info, redis_group_read_info, \
    redis_group_upload_info, redis_variable_info
from utils.plc_client import plc_client

# from data_collection_2 import readsuan

# 获取当前目录位置
here = os.path.abspath(os.path.dirname(__file__))

# 初始化celery
app = Celery(
    'test_celery'
)
app.config_from_object('celeryconfig', force=True)

# 日志
logging.basicConfig(level=logging.WARN)
# logging.basicConfig(filename='logger.log', level=logging.INFO)
logging.getLogger(__name__).addHandler(logging.NullHandler())

# 读取snap7 C库
load_snap7()

# redis连接
r = ConnDB()

# 初始化requests
req_s = requests.Session()
req_s.mount('http://', HTTPAdapter(max_retries=MAX_RETRIES))
req_s.mount('https://', HTTPAdapter(max_retries=MAX_RETRIES))


def database_reset():
    """
    初始化数据库
    
    :return: 
    """

    Base.metadata.drop_all(bind=eng)
    Base.metadata.create_all(bind=eng)


def boot():
    """
    开机初次运行
    
    :return: 
    """

    logging.debug('boot ruuning')

    Base.metadata.create_all(bind=eng)

    r.set('id_num', ID_NUM)


def before_running():
    """
    运行前设置
    
    :return: 
    """
    logging.debug('运行前初始化')

    # 清除上次运行数据
    r.set('group_upload', None)
    r.set('group_read', None)
    r.set('variable', None)
    r.set('alarm_info', None)
    r.set('check_time', None)
    r.set('plc', None)
    r.set('con_time', None)

    # session = Session()
    try:
        # 设定服务开始运行时间
        current_time = int(time.time())
        start_time = current_time + START_TIMEDELTA

        # 设定报警信息
        redis_alarm_variables(r)

        # 获取该终端所有PLC信息
        plc_models = session.query(YjPLCInfo).all()

        # 缓存PLC信息
        plc_data = plc_info(r, plc_models)
        logging.info('PLC配置信息： ' + str(plc_data))

        for plc in plc_models:

            # 获得该PLC的信息
            ip = plc.ip
            rack = plc.rack
            slot = plc.slot

            # client = snap7.client.Client()
            #
            # try:
            #     logging.debug('plc连接尝试 ip:{} rack:{} slot:{}'.format(ip, rack, slot))
            #     client.connect(ip, rack, slot)
            # except Snap7Exception as e:
            #     logging.error('PLC无法连接，请查看PLC状态' + str(e))

            with plc_client(ip, rack, slot) as client:
                # print(client.get_connected())
                # 获取该PLC下所有组信息
                groups = plc.groups

                # 设定变量组信息
                for g in groups:
                    if g.is_upload:
                        redis_group_upload_info(r, g, start_time)
                    redis_group_read_info(r, g, start_time)
                    redis_variable_info(r, g)
                    # print(r.get('group_upload'))
                    # print(r.get('group_read'))
                    # print(r.get('variable'))

                    # 变量写入
                    # 获取该变量组下所有变量信息
                    # variables = g.variables

                    # if variables:
                    #     for v in variables:
                    #         plc_write(v, plc_cli, plc)

                    # client.disconnect()
                    # client.destroy()
        # 数据库写入操作后，关闭数据库连接
        session.commit()

    except Exception as e:
        logging.exception('before_running' + str(e))
        session.rollback()
    finally:
        session.close()


@app.task(bind=True, default_retry_delay=10, max_retries=3)
def self_check(self):
    """
    celery任务
    定时自检
    
    :return: 
    """

    logging.debug('自检')

    current_time = int(time.time())

    # session = Session()
    try:
        # 获取站点配置信息
        id_num = r.get('id_num')

        # 获取上次检查时间并检查时间间隔，判断程序运行状态
        check_time = r.get('check_time')
        if check_time:
            check_time = int(check_time)
            # logging.debug('上次检查时间：{}'.format(datetime.datetime.fromtimestamp(check_time)))
            if current_time - check_time > CHECK_DELAY:
                alarm = check_time_err(id_num)
                session.add(alarm)
        r.set('check_time', current_time)

        # 检查与服务器通讯状态
        con_time = r.get('con_time')
        if con_time:
            con_time = int(con_time)
            # logging.debug('上次服务器通讯时间：{}'.format(datetime.datetime.fromtimestamp(con_time)))
            if current_time - con_time > SERVER_TIMEOUT:
                alarm = connect_server_err(id_num)
                session.add(alarm)

        # 检查PLC通讯状态
        plcs = r.get('plc')
        if not plcs:
            plc_models = session.query(YjPLCInfo)
            plcs = plc_info(r, plc_models)
            r.set('plc', plcs)

        for plc in plcs:
            plc_connect_time = int(plc['time'])
            # logging.debug('PLC连接时间：{}'.format(datetime.datetime.fromtimestamp(plc_connect_time)))

            # 超过一定时间的上传服务器
            if current_time - plc_connect_time > PLC_TIMEOUT:
                alarm = connect_plc_err(
                    id_num,
                    plc_id=plc['id'],
                )
                session.add(alarm)

        # 数据库写入，关闭连接
        session.commit()
    except Exception as e:
        logging.exception('self_check' + str(e))
        session.rollback()
    finally:
        session.close()


@app.task(bind=True, default_retry_delay=5, max_retries=3)
def beats(self):
    """
    celery任务
    与服务器的心跳连接
    
    :param : 
    :return: 
    """
    time1 = time.time()
    logging.debug('心跳连接')

    session = Session()
    try:

        current_time = int(time.time())

        # 从数据库获取站点信息
        id_num = ID_NUM

        # 获取上次心跳时间
        con_time = r.get('con_time')

        # 获取心跳时上传的数据
        data = beats_data(id_num, con_time, current_time)
        # print(data)
        data = encryption_client(data)

        # 发送心跳包
        try:
            rv = req_s.post(BEAT_URL, data=data, timeout=(CONNECT_TIMEOUT, REQUEST_TIMEOUT))

        # 连接服务器失败
        except (ConnectionError, MaxRetriesExceededError) as e:
            logging.warning('心跳连接错误：' + str(e))
            log = connect_server_err(id_num)
            session.add(log)

        # 连接成功
        else:
            # data = decryption_client(rv.json())
            # print(rv.status_code)
            data = rv.json()
            # print(data)

            # 更新服务器通讯时间
            r.set('con_time', current_time)

            # 配置有更新
            if data['is_modify'] == 1:
                logging.info('发现配置有更新，准备获取配置')
                get_config()
                before_running()
        finally:
            session.commit()

    except Exception as e:
        logging.exception('beats' + str(e))
        session.rollback()
    finally:
        session.close()
        time2 = time.time()
        print('beats', time2 - time1)


@app.task(bind=True, default_retry_delay=3, max_retries=3)
def get_config(self):
    """
    连接服务器接口，获取本机变量信息
    
    :return: 
    """
    time1 = int(time.time())
    logging.debug('连接服务器,获取数据')

    # session = Session()
    try:

        current_time = time.time()

        # 获取本机信息
        id_num = r.get('id_num')

        post_data = {
            'id_num': id_num
        }
        post_data = json.dumps(post_data)
        # logging.info('获取配置，发送请求：' + str(post_data))

        # 连接服务器
        try:
            rv = req_s.post(CONFIG_URL, data=post_data, timeout=(CONNECT_TIMEOUT, REQUEST_TIMEOUT))

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

                # print(data)

                # 配置更新，删除现有表
                try:
                    session.query(VarGroups).delete()
                    session.query(AlarmInfo).delete()
                    session.query(YjVariableInfo).delete()
                    session.query(YjStationInfo).delete()
                    session.query(YjPLCInfo).delete()
                    session.query(YjGroupInfo).delete()

                except IntegrityError as e:
                    logging.error('更新配置时，删除旧表出错: ' + str(e))
                    session.rollback()
                    alarm = db_commit_err(id_num, 'get_config')
                    session.add(alarm)
                else:
                    session.flush()

                # 添加'sqlalchemy' class数据
                session.bulk_insert_mappings(YjStationInfo, [data['stations']])
                session.bulk_insert_mappings(YjPLCInfo, data['plcs'])
                session.bulk_insert_mappings(YjGroupInfo, data['groups'])
                session.bulk_insert_mappings(YjVariableInfo, data['variables'])
                session.bulk_insert_mappings(VarGroups, data['variables_groups'])
                session.bulk_insert_mappings(AlarmInfo, data['alarm'])

                logging.debug('发送配置完成确认信息')
                result = server_confirm(CONFIRM_CONFIG_URL)
                if result:
                    logging.info('配置获取完成')
                else:
                    logging.error('无法向服务器确认获取配置已完成')

            else:
                log = server_return_err(id_num, 'get_config')
                session.add(log)
        finally:
            session.commit()

    except Exception as e:
        logging.exception('get_config' + str(e))
        session.rollback()
    finally:
        session.close()
        time2 = time.time()
        print('get_config', time2 - time1)

def upload_data(group, current_time):
    """
    查询该组内需要上传的变量，从数据库中取出变量对应的数值
    
    :param group: 上传组参数字典
    :param current_time: 当前时间
    :return: 变量值列表
    """

    logging.debug('上传数据打包')

    value_list = list()

    # session = Session()
    try:
        # 获取该组信息
        # print(group)
        server_record_cycle = group['server_record_cycle']

        # 准备本次上传的数据
        variables = group['var_id']

        for variable in variables:

            # 获取上次传输时间,没有上次时间就往前推一个上传周期
            if group['last_time'] is not None:
                get_time = group['last_time']
            else:
                get_time = current_time - group['upload_cycle']

            time1 = time.time()
            # 读取需要上传的值,所有时间大于上次上传的值
            all_values = session.query(Value).filter_by(var_id=variable).filter(
                get_time <= Value.time).filter(Value.time < current_time)

            # 循环从上次读取时间开始计算，每个一个记录周期提取一个数值
            while get_time < current_time:
                upload_value = all_values.filter(
                    get_time + server_record_cycle > Value.time).filter(Value.time >= get_time).order_by(Value.time.desc()).first()
                # print('get_time', get_time)
                # 当上传时间小于采集时间时，会出现取值时间节点后无采集数据，得到None，使得后续语句报错。
                if upload_value:
                    # print('数据时间', upload_value.time)
                    value_dict = value_serialize(upload_value)
                    value_list.append(value_dict)

                get_time += server_record_cycle

            time2 = time.time()
            # print('采样时间', time2 - time1)
        # print(value_list)
        session.commit()
    except Exception as e:
        logging.exception('upload_data' + str(e))
        session.rollback()
    finally:
        session.close()

    return value_list


def upload(variable_list, group_id):
    """
    数据上传
    :param variable_list: 
    :param group_id: 
    :return: 
    """

    logging.debug('上传数据')

    # session = Session()
    try:
        # 获取本机信息
        id_num = r.get('id_num')

        # 包装数据
        data = {
            'id_num': id_num,
            'value': variable_list
        }

        # print('上传数据数量', len(data['value']))

        data = encryption_client(data)

        # 上传日志记录
        # logging.info('group_id: {}将要上传.'.format(group_id))

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
                logging.info('group_id: {}成功上传.'.format(group_id))

            # 未知错误
            else:
                logging.error('upload无法识别服务端反馈 group_id: {}'.format(group_id))
                log = server_return_err(id_num, 'upload group_id: {}'.format(group_id))
                session.add(log)

        session.commit()

    except Exception as e:
        logging.exception('upload' + str(e))
        session.rollback()
    finally:
        session.close()


@app.task(bind=True, default_retry_delay=3, max_retries=3)
def check_group_upload_time(self):
    """
    检查变量组上传时间，将满足条件的变量组数据打包上传
    
    :return: 
    """
    upload_time1 = time.time()
    logging.debug('检查变量组上传时间')
    # print('上传')

    current_time = int(time.time())

    # session = Session()

    # 在redis中查询需要上传的变量组id
    group_upload_data = r.get('group_upload')

    # print(group_upload_data)

    for g in group_upload_data:
        if current_time >= g['upload_time']:
            g['is_uploading'] = True
    r.set('group_upload', group_upload_data)
    try:



        group_id = []
        value_list = list()


        for g in group_upload_data:
            if current_time >= g['upload_time']:
                value_list += upload_data(g, current_time)
                group_id.append(g['id'])
                g['last_time'] = g['upload_time']
                g['upload_time'] = current_time + g['upload_cycle']
                g['is_uploading'] = False

                # print('下次上传时间', datetime.datetime.fromtimestamp(g['upload_time']))



        # print(group_id)

        # print('上传数据', len(value_list), value_list)
        upload(value_list, group_id)

        # 设置为不在上传的状态
        # group_data = r.get('group_upload')
        # for g in group_data:
        #     if g['id'] in group_id:
        #         g['is_uploading'] = False
        r.set('group_upload', group_upload_data)

    except Exception as e:
        logging.exception('check_group' + str(e))

        for g in group_upload_data:
            if current_time >= g['upload_time']:
                g['is_uploading'] = False
        r.set('group_upload', group_upload_data)

    finally:
        session.close()
        upload_time2 = time.time()
        print('上传时间', upload_time2 - upload_time1)


@app.task(bind=True, default_retry_delay=1, max_retries=3)
def check_variable_get_time(self):
    """
    检查变量采集时间，采集满足条件的变量值

    :return: 
    """

    time1 = time.time()
    logging.debug('检查变量采集时间')

    current_time = int(time.time())

    # session = Session()
    try:
        plcs = r.get('plc')
        # print(plc_client)

        group_read_data = r.get('group_read')

        # print(plcs)
        for plc in plcs:
            # todo 循环内部 使用并发

            group_id = []
            for v in group_read_data:
                if v['plc_id'] == plc['id'] and current_time >= v['read_time']:
                    group_id.append(v['id'])
                    v['read_time'] = current_time + v['read_cycle']
            r.set('group_read', group_read_data)

            group_data = r.get('variable')
            variables = [variable
                         for group in group_data if group['group_id'] in group_id
                         for variable in group['variables']
                         ]

            # print(variables)
            # print('采集数量', len(variables))

            # client = plc_connect(plc)
            with plc_client(plc['ip'], plc['rack'], plc['slot']) as client:
                if client.get_connected():
                    plc['time'] = current_time

                if variables:

                    # readsuan(variables)
                    # variables = variables[0:2]
                    # print('variables', len(variables))

                    while len(variables) > 0:
                        variable_group = variables[:18]
                        variables = variables[18:]

                        # print(len(variables))
                        # print(plc)
                        read_multi(
                            plc=plc,
                            variables=variable_group,
                            current_time=current_time,
                            client=client
                        )

                        # client.disconnect()
                        # client.destroy()

        time2 = time.time()
        # print('采集时间' + str(time2 - time1))
        r.set('plc', plcs)

    except Exception as e:
        logging.exception('check_var' + str(e))
        session.rollback()
    finally:
        session.close()


@app.task(bind=True, default_retry_delay=1, max_retries=3)
def read_multi(self, plc, variables, current_time, client=None):
    # time1 = time.time()
    # print('采集')
    # session = Session()
    try:
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
            pBuffer = ctypes.cast(
                ctypes.pointer(buffer),
                ctypes.POINTER(ctypes.c_uint8)
            )
            di.pData = pBuffer

        if not client.get_connected():

            try:
                # client = snap7.client.Client()
                client.connect(
                    address=plc['ip'],
                    rack=plc['rack'],
                    slot=plc['slot'],
                )
            except Snap7Exception as e:
                logging.warning('PLC连接失败 ip：{} rack：{} slot:{}'.format(plc['ip'], plc['rack'], plc['slot']) + str(e))
                logging.info('重试连接plc')
                raise
                # raise self.retry(e)

        # time1 = time.time()
        result, data_items = client.read_multi_vars(data_items)
        # time2 = time.time()
        # print('读取时间', time2 - time1)

        for num in range(0, var_num):
            di = data_items[num]

            try:
                raw_value = read_value(
                    variables[num]['data_type'],
                    di.pData,
                    bool_index=bool_indexes[num]
                )
                # print(raw_value)
            except Snap7Exception as e:
                logging.error('plc读取数据错误' + str(e))
                id_num = r.get('id_num')
                alarm = read_err(
                    id_num=id_num,
                    plc_id=plc['id'],
                    plc_name=plc['name'],
                    area=variables[num]['area'],
                    db_num=variables[num]['db_num'],
                    address=variables[num]['address'],
                    data_type=variables[num]['data_type']
                )
                session.add(alarm)
                session.commit()
                raise
                # raise self.retry(e)
            else:
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
                    raw_value += + offset

                # 限制小数位数
                value = round(raw_value, 2)
                # print(str(variables[num]['id']) + '--' + str(value))

                value_model = {
                    'var_id': variables[num]['id'],
                    'time': current_time,
                    'value': value
                }
                # print(value_model)
                value_list.append(value_model)
        # print('采集数据', len(value_list), value_list)
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

    except (Exception, SoftTimeLimitExceeded) as e:
        logging.exception('read_multi' + str(e))
        session.rollback()
    finally:
        session.close()
        pass

        # time2 = time.time()

        # print('单次采集时间', time2 - time1)


@app.task(bind=True, default_retry_delay=60, max_retries=3)
def ntpdate(self):
    # 使用supervisor启动时用户为root 不需要sudo输入密码 不安全
    try:
        pw = 'touhou'

        cmd2 = 'echo {} | sudo -S ntpdate {}'.format(pw, NTP_SERVER)
        ntp = subprocess.Popen(
            cmd2,
            shell=True,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        status = ntp.wait()
        stdout, stderr = ntp.communicate()

        if not status:  # 判断进程执行状态
            note = '完成校时 :{}'.format(stdout.decode('utf-8'))
            logging.info(note)
        else:
            note = '校时失败 :{}'.format(stderr.decode('utf-8'))
            logging.error(note)
            id_num = r.get('id_num')
            alarm = ntpdate_err(
                id_num=id_num,
                note=note
            )
            session.add(alarm)
            session.commit()
    except Exception as e:
        logging.exception('ntpdate' + str(e))
        session.rollback()
    finally:
        session.close()


@app.task(bind=True)
def db_clean(self):
    # 删除一天前的采集数据
    current_time = int(time.time())
    try:
        old_value_model = session.query(Value).filter(Value.time < current_time - 60 * 60 * 24).delete(synchronize_session=False)
        session.commit()
    finally:
        session.close()


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

    post_data = json.dumps(post_data)
    # session = Session()
    print(post_data)
    try:
        rp = req_s.post(url, data=post_data, timeout=(CONNECT_TIMEOUT, REQUEST_TIMEOUT))
    except ConnectionError as e:
        logging.warning('确认请求发送失败: ' + str(e))
        alarm = connect_server_err(id_num, str(url))
        try:
            session.add(alarm)
            session.commit()
        except Exception as e:
            logging.exception('server_confirm' + str(e))
            session.rollback()
        finally:
            session.close()
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
            logging.error('plc_read', str(e))
            alarm = read_err(
                id_num=id_num,
                plc_id=plc_model.id,
                plc_name=plc_model.plc_name,
                area=area,
                db_num=db,
                address=address,
                data_type=data_type
            )
            # session = Session()
            try:
                session.add(alarm)
                session.commit()
            except Exception as e:
                logging.warning('plc_write' + str(e))
                session.rollback()
            finally:
                session.close()

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


@app.task(bind=True, default_retry_delay=3, max_retries=3)
def check_alarm(self):
    # r.set('alarm_info', None)
    logging.debug('check alarm')
    # print('检查报警')
    # redis_alarm_variables(r)

    is_no_alarm = r.get('is_no_alarm')
    if is_no_alarm:
        return
    alarm_variables = r.get('alarm_variables')
    # print('报警变量', alarm_variables)

    if not alarm_variables:
        redis_alarm_variables(r)
        return

    # 循环报警变量，查看最近采集的数值是否满足报警条件
    current_time = int(time.time())
    alarm_data = list()

    # session = Session()
    try:

        for alarm in alarm_variables:
            # 获取需要判断的采集数据
            if alarm['delay']:
                values = session.query(Value).filter_by(var_id=alarm['var_id']). \
                    filter(Value.time > current_time - alarm['delay'] - 1).all()
            else:
                values = session.query(Value).filter_by(var_id=alarm['var_id']). \
                    order_by(Value.time.desc()).limit(1).all()

            is_alarm = False
            if alarm['type'] == 1:
                for v in values:
                    if bool(v.value) == bool(alarm['limit']):
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

                elif alarm['symbol'] == 5:
                    for v in values:
                        if v.value == alarm['limit']:
                            is_alarm = True
                        else:
                            is_alarm = False
                            break
                else:
                    is_alarm = False

            else:
                is_alarm = False

            if is_alarm and not alarm['is_alarming']:
                alarm_data.append({
                    'i': alarm['var_id'],
                    'a': is_alarm
                })
                alarm['is_alarming'] = True
            elif not is_alarm and alarm['is_alarming']:
                alarm_data.append({
                    'i': alarm['var_id'],
                    'a': is_alarm
                })
                alarm['is_alarming'] = False

        r.set('alarm_variables', alarm_variables)

        if alarm_data:
            alarm_info = {'time': current_time, 'data': alarm_data}
            old_alarm = r.get('alarm_info')
            # print(old_alarm)
            if old_alarm:
                old_alarm.append(alarm_info)
                r.set('alarm_info', old_alarm)
            else:
                r.set('alarm_info', [alarm_info])

                # print(alarm_info)
        # print(alarm_variables)
    except Exception as e:
        logging.exception('check_alarm' + str(e))
        session.rollback()
    finally:
        session.close()

    return


def plc_connect(plc):
    client = Client()
    try:
        client.connect(
            address=plc['ip'],
            rack=plc['rack'],
            slot=plc['slot'],
        )
    except Snap7Exception as e:
        logging.warning('PLC连接失败 ip：{} rack：{} slot:{}'.format(plc['ip'], plc['rack'], plc['slot']) + str(e))
        id_num = r.get('id_num')
        plc_alarm = connect_plc_err(
            id_num,
            plc_id=plc['id'],
        )
        # session = Session()
        try:
            session.add(plc_alarm)
            session.commit()
        except Exception as e:
            logging.exception('plc_connect' + str(e))
            session.rollback()
        finally:
            session.close()

    return client
