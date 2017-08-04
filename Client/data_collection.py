# coding=utf-8
import snap7
from snap7.snap7types import S7AreaDB, S7AreaMK, S7AreaPA, S7AreaPE


def variable_size(variable_model):
    if variable_model.data_type == 'FLOAT':
        return 'f', 4
    elif variable_model.data_type == 'INT':
        return 'h', 2
    elif variable_model.data_type == 'DINT':
        return 'i', 4
    elif variable_model.data_type == 'WORD':
        return 'H', 2
    elif variable_model.data_type == 'BYTE':
        return 's', 1
    elif variable_model.data_type == 'BOOL':
        return '?', 1
    else:
        return 'h', 2


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
