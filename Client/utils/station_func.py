import logging
import time
import zlib
import base64
import json
import subprocess
from functools import wraps

import requests
from eventlet import Timeout

from models import Base, eng, Session, YjPLCInfo
from param import ID_NUM, START_TIMEDELTA, FILE_URL
from utils.redis_middle_class import r
from utils.plc_connect import plc_client
from utils.station_data import (redis_variable_info, redis_group_read_info, redis_group_upload_info,
                                redis_alarm_variables, plc_info)
from utils.mysql_middle import ConnMySQL


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
    r.conn.delete('group_upload')
    r.conn.delete('group_read')
    r.conn.delete('variable')
    r.conn.delete('alarm_info')
    r.conn.delete('check_time')
    r.conn.delete('plc')
    r.conn.delete('con_time')
    r.conn.delete('value')

    session = Session()
    try:
        # 设定服务开始运行时间
        current_time = int(time.time())
        start_time = current_time + START_TIMEDELTA

        # 设定报警信息
        redis_alarm_variables(r)
        # print(r.get('alarm_variables'))

        # 获取该终端所有PLC信息
        plc_models = session.query(YjPLCInfo).all()

        # 缓存PLC信息
        plc_data = plc_info(r, plc_models)
        logging.info('PLC配置信息： ' + str(plc_data))
        for plc in plc_models:

            # 获得该PLC的信息
            plc_id = plc.id
            ip = plc.ip
            rack = plc.rack
            slot = plc.slot

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

            with plc_client(ip, rack, slot, plc_id) as client:
                if not client.get_connected():
                    logging.error('PLC无法连接，请查看PLC状态')

            # 变量写入
            # 获取该变量组下所有变量信息
            # variables = g.variables

            # if variables:
            #     for v in variables:
            #         plc_write(v, plc_cli, plc)
    finally:
        session.close()


def encryption_client(dict_data):
    """
    压缩
    :param dict_data:
    :return:
    """

    str_data = json.dumps(dict_data).encode('utf-8')
    zlib_data = zlib.compress(str_data, level=9)

    return zlib_data


def decryption_client(base64_data):
    """
    解压
    :param base64_data:
    :return:
    """

    zlib_data = base64.b64decode(base64_data)
    str_data = zlib.decompress(zlib_data)
    dict_data = json.loads(str_data)

    return dict_data


def get_data_from_query(models):
    # 输入session.query()查询到的模型实例列表,读取每个实例每个值,放入列表返回
    data_list = []
    for model in models:
        model_column = {}
        for c in model.__table__.columns:
            model_column[c.name] = getattr(model, c.name, None)
        data_list.append(model_column)
    return data_list


def get_data_from_model(model):
    # 读取一个模型实例中的每一项与值，放入字典
    model_column = {}
    for c in model.__table__.columns:
        model_column[c.name] = getattr(model, c.name, None)
    return model_column


def remote_command(code):
    # 重启系统
    if code == 1:
        subprocess.call(['init', '6'])

    # 重启程序
    elif code == 2:
        subprocess.call(['supervisorctl', 'restart', 'pyplc'])

    # 上传日志
    elif code == 3:
        data = {
            'note': 'note'
        }
        data = encryption_client(data)
        note_file = {
            'note': open('/home/pi/pythonPLC/Client/pyplc.log', 'rb')
        }
        requests.post(FILE_URL, data, files=note_file)

    # 同步代码
    elif code == 4:
        subprocess.call('(cd /home/pi/pythonPLC/; git reset --hard; git pull)', shell=True)

    # 清理数据
    elif code == 5:
        with ConnMySQL as db:
            cur = db.cursor()
            try:
                cur.execute('SET foreign_key_checks = 0')
                cur.execute('truncate table `values`')
                cur.execute('SET foreign_key_checks = 1')
            finally:
                cur.close()


def timeout(second):
    # 封装evnetlet的Timeout，以装饰器形式实现任务时间控制
    def decorator(func):
        @wraps(func)
        def new_func(*args, **kwargs):
            try:
                with Timeout(second):
                    return func(*args, **kwargs)
            except Timeout as e:
                print('too long')

        return new_func

    return decorator
