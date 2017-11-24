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
from snap7.util import set_int

import struct
import snap7
from snap7.snap7types import S7AreaDB, S7AreaMK

snap7.common.load_library(lib_location=path.join(path.abspath(path.dirname(__file__)),
                                                 "plc_connect_lib/snap7/mac_os/libsnap7.dylib"))

# server_path = path.join(path.abspath(path.dirname(__file__)),
#                         "plc_connect_lib/python-snap7/snap7/bin/snap7-server.py")
# server_pid = Popen([server_path]).pid
# time.sleep(2)  # wait for server to start

client = snap7.client.Client()
# client.connect('192.168.18.12', 0, 2, 102)
client.connect('127.0.0.1', 1, 1, 1102)

client.db_rea
a = client.read_area(S7AreaDB, 1, 0, 2)
set_int(a, 0, 2)
client.write_area(S7AreaDB, 1, 0, a)
a = client.read_area(S7AreaDB, 1, 0, 2)
data = struct.unpack('!h', a)[0]

print(data)
# kill(server_pid, 1)