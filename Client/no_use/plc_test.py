import ctypes
import struct
import unittest
import logging
import time
import mock

from subprocess import Popen
from os import path, kill
import snap7
from snap7.snap7exceptions import Snap7Exception
from snap7.snap7types import S7AreaDB, S7WLByte, S7DataItem
from snap7 import util


logging.basicConfig(level=logging.WARNING)

ip = '127.0.0.1'
tcpport = 1102
db_number = 1
rack = 1
slot = 1

class TestClient(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        server_path = path.join(path.dirname(path.realpath(snap7.__file__)),
                                "bin/snap7-server.py")
        cls.server_pid = Popen([server_path]).pid
        time.sleep(2)  # wait for server to start

    @classmethod
    def tearDownClass(cls):
        kill(cls.server_pid, 1)

    def setUp(self):
        self.client = snap7.client.Client()
        self.client.connect(ip, rack, slot, tcpport)

    def tearDown(self):
        self.client.disconnect()
        self.client.destroy()

if __name__ == '__main__':
    unittest.main()