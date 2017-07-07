# coding=utf-8

import hmac
import requests
from requests.exceptions import ConnectionError
import json
import base64
import zlib
import struct
import time
import multiprocessing as mp

import snap7
from celery import Celery, group
from sqlalchemy.orm.exc import UnmappedInstanceError

from models import *
from config import DevConfig

# from config import *

app = Celery()
# app.config_from_object('celeryconfig')
app.config_from_object(DevConfig)

global con
con = False


def encryption(data):
    """
    :param data: dict
    :return: dict
    """
    h = hmac.new(b'poree')
    data = unicode(data)
    h.update(data)
    data = zlib.compress(data)
    data = base64.b64encode(data)
    digest = h.hexdigest()
    data = {"data": data, "digest": digest}
    return data


def decryption(rj):
    """
    :param rj: json
    :return: dict
    """
    data = rj["data"]
    di = rj["digest"]
    data = base64.b64decode(data)
    data = zlib.decompress(data)
    h = hmac.new(b'poree')
    h.update(data)
    test = h.hexdigest()
    if di == test:
        data = json.loads(data.replace("'", '"'))
    else:
        data = {"status": "Error"}
    return data


def get_data_from_query(models):
    # 输入session.query()查询到的模型实例列表,读取每个实例每个值,放入列表返回
    data_list = []
    for model in models:
        model_column = {}
        for c in model.__table__.columns:
            model_column[c.name] = str(getattr(model, c.name, None))
        data_list.append(model_column)
    return data_list


def get_data_from_model(model):
    # 读取一个模型实例中的每一项与值，放入字典
    model_column = {}
    for c in model.__table__.columns:
        model_column[c.name] = str(getattr(model, c.name, None))
    return model_column


def get_station_info(station_id_num):
    try:
        station = session.query(YjStationInfo).filter(YjStationInfo.id_num == station_id_num).first()
        version = station.version
    except AttributeError:
        version = app.conf['VERSION']
    return {"station_id_num": station_id_num, "version": version}


def variable_size(variable):
    if variable.data_type == 'FLOAT':
        return 'f', 4
    elif variable.data_type == 'INT':
        return 'i', 4
    elif variable.data_type == 'DINT':
        return 'i', 4
    elif variable.data_type == 'WORD':
        return 'h', 2
    elif variable.data_type == 'BYTE':
        return 's', 1
    elif variable.data_type == 'BOOL':
        return '?', 1


def database_reset():
    Base.metadata.drop_all(bind=eng)
    Base.metadata.create_all(bind=eng)


def first_running():
    Base.metadata.create_all(bind=eng)
    get_config()

    before_running()


def before_running():
    # 设定服务开始运行时间
    current_time = int(time.time())
    start_time = current_time + app.conf['START_TIMEDELTA']

    # 设定变量组初始上传时间
    groups = session.query(YjGroupInfo).all()
    for g in groups:
        g.upload_time = start_time + g.upload_cycle
        g.uploading = False

    # 设定变量初始采集时间
    variables = session.query(YjVariableInfo).all()
    for v in variables:
        v.acquisition_time = start_time + v.acquisition_cycle

    session.commit()


@app.task
def beats():
    # 获取本机的信息
    station_info = get_station_info(app.conf['ID_NUM'])  # todo 只需一次
    data = station_info
    # data = encryption(data)

    current_time = int(time.time())

    try:
        rv = requests.post(app.conf['BEAT_URL'], json=data)
    except ConnectionError:
        status = 'error'
        note = '无法连接服务器，检查网络状态。'
    else:
        # data = decryption(rv)
        data = rv.json()

        if data["modification"] == 1:
            get_config()
            before_running()
            note = '完成一次心跳连接，时间:{},发现配置信息有更新.'.format(datetime.datetime.fromtimestamp(current_time))
        else:
            note = '完成一次心跳连接，时间:{}.'.format(datetime.datetime.fromtimestamp(current_time))
        status = 'OK'
    log = TransferLog(trans_type='beats', time=current_time, status=status, note=note)
    session.add(log)
    session.commit()


@app.task
def get_config():
    current_time = int(time.time())
    # 获取本机的信息
    station_info = get_station_info(app.conf['ID_NUM'])  # todo 只需一次
    # data = encryption(data)
    try:
        response = requests.post(app.conf['CONFIG_URL'], json=station_info)
    except ConnectionError:
        status = 'error'
        note = '无法连接服务器，检查网络状态。'
        log = TransferLog(trans_type='config', time=current_time, status=status, note=note)
        session.add(log)
        session.commit()
        return 1

    if response.status_code == 404:
        status = 'error'
        note = '获取配置信息失败'
    elif response.status_code == 200:
        data = response.json()['data']
        print data
        try:
            session.delete(session.query(YjStationInfo).first())
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

        station = YjStationInfo(id=data["YjStationInfo"]["id"],
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
            p = YjPLCInfo(id=plc["id"],
                          plc_name=plc["plc_name"],
                          station_id=plc["station_id"],
                          note=plc["note"],
                          ip=plc["ip"],
                          mpi=plc["mpi"],
                          type=plc["type"],
                          plc_type=plc["plc_type"],
                          ten_id=plc["ten_id"],
                          item_id=plc["item_id"]
                          )
            session.add(p)
        session.commit()

        for group in data["YjGroupInfo"]:
            g = YjGroupInfo(id=group["id"],
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
            v = YjVariableInfo(id=variable["id"],
                               variable_name=variable["variable_name"],
                               plc_id=variable["plc_id"],
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
                               item_id=variable["item_id"]
                               )
            session.add(v)
        session.commit()

        # update_log = ConfigUpdateLog(time=int(time.time()), version=version)
        # session.add(update_log)
        status = 'OK'
        note = '成功将配置从version: {} 升级到 version: {}.'.format(station_info['version'], version)
    else:
        status = 'error'
        note = '获取配置时发生未知问题，检查服务器代码。 {}'.format(response.status_code)
    log = TransferLog(trans_type='config', time=current_time, status=status, note=note)
    session.add(log)
    session.commit()

    return 1


@app.task
def upload(group_model):
    # group_model = session.query(YjGroupInfo).first()
    # 获取该组信息
    group_id = group_model.id
    group_name = group_model.group_name

    # 记录本次上传时间
    upload_time = int(time.time())

    group_log = session.query(TransferLog).filter(TransferLog.trans_type == 'upload').filter(
        TransferLog.note.like('% {} %'.format(group_id))).order_by(TransferLog.time.desc()).first()

    # 获取上次传输时间,没有上次时间就往前推一个上传周期
    if group_log:
        last_time = group_log.time
    else:
        timedelta = group_model.upload_cycle
        last_time = upload_time - timedelta

    # # 获取该组包括的所有变量
    # # 记录中如果有原配置中有的组名，更改配置后会导致取到空值
    # try:
    #     variables = session.query(YjGroupInfo).filter(YjGroupInfo.groupname == group_name).first().variables
    # except AttributeError as e:
    #     session.delete(session.query(GroupUploadTime).filter(GroupUploadTime.group_name == group_name).first())
    #     session.commit()
    #     return 0

    variables = group_model.variables

    # 准备本次上传的数据
    variable_list = []
    for variable in variables:
        # 判断该变量是否需要上传
        if variable.upload:
            # 读取需要上传的值,所有时间大于上次上传的值
            get_time = last_time
            # all_values = variable.values.filter(get_time <= Value.time < upload_time)
            all_values = session.query(Value).filter_by(variable_id=variable.id).filter(
                get_time <= Value.time).filter(Value.time < upload_time)

            # # test
            # for a in all_values:
            #     print a.id

            # 循环从上次读取时间开始计算，每个一个记录周期提取一个数值
            while get_time < upload_time:
                upload_value = all_values.filter(
                    get_time + variable.server_record_cycle > Value.time).filter(Value.time >= get_time).first()
                # 当上传时间小于采集时间时，会出现取值时间节点后无采集数据，得到None，使得后续语句报错。
                try:
                    value_dict = get_data_from_model(upload_value)
                    variable_list.append(value_dict)
                except AttributeError:
                    pass

                get_time += variable.server_record_cycle

    # 修改下次组传输时间
    group_model.upload_time = upload_time + group_model.upload_cycle
    group_model.uploading = False
    session.merge(group_model)

    # 记录本次传输
    session.add(TransferLog(trans_type='group_upload',
                            time=upload_time,
                            status='OK',
                            note='group_id: {} group_name:{} 将要上传.'.format(group_id, group_name)))
    session.commit()

    station = get_station_info(app.conf['ID_NUM'])  # todo 只需一次

    # 包装数据
    data = {"station_id_num": station["station_id_num"], "version": station["version"], "group_id": group_model.id,
            "value": variable_list}
    print data
    # data = encryption(data)
    try:
        response = requests.post(app.conf['UPLOAD_URL'], json=data)
    except ConnectionError:
        status = 'error'
        note = '无法连接服务器，检查网络状态。'
        log = TransferLog(trans_type='upload_call_back', time=upload_time, status=status, note=note)
        session.add(log)
        session.commit()
        return 0

    data = response.json()
    # data = decryption(data)

    # 日志记录
    # 正常传输
    if response.status_code == 200:
        note = 'group_id: {} group_name:{} 成功上传.'.format(group_id, group_name)

    # 版本错误
    elif response.status_code == 403:
        note = 'group_id: {} group_name:{} 上传的数据不是在最新版本配置下采集的.'.format(group_id, group_name)
        get_config()

    # 未知错误
    else:
        note = 'group_id: {} group_name:{} 无法识别服务端反馈。'.format(group_id, group_name)
    print data
    log = TransferLog(trans_type='upload_call_back',
                      time=upload_time,
                      status=data["status"],
                      note=note)
    session.add(log)
    session.commit()


# @app.task
# def fake_data():
#     # 产生一个假数据
#     value = Value(variable_id=1, value=1, time=int(time.time()))
#     session.add(value)
#     session.commit()


@app.task
def check_group_upload_time():
    current_time = int(time.time())
    print 'c'
    try:
        groups = session.query(YjGroupInfo).filter(current_time >= YjGroupInfo.upload_time).filter(
            YjGroupInfo.uploading is not True).all()
    except:
        return 'skip'
    # poll = multiprocessing.Pool(4)
    for g in groups:
        print 'b'
        g.uploading = True
    session.commit()

    for g in groups:
        print 'a'
        upload(g)
    # curr_proc = mp.current_process()
    # curr_proc.daemon = False
    # p = mp.Pool(mp.cpu_count())
    # curr_proc.daemon = True
    # for g in groups:
    #     print 'a'
    #     p.apply_async(upload, args=(g,))  # todo 多线程
    # p.close()
    # p.join()
    #
    # return 1
    # poll.apply_async(upload, (g,))


@app.task
def check_variable_get_time():
    current_time = int(time.time())
    try:
        variables = session.query(YjVariableInfo).filter(current_time >= YjVariableInfo.acquisition_time)
    except:
        return 'skip'

    # sig = group(get_value.s(v) for v in variables)
    # sig.delay()
    # poll = multiprocessing.Pool(4)
    for v in variables:
        # print 'variable'
        print 'get value'
        get_value(v)
        # poll.apply_async(get_value, (v,))


@app.task
def get_value(variable_model):
    variable_model.acquisition_time += variable_model.acquisition_cycle
    session.merge(variable_model)
    session.commit()
    # 获得变量信息
    # variable_model = session.query(YjVariableInfo).first()
    ip = variable_model.plc.ip
    rack = app.conf['rack']
    slot = app.conf['slot']
    tcp_port = app.conf['tcp_port']

    variable_db = variable_model.db_num
    type_code, size = variable_size(variable_model)
    address = int(variable_model.address)
    # 采集数据
    with PythonPLC(ip, rack, slot, tcp_port) as db:
        result = db.db_read(db_number=variable_db, start=address, size=size)
    value = struct.unpack('!{}'.format(type_code), result)[0]
    # print value

    # 保存数据
    value = Value(variable_id=variable_model.id, time=int(time.time()), value=value)
    session.add(value)
    session.commit()


class PythonPLC(object):
    def __init__(self, ip, rack, slot, tcp_port):
        self.ip = ip
        self.rack = rack
        self.slot = slot
        self.tcp_port = tcp_port

    def __enter__(self):
        self.client = snap7.client.Client()
        self.client.connect(self.ip, self.rack, self.slot, self.tcp_port)
        return self.client

    def __exit__(self, *args):
        self.client.disconnect()
        self.client.destroy()


if __name__ == '__main__':
    # database_reset()
    first_running()
    # print app.conf['BEAT_URL']
    # beats()
    # get_config()
    # get_value()
    # upload()
