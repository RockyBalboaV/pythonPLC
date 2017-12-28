# coding=utf-8
import hmac, requests, json, chardet, base64, simplejson, cProfile, pstats, PIL, zlib, hashlib
import urllib2, urllib

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
    # data['data']=zlib.compress(data['data']).encode('utf-8')

    rv = requests.post('http://127.0.0.1:11000/beats', json=data)
    data = rv.json()
    #data = decryption(rv)
    print data["modification"]


def __test__transfer():
    data = {"idnum": 1}
    print type(data)
    print isinstance(data, unicode)
    h = hmac.new(b'poree')
    data = unicode(data)
    print type(data)
    data = base64.b64encode(data)
    print type(data)
    h.update(bytes(data))
    digest = h.hexdigest()
    data = {"data": data, "digest": digest}
    #data = json.dumps({"data": data, "digest": digest})
    # print json.loads(data)["data"]
    print digest
    r = requests.post('http://127.0.0.1:11000/', json=data)
    print r.text


def __test__get_config():
    data = {"idnum": 1}
    #data = encryption(data)
    rv = requests.post('http://127.0.0.1:11000/config', json=data)
    data = rv.json()
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
    #__test__transfer()
    #__test__unicode()
    #__test__beats()
    #__test__urllib()
    #__test__get_config()
    __test__upload()
    #cProfile.run('__test__transfer()')
    #prof = cProfile.Profile()
    #prof.enable()
    #__test__transfer()
    #prof.create_stats()
    #prof.print_stats()
    #p = pstats.Stats(prof)
    #p.print_callers()

