#coding=utf-8
import hmac, requests, json, chardet, base64, simplejson


data = {"name": "5", "id": "12", "tenid": "0"}
print type(data)
print isinstance(data, unicode)
h = hmac.new(b'poree')
data = unicode(data)
print type(data)
data = base64.b64encode(data)
print type(data)
h.update(bytes(data))
digest = h.hexdigest()
data = json.dumps({"data": data, "digest": digest})
print json.loads(data)["data"]
print digest
r = requests.post('http://127.0.0.1:11000/', data=data)
print r.text
