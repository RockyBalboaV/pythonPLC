import pickle
import msgpack
import snap7
from snap7.snap7exceptions import Snap7Exception
from snap7.util import set_real, get_real, set_bool, get_bool
from snap7.snap7types import S7AreaDB

import shelve
from data_collection import load_snap7


class TestPLC:
    @classmethod
    def setup_class(cls):
        load_snap7()
        cls.client = snap7.client.Client()

    @classmethod
    def teardown_class(cls):
        cls.client.destroy()

    def setup_method(self, method):
        self.client.connect('192.168.18.17', 0, 2, 102)

    def teardown_method(self, method):
        self.client.disconnect()

    def test_db_read_bool(self):
        byte_data = self.client.db_read(151, 156, 1)
        data = get_bool(byte_data, 0, 5)
        print(data)

    def test_db_write(self):
        byte_data = self.client.db_read(151, 156, 1)
        data = get_bool(byte_data, 0, 5)
        print(data)
        set_bool(byte_data, 0, 5, False)
        self.client.db_write(151, 156, byte_data)
        byte_data = self.client.db_read(151, 156, 1)
        data = get_bool(byte_data, 0, 5)
        print(data)

    def test_db_connected(self):
        assert self.client.get_connected() is True
