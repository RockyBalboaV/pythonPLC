# coding=utf-8
from models import *
import hmac, requests, json, chardet, base64, simplejson, cProfile, pstats, PIL, zlib, hashlib
import time
from celery import Celery
from sqlalchemy.orm.exc import UnmappedInstanceError

app = Celery()
app.config_from_object('celeryconfig')


def encryption(data):
    """
    :param data: dict
    :return: dict
    """
    h = hmac.new(b'poree')
    data = unicode(data)
    # data = base64.b64encode(data)
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
    data = rj['data']
    di = rj['digest']
    data = base64.b64decode(data)
    data = zlib.decompress(data)
    h = hmac.new(b'poree')
    h.update(data)
    test = h.hexdigest()
    if di == test:
        # data = base64.b64decode(data)
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
    model_column ={}
    for c in model.__table__.columns:
        model_column[c.name] = str(getattr(model, c.name, None))
    return model_column


def __init__():
    # Base.metadata.drop_all(bind=eng)
    GroupUploadTime.__table__.drop(eng, checkfirst=True)
    Base.metadata.create_all(bind=eng)
    __test__get_config()
    current_time = datetime.datetime.now()
    groups = session.query(YjGroupInfo).filter().all()
    for g in groups:
        g_upload_time = current_time+datetime.timedelta(seconds=g.uploadcycle)
        g_upload = GroupUploadTime(group_name=g.groupname, next_time=g_upload_time)
        session.add(g_upload)
    session.commit()


@app.task
def beats():
    idnum = 1
    version =1
    #idnum = session.query(YjStationInfo).first().idnum
    #version = session.query(YjStationInfo).first().version

    data = {"idnum": idnum, "version": version}
    #data = encryption(data)
    rv = requests.post('http://127.0.0.1:11000/beats', json=data)
    data = rv.json()
    #data = decryption(rv)
    if data["modification"] == 1:
        __test__get_config()


def __test__get_config():
    data = {"idnum": "1"}
    #data = session.query(YjStationInfo).first().idnum
    #data = encryption(data)
    rv = requests.post('http://127.0.0.1:11000/config', json=data)
    data = rv.json()
    try:
        session.delete(session.query(YjStationInfo).first())
    except UnmappedInstanceError:
        pass
    else:
        session.commit()

    station = YjStationInfo(id=data["YjStationInfo"]["id"], name=data["YjStationInfo"]["name"],
                            mac=data["YjStationInfo"]["mac"], ip=data["YjStationInfo"]["ip"],
                            note=data["YjStationInfo"]["note"], idnum=data["YjStationInfo"]["idnum"],
                            plcnum=data["YjStationInfo"]["plcnum"], tenid=data["YjStationInfo"]["tenid"],
                            itemid=data["YjStationInfo"]["itemid"], version=data["YjStationInfo"]["version"],
                            con_date=data["YjStationInfo"]["con_date"], modification=u'0')
    session.add(station)
    session.commit()

    for plc in data["YjPLCInfo"]:
        p = YjPLCInfo(id=plc["id"], name=plc["name"], station_id=plc["station_id"], note=plc["note"],
                      ip=plc["ip"],mpi=plc["mpi"], type=plc["type"], plctype=plc["plctype"],
                      tenid=plc["tenid"], itemid=plc["itemid"])
        session.add(p)
        session.commit()

    for group in data["YjGroupInfo"]:
        g = YjGroupInfo(id=group["id"], groupname=group["groupname"], plc_id=group["plc_id"], note=group["note"],
                        uploadcycle=group["uploadcycle"], tenid=group["tenid"], itemid=group["itemid"])
        session.add(g)
        session.commit()

    for variable in data["YjVariableInfo"]:
        v = YjVariableInfo(id=variable["id"], tagname=variable["tagname"], plc_id=variable["plc_id"], group_id=variable["group_id"],
                           address=variable["address"], datatype=variable["datatype"], rwtype=variable["rwtype"],
                           upload=variable["upload"], acquisitioncycle=variable["acquisitioncycle"],
                           serverrecordcycle=variable["serverrecordcycle"], writevalue=variable["writevalue"],
                           note=variable["note"], tenid=variable["tenid"], itemid=variable["itemid"])
        session.add(v)
        session.commit()


def upload(group_name):
    # 读取站信息
    # idnum = session.query(YjStationInfo).filter().first().idnum
    idnum = 1
    # version = session.query(YjStationInfo).version
    # 记录本次上传时间
    upload_time = datetime.datetime.now()

    group = session.query(YjGroupInfo).filter(YjGroupInfo.groupname == group_name).first()
    group_log = session.query(TransferLog).filter(TransferLog.type == 'group').filter(
        TransferLog.note == group_name).order_by(TransferLog.date.desc()).first()


    # 读取需要上传的值,所有时间大于上次上传的值
    # values = session.query(Value).filter(Value.get_time > last_log.date).all()
    # 获取该组包括的所有变量
    # 记录中如果有原配置中有的组名，更改配置后会导致取到空值
    try:
        variables = session.query(YjGroupInfo).filter(YjGroupInfo.groupname == group_name).first().variables
    except AttributeError as e:
        session.delete(session.query(GroupUploadTime).filter(GroupUploadTime.group_name == group_name).first())
        session.commit()
        return 0
    print variables

    # 获取上次传输时间,没有上次时间就往前推一个上传周期
    last_variable_upload_time = group_log.date
    if not last_variable_upload_time:
        timedelta = datetime.timedelta(seconds=group.uploadcycle)
        last_variable_upload_time = upload_time - timedelta

    variable_list = []
    for variable in variables:
        # 判断该变量是否需要上传
        if variable.upload:
            break

        all_values = session.query(Value).filter(Value.variable_name == variable.tagname).\
            filter(Value.get_time > last_variable_upload_time)

        # 循环从上次读取时间开始计算，每个一个记录周期提取一个数值
        while last_variable_upload_time < upload_time:
            upload_value = all_values.filter(Value.get_time > last_variable_upload_time).filter(last_variable_upload_time + datetime.timedelta(seconds=variable.serverrecordcycle) > Value.get_time).first()
            # 当上传时间小于采集时间时，会出现取值时间节点后无采集数据，得到None，使得后续语句报错。
            try:
                value_dict = get_data_from_model(upload_value)
            except AttributeError:
                break

            variable_list.append(value_dict)
            timedelta = datetime.timedelta(seconds=variable.serverrecordcycle)
            last_variable_upload_time += timedelta

    # 记录本次传输
    group_next = session.query(GroupUploadTime).filter(GroupUploadTime.group_name == group_name).first()
    group_next.next_time = upload_time + datetime.timedelta(seconds=group.uploadcycle)
    session.merge(group_next)
    #session.add(session.query(GroupUploadTime).filter(GroupUploadTime.group_name == group_name).
    #            update({GroupUploadTime.next_time: upload_time + datetime.timedelta(seconds=group.uploadcycle)}))
    session.add(TransferLog(type='group', date=upload_time, status='OK', note=group_name))
    session.commit()

    data = {"GroupName": group_name, "Value": variable_list}
    print(data)
    # data = encryption(data)
    rv = requests.post("http://127.0.0.1:11000/upload", json=data)
    data = rv.json()
    # data = decryption(data)
    status = data["status"]
    log = TransferLog(type='upload', date=upload_time, status=status)
    session.add(log)
    session.commit()


@app.task
def fake_data():

        value = Value(variable_name='DB1', value=1, get_time=datetime.datetime.now(), up_time=1)
        session.add(value)

        #value = Value('DB2', 2, datetime.datetime.now(), 10)
        #session.add(value)

        session.commit()


@app.task
def check_group_upload_time():
    current_time = datetime.datetime.now()
    groups = session.query(GroupUploadTime).order_by(GroupUploadTime.next_time).all()
    for g in groups:
        if current_time > g.next_time:
            upload(g.group_name)
        if current_time < g.next_time:
            break


if __name__ == '__main__':
    #__init__()
    #__test__get_config()
    #check_group_upload_time()
    upload('g1')
    #session.delete(session.query(YjStationInfo).first())
    #session.commit()
    #db_init()
    #fake_data()

    #while True:

    #Base.metadata.drop_all(bind=eng)

    #Base.metadata.create_all(bind=eng)




    #Base.metadata.create_all(bind=eng)
    #__test__transfer()
    #__test__unicode()
        #beats()
    #__test__urllib()
    #__test__get_config()
        # time.sleep(5)
    #__test__upload('g1')
    #cProfile.run('__test__transfer()')
    #prof = cProfile.Profile()
    #prof.enable()
    #__test__transfer()
    #prof.create_stats()
    #prof.print_stats()
    #p = pstats.Stats(prof)
    #p.print_callers()