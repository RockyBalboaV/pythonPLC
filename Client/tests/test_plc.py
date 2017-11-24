import pickle
import msgpack
import snap7
from snap7.snap7exceptions import Snap7Exception
import shelve

# class TestPLC():
#     def test_connect(self):
client = snap7.client.Client()
try:
    client.connect('192.168.18.18', 0, 2, 102)
except Snap7Exception as e:
    print(e)
# assert client.get_connected()