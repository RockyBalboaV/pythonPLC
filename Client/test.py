import struct
import snap7
from snap7.snap7types import S7AreaDB, S7AreaMK 

snap7.common.load_library(lib_location="/home/pi/pythonPLC/Client/libsnap7.so")
client = snap7.client.Client()
client.connect('192.168.1.10', 0, 2)

a = client.read_area(S7AreaDB, 1, 0, 2)
data = struct.unpack('!H', a)[0]

print(data)
