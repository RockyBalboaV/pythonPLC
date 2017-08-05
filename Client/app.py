# coding=utf-8

import os
import hmac
import requests
from requests.exceptions import ConnectionError
from requests.packages.urllib3.connection import NewConnectionError
import json
import base64
import zlib
import struct
import time
import multiprocessing as mp
import ConfigParser
import datetime

from celery import Celery
from celery.signals import worker_process_init
from celery.exceptions import MaxRetriesExceededError
import billiard
from sqlalchemy.orm.exc import UnmappedInstanceError, UnmappedClassError
from sqlalchemy.exc import ProgrammingError
from snap7.snap7exceptions import Snap7Exception

from models import (eng, Base, Session, YjStationInfo, YjPLCInfo, YjGroupInfo, YjVariableInfo, TransferLog, \
                    Value, serialize)
from celeryconfig import Config
from data_collection import variable_size, variable_area, PythonPLC

app = Celery()
app.config_from_object(Config)

cf = ConfigParser.ConfigParser()
cf.readfp(open('config.ini'))


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


def first_running():
    Base.metadata.create_all(bind=eng)
    # print('bbbb')
    get_config()


def before_running():
    session = Session()
    # print 'running setup'
    # 设定服务开始运行时间
    current_time = int(time.time())
    start_time = current_time + int(cf.get('client', 'START_TIMEDELTA'))

    # 获取站信息
    global station_info
    station_info = get_station_info()

    # 设定变量组初始上传时间
    groups = session.query(YjGroupInfo)
    for g in groups:
        g.upload_time = start_time + g.upload_cycle
        # g.uploading = False

    # 设定变量,需要读取的值设定初始采集时间，需要写入的值立即写入PLC
    variables = session.query(YjVariableInfo).all()
    for v in variables:
        if v.rw_type == 2 or v.rw_type == 3 and v.write_value:
            ip = v.group.plc.ip
            rack = v.group.plc.rack
            slot = v.group.plc.slot
            variable_db = v.db_num
            type_code, size = variable_size(v)
            address = v.address
            area = v.area

            write_value = struct.pack('!{}'.format(type_code), v.write_value)

            with PythonPLC(ip, rack, slot) as db:
                db.write_area(area=area, dbnumber=variable_db, start=address, data=write_value)

        if v.rw_type == 1 or v.rw_type == 3:
            v.acquisition_time = start_time + v.acquisition_cycle

    session.commit()


@worker_process_init.connect
def fix_mutilprocessing(**kwargs):
    try:
        mp.current_process()._authkey
    except AttributeError:
        mp.current_process()._authkey = mp.current_process().authkey


@app.task(bind=True, rate_limit='5/s', max_retries=MAX_RETRIES)
def beats(self):
    session = Session()
    current_time = int(time.time())

    data = station_info
    # data = encryption(data)
    # todo 报警变量加到data里

    try:
        rv = requests.post(BEAT_URL, json=data, timeout=(CONNECT_TIMEOUT, REQUEST_TIMEOUT))
    except (ConnectionError, NewConnectionError, MaxRetriesExceededError) as e:
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
        print data
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

    # 准备本次上传的数据
    variables = group_model.variables
    variable_list = []
    print(variables)

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
    # 包装数据
    data = {
        "id_num": station_info["id_num"],
        "version": station_info["version"],
        "group_id": group_model.id,
        "value": variable_list
    }
    print data
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
        note = 'group_id: {} group_name:{} 成功上传.'.format(group_model.id, group_model.group_name)

    # 版本错误
    elif response.status_code == 403:
        note = 'group_id: {} group_name:{} 上传的数据不是在最新版本配置下采集的.'.format(group_model.id, group_model.group_name)

    # 未知错误
    else:
        note = 'group_id: {} group_name:{} 无法识别服务端反馈。'.format(group_model.id, group_model.group_name)
    log = TransferLog(
        trans_type='upload_call_back',
        time=current_time,
        status=data["status"],
        note=note
    )
    session.add(log)
    # session.commit()


@app.task(rate_limit='1/s')
def check_group_upload_time():
    session = Session()
    current_time = int(time.time())
    print 'check_group'
    # try:
    # groups = session.query(YjGroupInfo).filter(current_time >= YjGroupInfo.upload_time).all()
    group_models = session.query(YjGroupInfo).filter(current_time >= YjGroupInfo.upload_time).filter(
        YjGroupInfo.uploading is not True).all()
    # print(groups)
    # except:
    #     return 'skip'

    # poll = multiprocessing.Pool(4)

    # 修改下次组传输时间
    for group_model in group_models:
        # print 'b'
        group_model.upload_time = current_time + group_model.upload_cycle
        session.merge(group_model)
    # try:
    session.commit()
    # except:
    #     session.rollback()

    for group_model in group_models:
        # print 'a'
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

    # session.commit()


@app.task(rate_limit='1/s')
def check_variable_get_time():
    session = Session()
    current_time = int(time.time())
    print('check_variable')
    # try:
    variables = session.query(YjVariableInfo).filter(current_time >= YjVariableInfo.acquisition_time).all()
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
    for v in variables:
        # 保证一段时间内不会产生两个task采集同一个变量
        v.acquisition_time = current_time + v.acquisition_cycle
        session.merge(v)
    session.commit()
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


@app.task
def get_value(variable_model, session):
    current_time = int(time.time())

    # print(2)
    # session.commit()
    # print(3)

    # 获得变量信息
    # 变量所属plc的信息
    ip = variable_model.group.plc.ip
    rack = variable_model.group.plc.rack
    slot = variable_model.group.plc.slot

    # print(5)
    # 获取采集变量时需要的信息
    area = variable_area(variable_model)
    # print(6)
    variable_db = variable_model.db_num
    # print(7)
    type_code, size = variable_size(variable_model)
    # print(8)
    address = variable_model.address

    # print('cccc')
    # 采集数据
    # print ip, rack, slot, area, variable_db, address, size
    # print type(ip), type(rack), type(slot)
    # TODO 建立连接的开销很大，在代码启动时创建连接并保持，定时查询连接状态就好，这样不用重复建立连接
    try:
        with PythonPLC(ip, rack, slot) as db:
            result = db.read_area(area=area, dbnumber=variable_db, start=address, size=size)
    except Snap7Exception as e:
        print(e)
    else:
        value = struct.unpack('!{}'.format(type_code), result)[0]
        # print value

        # print('dddd')
        # 保存数据
        value = Value(variable_id=variable_model.id, time=current_time, value=value)
        session.add(value)

        # 采集完后整体保存
        # session.commit()
