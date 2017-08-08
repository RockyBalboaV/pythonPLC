# coding=utf-8

import os
import requests
from requests.exceptions import ConnectionError
import json
import struct
import time
import multiprocessing as mp
import math

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

from models import (eng, Base, Session, YjStationInfo, YjPLCInfo, YjGroupInfo, YjVariableInfo, TransferLog, \
                    Value, serialize)
from celeryconfig import Config
from data_collection import variable_size, variable_area, read_value, write_value, PythonPLC

app = Celery()
app.config_from_object(Config)

here = os.path.abspath(os.path.dirname(__name__))
cf = ConfigParser.ConfigParser()
cf.read_file(open(os.path.join(here, 'config.ini'), encoding='utf-8'))


def database_reset():
    Base.metadata.drop_all(bind=eng)
    Base.metadata.create_all(bind=eng)


def get_station_info():
    session = Session()
    id_num = cf.get('client', 'id_num')
    try:
        station_model = session.query(YjStationInfo).filter_by(id_num=id_num).first()
        version = station_model.version
    except:
        version = cf.get('client', 'version')

    return dict(id_num=id_num, version=version)


# 设置通用变量
# print('abcde')
station_info = get_station_info()
# print(os.environ.get('url'))
BEAT_URL = cf.get(os.environ.get('url'), 'beat_url')
CONFIG_URL = cf.get(os.environ.get('url'), 'config_url')
UPLOAD_URL = cf.get(os.environ.get('url'), 'upload_url')
CONNECT_TIMEOUT = float(cf.get('client', 'connect_timeout'))
REQUEST_TIMEOUT = float(cf.get('client', 'request_timeout'))
MAX_RETRIES = int(cf.get('client', 'max_retries'))
plc_client = list()


def first_running():
    Base.metadata.create_all(bind=eng)
    # print('bbbb')
    get_config()


def plc_connection(plcs):
    plc_client = list()
    for plc in plcs:
        client = snap7.client.Client()
        client.connect(plc.ip, plc.rack, plc.slot)
        if client.get_connected():
            plc_client.append((client, plc.ip, plc.rack, plc.slot))
    return plc_client


def before_running():
    session = Session()
    # print 'running setup'
    # 设定服务开始运行时间
    current_time = int(time.time())
    start_time = current_time + int(cf.get('client', 'START_TIMEDELTA'))

    # 获取站信息
    global station_info
    station_info = get_station_info()

    plcs = session.query(YjPLCInfo)
    global plc_client
    plc_client = plc_connection(plcs)

    for plc in plcs:
        ip = plc.ip
        rack = plc.rack
        slot = plc.slot

        with PythonPLC(ip, rack, slot) as db:

            groups = plc.groups

            # 设定变量组初始上传时间
            for g in groups:
                g.upload_time = start_time + g.upload_cycle

                variables = g.variables

                for v in variables:
                    if v.rw_type == 2 or v.rw_type == 3 and v.write_value is not None:
                        variable_db = v.db_num
                        area = v.area
                        address = v.address
                        byte_value = write_value(v, v.write_value)

                        db.write_area(area=area, dbnumber=variable_db, start=address, data=byte_value)

                    if v.rw_type == 1 or v.rw_type == 3:
                        v.acquisition_time = start_time + v.acquisition_cycle
                        v.ip = plc.ip

    session.commit()


@worker_process_init.connect
def fix_mutilprocessing(**kwargs):
    try:
        mp.current_process()._authkey
    except AttributeError:
        mp.current_process()._authkey = mp.current_process().authkey


@app.task(bind=True, rate_limit='5/s', max_retries=MAX_RETRIES)
def beats(self):
    print('beats')
    session = Session()
    current_time = int(time.time())
    global station_info
    station_info = get_station_info()
    data = station_info
    # data = encryption(data)
    # todo 报警变量加到data里

    try:
        rv = requests.post(BEAT_URL, json=data, timeout=(CONNECT_TIMEOUT, REQUEST_TIMEOUT))
    except (ConnectionError, MaxRetriesExceededError) as e:
        status = 'error'
        note = '无法连接服务器，检查网络状态。'
        log = TransferLog(
            trans_type='beats',
            time=current_time,
            status=status,
            note=note
        )
        session.add(log)
        session.commit()
        try:
            raise self.retry(exc=e)
        except ConnectionError:
            pass
    else:
        # data = decryption(rv)
        data = rv.json()
        # print(data)

        if data["modification"] == 1:
            # print('ccccc')
            # get_config.delay()
            get_config()
            # print 'get_config'
            note = '完成一次心跳连接，时间:{},发现配置信息有更新.'.format(datetime.datetime.fromtimestamp(current_time))
        else:
            note = '完成一次心跳连接，时间:{}.'.format(datetime.datetime.fromtimestamp(current_time))
        status = 'OK'

    log = TransferLog(
        trans_type='beats',
        time=current_time,
        status=status,
        note=note
    )
    session.add(log)
    session.commit()

    if not plc_client:
        plcs = session.query(YjPLCInfo)
        global plc_client
        plc_client = plc_connection(plcs)


@app.task(bind=True, max_retries=MAX_RETRIES)
def get_config(self):
    session = Session()
    current_time = int(time.time())
    # data = encryption(data)
    data = station_info
    try:
        response = requests.post(CONFIG_URL, json=data, timeout=(CONNECT_TIMEOUT, REQUEST_TIMEOUT))
    except ConnectionError as e:
        status = 'error'
        note = '无法连接服务器，检查网络状态。'
        log = TransferLog(trans_type='config', time=current_time, status=status, note=note)
        session.add(log)
        session.commit()
        try:
            raise self.retry(exc=e)
        except ConnectionError:
            pass
        return 1

    if response.status_code == 404:
        status = 'error'
        note = '获取配置信息失败'
    elif response.status_code == 200:
        data = response.json()['data']
        print(data)
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
        session.commit()

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
        session.commit()

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
        session.commit()

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
        session.commit()

        status = 'OK'
        note = '成功将配置从version: {} 升级到 version: {}.'.format(station_info['version'], version)
    else:
        status = 'error'
        note = '获取配置时发生未知问题，检查服务器代码。 {}'.format(response.status_code)
    log = TransferLog(trans_type='config', time=current_time, status=status, note=note)
    session.add(log)
    session.commit()

    before_running()


def upload_data(group_model, current_time, session):
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

    log = TransferLog(
        trans_type='group_upload',
        time=current_time,
        status='OK',
        note='group_id: {} group_name:{} 将要上传.'.format(group_id, group_name)
    )
    # 记录本次传输
    session.add(log)

    return variable_list


@app.task(bind=True, max_retries=MAX_RETRIES, default_retry_delay=30)
def upload(self, variable_list, group_model, current_time, session):
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
    try:
        response = requests.post(UPLOAD_URL, json=data, timeout=(CONNECT_TIMEOUT, REQUEST_TIMEOUT))
    except ConnectionError as e:
        status = 'error'
        note = '无法连接服务器，检查网络状态。'
        log = TransferLog(
            trans_type='upload_call_back',
            time=current_time,
            status=status,
            note=note
        )
        session.add(log)
        # session.commit()
        try:
            raise self.retry(exc=e)
        except ConnectionError:
            pass
        return 1

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
    # session.commit()


@app.task(bind=True, rate_limit='1/s', time_limit=2, max_retries=MAX_RETRIES, default_retry_delay=3)
def check_group_upload_time(self):
    try:

        session = Session()
        current_time = int(time.time())
        print('check_group')
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
            value_list = upload_data(group_model, current_time, session)
            upload(value_list, group_model, current_time, session)

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
        self.retry(exc=exc)
        # session.commit()


@app.task(bind=True, rate_limit='1/s', soft_time_limit=2, max_retries=MAX_RETRIES, default_retry_delay=3)
def check_variable_get_time(self):
    try:
        session = Session()
        current_time = int(time.time())
        print('check_variable')
        # try:
        variables = session.query(YjVariableInfo).filter(current_time >= YjVariableInfo.acquisition_time).all()

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

        for var in variables:
            # print 'variable'
            # print 'get value'
            get_value(var, session)
            # get_value.apply_async((var, session))
            # poll.apply_async(get_value, (v,))

        session.commit()
        # except:
        #     session.rollback()
    except SoftTimeLimitExceeded as exc:
        session.rollback()
        self.retry(exc=exc)


@app.task
def get_value(variable_model, session):
    current_time = int(time.time())
    variable_model.acquisition_time = current_time + variable_model.acquisition_cycle
    # 获得变量信息
    # 变量所属plc的信息
    ip = variable_model.ip
    for plc in plc_client:
        if plc[1] == ip:

            if not plc[0].get_connected():
                plc[0].connect(plc.ip, plc.rack, plc.slot)

            area = variable_area(variable_model)
            variable_db = variable_model.db_num
            size = variable_size(variable_model)
            address = int(math.modf(variable_model.address)[1])
            bool_index = int(math.modf(variable_model.address)[0] * 10)

            result = plc[0].read_area(area=area, dbnumber=variable_db, start=address, size=size)
            value = read_value(variable_model, result, bool_index)
            # print(value)

            value = Value(variable_id=variable_model.id, time=current_time, value=value)
            session.add(value)

        break
    return
