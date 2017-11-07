import pickle
import msgpack
import snap7
import shelve

class TestPLC():
    def test_connect(self):
        client = snap7.client.Client()
        client.connect('127.0.0.1', 1, 1, 102)
        assert client.get_connected()
        with shelve.open('a') as file:
            file['client'] = client
        p = pickle.Pickler(client)
        p.dump(client)
        s = msgpack.pack(client)
        assert s == 1