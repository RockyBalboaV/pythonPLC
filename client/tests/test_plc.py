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
        byte_data = self.client.db_read(151, 164, 1)
        data = get_bool(byte_data, 0, 5)
        print(data)

    def test_db_write_bool(self):
        byte_data = self.client.db_read(141, 164, 1)
        data = get_bool(byte_data, 0, 1)
        print(data)
        set_bool(byte_data, 0, 1, 1)
        self.client.db_write(141, 164, byte_data)
        byte_data = self.client.db_read(141, 164, 1)
        data = get_bool(byte_data, 0, 1)
        print(data)

    def test_db_write_real(self):
        byte_data = self.client.db_read(11, 22, 4)
        data = get_real(byte_data, 0)
        print(data)
        set_real(byte_data, 0, 33)
        self.client.db_write(11, 22, byte_data)
        byte_data = self.client.db_read(11, 22, 4)
        data = get_real(byte_data, 0)
        print(data)

    def test_db_connected(self):
        assert self.client.get_connected() is True
