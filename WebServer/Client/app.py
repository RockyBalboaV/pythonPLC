# coding=utf-8
from models import *
import hmac, requests, json, chardet, base64, simplejson, cProfile, pstats, PIL, zlib, hashlib
import urllib2, urllib
import time
import MySQLdb
from celery import Celery

app = Celery()
app.config_from_object('celeryconfig')


session = Session()


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


def get_data_form_query(models):
    # 输入session.query()查询到的模型实例列表,读取每个实例每个值,放入列表返回
    data_list = []
    for model in models:
            model_column = {}
            for c in model.__table__.columns:
                model_column[c.name] = str(getattr(model, c.name, None))
            data_list.append(model_column)
    return data_list


def db_init():
    Base.metadata.drop_all(bind=eng)
    Base.metadata.create_all(bind=eng)


@app.task
def __test__beats():
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
    print data["modification"]


def __test__get_config():
    data = {"idnum": "1"}
    #data = session.query(YjStationInfo).first().idnum
    #data = encryption(data)
    rv = requests.post('http://127.0.0.1:11000/config', json=data)
    data = rv.json()
    Base.metadata.drop_all(bind=eng)
    Base.metadata.create_all(bind=eng)
    #con = MySQLdb.connect('localhost', 'client', 'pyplc_client', 'pyplc_client')
    #with con as cur:
    #    cur.execute('drop table if exists yjstationinfo')
    #    cur.execute('drop table if exists yjplcinfo')
    #    cur.execute('drop table if exists yjgroupinfo')
    #    cur.execute('drop table if EXISTS yjvariableinfo')
    #session.query(YjVariableInfo)
    # print session.query(YjStationInfo).first()
    # session.delete()

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

    #data = decryption(rv)


def __test__upload():
    # 读取站信息
    # idnum = session.query(YjStationInfo).filter().first().idnum
    idnum = 1
    print session.query(YjStationInfo).filter().first()
    # version = session.query(YjStationInfo).version

    # 读取需要上传的值,所有时间大于上次上传的值

    last_log = session.query(TransferLog).order_by(TransferLog.date.desc()).first()
    if last_log:
        values = session.query(Value).filter_by(Value.date > last_log.date).all()
        upload_values = get_data_form_query(values)

    # 记录本次上传时间
    upload_time = datetime.datetime.utcnow()
    trans_type = "upload"

    data = {"YjValueInfo": upload_values, "Station_idnum": idnum}
    # data = encryption(data)
    rv = requests.post("http://127.0.0.1:11000/upload", json=data)
    print rv
    data = rv.json()
    # data = decryption(data)
    status = data["status"]
    log = TransferLog(type=trans_type, date=upload_time, status=status)
    session.add(log)
    session.commit()
    print data


if __name__ == '__main__':
    db_init()
    #while True:

        # Base.metadata.drop_all(bind=eng)
        # Base.metadata.create_all(bind=eng)




    #Base.metadata.create_all(bind=eng)
    #__test__transfer()
    #__test__unicode()
        #__test__beats()
    #__test__urllib()
        #__test__get_config()
        # time.sleep(5)
        #__test__upload()
    #cProfile.run('__test__transfer()')
    #prof = cProfile.Profile()
    #prof.enable()
    #__test__transfer()
    #prof.create_stats()
    #prof.print_stats()
    #p = pstats.Stats(prof)
    #p.print_callers()









#todo 使用删除后重新插入的方法需要值中不带外链,测试下使用update方法更新配置