# coding=utf-8
from models import *
import hmac, requests, json, chardet, base64, simplejson, cProfile, pstats, PIL, zlib, hashlib
import urllib2, urllib
import MySQLdb


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
    print data
    print len(bytes(data))
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
    print data
    print len(bytes(data))

    return data


def __test__beats():
    data = {"idnum": 1}
    #data = encryption(data)
    rv = requests.post('http://127.0.0.1:11000/beats', json=data)
    data = rv.json()
    #data = decryption(rv)
    plc = YjStationInfo.query.filter_by(idnum=data["idnum"]).first()
    session.add(plc)
    session.commit()
    print data["modification"]


def __test__get_config():
    data = {"idnum": 1}
    #data = encryption(data)
    rv = requests.post('http://127.0.0.1:11000/config', json=data)
    data = rv.json()
    con = MySQLdb.connect('localhost', 'client', 'pyplc_client', 'pyplc_client')
    #with con as cur:
    #    cur.execute('drop table if exists yjstationinfo')
    #    cur.execute('drop table if exists yjplcinfo')
    #    cur.execute('drop table if exists yjgroupinfo')
    #    cur.execute('drop table if EXISTS yjvariableinfo')

    station = YjStationInfo(id=data["YjStationInfo"]["id"], name=data["YjStationInfo"]["name"],
                            mac=data["YjStationInfo"]["mac"], ip=data["YjStationInfo"]["ip"],
                            note=data["YjStationInfo"]["note"], idnum=data["YjStationInfo"]["idnum"],
                            plcnum=data["YjStationInfo"]["plcnum"], tenid=data["YjStationInfo"]["tenid"],
                            itemid=data["YjStationInfo"]["itemid"],
                            con_date=data["YjStationInfo"]["con_date"], modification=False)
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
    print data


def __test__unicode():
    a = {"a": "1", "b": "2"}
    b = json.dumps(a, encoding='utf-8')
    print type(b)
    print b

    #c = json.loads(b.decode(encoding='utf-8'))
    c = json.loads(b.replace("'", '"'))
    print c
    #print d

def __test__urllib():
    url = 'http://127.0.0.1:11000/beats'
    values = {"idnum": "1"}
    #data = urllib.urlencode(values)
    data = json.dumps(values)
    print data, type(data)
    req = urllib2.Request(url, data)
    response = urllib2.urlopen(req)
    html = response.read()
    print html


def __test__upload():
    data = {"YjValueInfo": [{"variable_id": "1", "value": "1"}, {"variable_id": "2", "value": "3"}],
            "Station_idnum": "1"}
    # data = encryption(data)
    rv = requests.post("http://127.0.0.1:11000/upload", json=data)
    print rv
    data = rv.json()
    # data = decryption(data)
    print data


if __name__ == '__main__':
    #Base.metadata.drop_all(bind=eng)
    #Base.metadata.create_all(bind=eng)
    #print(session.query(YjStationInfo).column_descriptions)
    #print(session.query(YjVariableInfo).all())
    #session.query(YjVariableInfo).delete()

    #session.query(YjGroupInfo).delete()
    #session.query(YjPLCInfo).delete()
    session.delete(session.query(YjStationInfo).first())
    #print session.query(YjGroupInfo).all()
    #session.delete(session.query(YjGroupInfo).all())
    session.commit()


    #Base.metadata.create_all(bind=eng)
    #__test__transfer()
    #__test__unicode()
    #__test__beats()
    #__test__urllib()
    #__test__get_config()
    #__test__upload()
    #cProfile.run('__test__transfer()')
    #prof = cProfile.Profile()
    #prof.enable()
    #__test__transfer()
    #prof.create_stats()
    #prof.print_stats()
    #p = pstats.Stats(prof)
    #p.print_callers()









