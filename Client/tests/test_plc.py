import pickle
import msgpack
import snap7
from snap7.snap7exceptions import Snap7Exception
from snap7.util import set_real, get_real, set_bool, get_bool
from snap7.snap7types import S7AreaDB

import shelve

# class TestPLC():
#     def test_connect(self):
client = snap7.client.Client()
try:
    client.connect('192.168.18.17', 0, 2, 102)
except Snap7Exception as e:
    print(e)
# data = client.db_read(11, 502, 4)
data = client.db_read(151, 156, 1)
b = get_bool(data, 0, 5)
print(b)
set_bool(data, 0, 5, False)
client.db_write(151, 156, data)
data = client.db_read(151, 156, 1)
b = get_bool(data, 0, 5)
print(b)
# print(get_real(data, 0))
# set_real(data, 0, 1)
# client.db_write(1, 0, data)
# data = client.db_read(1, 0, 4)
# print(get_real(data, 0))
# assert client.get_connected()