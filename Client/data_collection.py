# coding=utf-8
import struct
import math

import snap7
from snap7.snap7types import S7AreaDB, S7AreaMK, S7AreaPA, S7AreaPE
from snap7.util import get_bool, set_bool


def variable_size(variable_model):
    if variable_model.data_type == 'FLOAT':
        return 4
    elif variable_model.data_type == 'INT':
        return 2
    elif variable_model.data_type == 'DINT':
        return 4
    elif variable_model.data_type == 'WORD':
        return 2
    elif variable_model.data_type == 'BYTE':
        return 1
    elif variable_model.data_type == 'BOOL':
        return 1
    elif variable_model.data_type == 'DWORD':
        return 4
    else:
        assert ValueError, 'data_type is not useful'
        return 4


def variable_area(variable_model):
    if variable_model.area == 1:
        return S7AreaDB
    elif variable_model.area == 2:
        return S7AreaPE
    elif variable_model.area == 3:
        return S7AreaPA
    elif variable_model.area == 4:
        return S7AreaMK
    else:
        return S7AreaDB


def read_value(variable_model, result, bool_index=None):
    if variable_model.data_type == 'FLOAT':
        return struct.unpack('!f', result)[0]
    elif variable_model.data_type == 'INT':
        return struct.unpack('!h', result)[0]
    elif variable_model.data_type == 'DINT':
        return struct.unpack('!i', result)[0]
    elif variable_model.data_type == 'WORD':
        return struct.unpack('!H', result)[0]
    elif variable_model.data_type == 'BYTE':
        return struct.unpack('!s', result)[0]
    elif variable_model.data_type == 'BOOL':
        return get_bool(result, 0, bool_index)
    elif variable_model.data_type == 'DWORD':
        return struct.unpack('!I', result)[0]
    else:
        assert ValueError, 'data_type is not useful'


def write_value(variable_model, data, bool_index=None):
    if variable_model.data_type == 'FLOAT':
        return struct.pack('!f', data)
    elif variable_model.data_type == 'INT':
        return struct.pack('!h', data)
    elif variable_model.data_type == 'DINT':
        return struct.pack('!i', data)
    elif variable_model.data_type == 'WORD':
        return struct.pack('!H', data)
    elif variable_model.data_type == 'BYTE':
        return struct.pack('!s', data)
    elif variable_model.data_type == 'BOOL':
        bool_index = int(math.modf(variable_model.address)[0] * 10)
        return set_bool(data, 0, bool_index)
    elif variable_model.data_type == 'DWORD':
        return struct.pack('!I', data)


class PythonPLC(object):
    def __init__(self, ip, rack, slot):
        self.ip = ip
        self.rack = rack
        self.slot = slot

    def __enter__(self):
        self.client = snap7.client.Client()
        self.client.connect(self.ip, self.rack, self.slot)
        return self.client

    def __exit__(self, *args):
        self.client.disconnect()
        self.client.destroy()
