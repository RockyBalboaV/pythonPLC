
import ctypes

# a = ctypes.cdll.LoadLibrary("libnodave.net.dll")
# a.Read()

import clr
import System

import sys
clr.AddReferenceToFile("ClassLibrary1.dll")
print(dir())
from ClassLibrary1 import sim
print(dir())
client = sim()
print(client.__str__())


a = client.Read('IP', 132, 0, 'int', 1, '192.168.18.17', 0)
print(a)