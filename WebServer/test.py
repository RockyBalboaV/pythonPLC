# coding=utf-8
import hmac, requests, json, chardet, base64, simplejson, cProfile, pstats, PIL


def __test__transfer():
    data = {"name": "5", "id": "2", "tenid": "0"}
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


def __test__unicode():
    a = {"a": "1", "b": "2"}
    b = json.dumps(a, encoding='utf-8')
    print type(b)
    print b

    #c = json.loads(b.decode(encoding='utf-8'))
    c = json.loads(b.replace("'", '"'))
    print c
    #print d


if __name__ == '__main__':
     __test__transfer()
    #__test__unicode()
    #cProfile.run('__test__transfer()')
    #prof = cProfile.Profile()
    #prof.enable()
    #__test__transfer()
    #prof.create_stats()
    #prof.print_stats()
    #p = pstats.Stats(prof)
    #p.print_callers()

