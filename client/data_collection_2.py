# coding=utf-8
import struct
import time
import platform

from snap7.snap7types import S7AreaDB, S7AreaMK, S7AreaPA, S7AreaPE
from snap7.util import get_bool, set_bool, get_real, get_dword, get_int, set_dword, set_int, set_real
import numpy as np


def snap7_path():
    system_str = platform.system()
    lib_path = '/plc_connect_lib/snap7'

    # Mac os
    if system_str == 'Darwin':
        lib_path += '/mac_os/libsnap7.dylib'

    elif system_str == 'Linux':
        # raspberry
        if platform.node() == 'raspberrypi':
            lib_path += '/raspberry/libsnap7.so'

        # ubuntu
        elif platform.machine() == 'x86_64':
            lib_path += '/ubuntu/libsnap7.so'

    return lib_path


def variable_size(data_type):
    if data_type == 'FLOAT':
        return 4
    elif data_type == 'INT':
        return 2
    elif data_type == 'DINT':
        return 4
    elif data_type == 'WORD':
        return 2
    elif data_type == 'BYTE':
        return 1
    elif data_type == 'BOOL':
        return 1
    elif data_type == 'DWORD':
        return 4
    else:
        assert ValueError, 'data_type is not useful'
        return 4


def variable_area(area):
    if area == 1:
        return S7AreaDB
    elif area == 2:
        return S7AreaPE
    elif area == 3:
        return S7AreaPA
    elif area == 4:
        return S7AreaMK
    else:
        return S7AreaDB


def set_dint(_bytearray, byte_index, _int):
    """
    Set value in bytearray to int
    """
    # make sure were dealing with an int
    _int = int(_int)
    _bytes = struct.unpack('4B', struct.pack('>i', _int))
    _bytearray[byte_index:4] = _bytes


def get_dint(_bytearray, byte_index):
    data = _bytearray[byte_index:byte_index + 4]
    value = struct.unpack('>i', struct.pack('4B', *data))[0]
    return value


def set_word(_bytearray, byte_index, word):
    word = int(word)
    _bytes = struct.unpack('2B', struct.pack('>H', word))
    _bytearray[byte_index:2] = _bytes


def get_word(_bytearray, byte_index):
    data = _bytearray[byte_index:byte_index + 2]
    value = struct.unpack('>H', struct.pack('2B', *data))[0]
    return value


def set_byte(_bytearray, byte_index, byte):
    byte = int(byte)
    _bytes = struct.unpack('1B', struct.pack('>s', byte))
    _bytearray[byte_index:1] = _bytes


def get_byte(_bytearray, byte_index):
    data = _bytearray[byte_index:byte_index + 1]
    value = struct.unpack('>s', struct.pack('1B', *data))[0]
    return value


def read_value(data_type, result, byte_index=0, bool_index=0):
    if data_type == 'FLOAT':
        return get_real(result, byte_index)

    elif data_type == 'INT':
        return get_int(result, byte_index)

    elif data_type == 'DINT':
        return get_dint(result, byte_index)

    elif data_type == 'WORD':
        return get_word(result, byte_index)

    elif data_type == 'BYTE':
        return get_byte(result, byte_index)

    elif data_type == 'BOOL':
        return get_bool(result, byte_index, bool_index)

    elif data_type == 'DWORD':
        return get_dword(result, byte_index)

    else:
        assert ValueError, 'data_type is not useful'


def write_value(data_type, result, data, byte_index=0, bool_index=0):
    if data_type == 'FLOAT':
        set_real(result, byte_index, data)

    elif data_type == 'INT':
        set_int(result, byte_index, data)

    elif data_type == 'DINT':
        set_dint(result, byte_index, data)

    elif data_type == 'WORD':
        set_word(result, byte_index, data)

    elif data_type == 'BYTE':
        set_byte(result, byte_index, data)

    elif data_type == 'BOOL':
        set_bool(result, byte_index, bool_index, data)

    elif data_type == 'DWORD':
        set_dword(result, byte_index, data)


import snap7
import snap7.snap7types as ID
import struct
import math


def order1(string):
    i = 0
    j = 0
    n = len(string)
    while j < n - 1:
        while i < n - 1 - j:
            if string[i][1] > string[i + 1][1]:
                temp = string[i + 1]
                string[i + 1] = string[i]
                string[i] = temp
            i = i + 1
        i = 0
        j = j + 1


def order0(string):
    i = 0
    j = 0
    n = len(string)
    while j < n - 1:
        while i < n - 1 - j:
            if string[i][0] > string[i + 1][0]:
                temp = string[i + 1]
                string[i + 1] = string[i]
                string[i] = temp
            i = i + 1
        i = 0
        j = j + 1


def unpack(array_read, array_order, variables):
    buffer = []
    j = 0
    for loop in range(len(array_order)):
        a = array_order[loop][0]
        print(a)
        start_index = int(math.modf(variables[a]['address'])[1])
        i = 0
        while i < len(array_order[loop]):
            order = array_order[loop][i]
            byte_index = int(math.modf(variables[order]['address'])[1])
            type = variables[order]['data_type']
            if type == 7:
                bool_index = round(math.modf(variables[order]['address'])[0] * 10)
                buffer.append([get_bool(array_read[loop], byte_index - start_index, bool_index)])
            if type == 6:
                buffer.append([get_byte(array_read[loop], byte_index - start_index)])
            if type == 4:
                buffer.append([get_word(array_read[loop], byte_index - start_index)])
            if type == 5:
                buffer.append([get_dword(array_read[loop], byte_index - start_index)])
            if type == 2:
                buffer.append([get_int(array_read[loop], byte_index - start_index)])
            if type == 3:
                buffer.append([get_dint(array_read[loop], byte_index - start_index)])
            if type == 1:
                buffer.append([get_real(array_read[loop], byte_index - start_index)])
            buffer[j].append(order)
            j = j + 1
            i = i + 2

    order1(buffer)  # 按最后一列顺序排序
    return buffer


def dborder(str_D):
    s = []  # 按db分区 类[[db1,loop,offset],[db2,loop,offset].......]
    flag = 0
    for i in range(len(str_D)):
        for j in range(len(s)):
            if s[j][0] == str_D[i][0]:
                flag = 1
                s[j].append(str_D[i][1])
                s[j].append(str_D[i][2])
        if flag == 0:
            s.append([str_D[i][0], str_D[i][1], str_D[i][2]])
        flag = 0
    return s


def PDUorder(string, variables):
    j = 0  # 相对距离差18，总长度小于222，最终分组
    n = len(string)
    s = []
    if n > 0:
        s = [[string[0][0], string[0][1]]]
        for i in range(n - 1):
            offnum = variable_size(variables[string[i + 1][0]]['data_type'])
            if string[i + 1][1] - string[i][1] + offnum < 96 and len(s[j]) < 222:
                s[j].append(string[i + 1][0])
                s[j].append(string[i + 1][1])
            else:
                s.append([string[i + 1][0], string[i + 1][1]])
                j = j + 1
    return s


def readsuan(variables):
    str_I = []
    str_Q = []
    str_M = []
    str_D = []

    for loop in range(len(variables)):  # 按M D I Q分成四区域，二维数组[[],[],[].....]
        offset = int(math.modf(variables[loop]['address'])[1])
        if variable_area(variables[loop]['area']) == S7AreaPA:
            str_I.append([loop, offset])
        if variable_area(variables[loop]['area']) == S7AreaPE:
            str_Q.append([loop, offset])
        if variable_area(variables[loop]['area']) == S7AreaMK:
            str_M.append([loop, offset])
        if variable_area(variables[loop]['area']) == S7AreaDB:
            str_D.append([variables[loop]['db_num'], loop, offset])

    str_D = dborder(str_D)  # 按db分区 类[[db1,loop,offset],[db2,loop,offset].......]

    for i in range(len(str_D)):  # [[loop,offset,loop,offset],......]去除db号
        del str_D[i][0]

    order1(str_I)  # 按第2个元素顺序排序
    order1(str_Q)
    order1(str_M)

    str_I = PDUorder(str_I, variables)  # 相对距离差18，总长度小于222，最终分组
    str_Q = PDUorder(str_Q, variables)
    str_M = PDUorder(str_M, variables)

    s = []
    temp = []
    for i in range(len(str_D)):  # db排序和最终分组
        j = 0
        while j < len(str_D[i]):
            temp.append([str_D[i][j], str_D[i][j + 1]])
            j = j + 2
        order1(temp)
        s += PDUorder(temp, variables)
        temp = []

    s = s + str_I + str_Q + str_M  # 最终数组

    IP = "192.168.18.17"
    read_array = []

    for i in range(len(s)):
        num = s[i][0]
        area = variable_area(variables[num]['area'])
        db_number = variables[num]['db_num']
        offnum = variable_size(variables[num]['data_type'])
        size = s[i][int(len(s[i])) - 1] - s[i][1] + offnum
        start = s[i][1]
        client = snap7.client.Client()
        client.create()
        client.connect(address=IP, rack=0, slot=2, tcpport=102)
        time1 = time.time()
        read_array.append(client.read_area(area=area, dbnumber=db_number, start=start, size=size))
        time2 = time.time()
        print('读取时间', time2 - time1)
        client.disconnect()
        client.destroy()


    temp = unpack(read_array, s, variables)
    print(temp)
    return temp


variables = [
    {'id': 315, 'db_num': 11, 'address': 22.0, 'data_type': 1, 'area': 1, 'is_analog': False, 'analog_low_range': 0.0,
     'analog_high_range': 0.0, 'digital_low_range': 0.0, 'digital_high_range': 0.0, 'offset': 0.0},
    {'id': 316, 'db_num': 11, 'address': 342.0, 'data_type': 1, 'area': 1, 'is_analog': False, 'analog_low_range': 0.0,
     'analog_high_range': 0.0, 'digital_low_range': 0.0, 'digital_high_range': 0.0, 'offset': 0.0},
    {'id': 319, 'db_num': 11, 'address': 582.0, 'data_type': 1, 'area': 1, 'is_analog': False, 'analog_low_range': 0.0,
     'analog_high_range': 0.0, 'digital_low_range': 0.0, 'digital_high_range': 0.0, 'offset': 0.0},
    {'id': 320, 'db_num': 11, 'address': 262.0, 'data_type': 1, 'area': 1, 'is_analog': False, 'analog_low_range': 0.0,
     'analog_high_range': 0.0, 'digital_low_range': 0.0, 'digital_high_range': 0.0, 'offset': 0.0},
    {'id': 321, 'db_num': 11, 'address': 102.0, 'data_type': 1, 'area': 1, 'is_analog': False, 'analog_low_range': 0.0,
     'analog_high_range': 0.0, 'digital_low_range': 0.0, 'digital_high_range': 0.0, 'offset': 0.0},
    {'id': 322, 'db_num': 11, 'address': 422.0, 'data_type': 1, 'area': 1, 'is_analog': False, 'analog_low_range': 0.0,
     'analog_high_range': 0.0, 'digital_low_range': 0.0, 'digital_high_range': 0.0, 'offset': 0.0},
    {'id': 323, 'db_num': 11, 'address': 662.0, 'data_type': 1, 'area': 1, 'is_analog': False, 'analog_low_range': 0.0,
     'analog_high_range': 0.0, 'digital_low_range': 0.0, 'digital_high_range': 0.0, 'offset': 0.0},
    {'id': 324, 'db_num': 11, 'address': 182.0, 'data_type': 1, 'area': 1, 'is_analog': False, 'analog_low_range': 0.0,
     'analog_high_range': 0.0, 'digital_low_range': 0.0, 'digital_high_range': 0.0, 'offset': 0.0},
    {'id': 325, 'db_num': 11, 'address': 502.0, 'data_type': 1, 'area': 1, 'is_analog': False, 'analog_low_range': 0.0,
     'analog_high_range': 0.0, 'digital_low_range': 0.0, 'digital_high_range': 0.0, 'offset': 0.0},
    {'id': 326, 'db_num': 11, 'address': 742.0, 'data_type': 1, 'area': 1, 'is_analog': False, 'analog_low_range': 1.0,
     'analog_high_range': 1.0, 'digital_low_range': 1.0, 'digital_high_range': 1.0, 'offset': 1.0},
    {'id': 327, 'db_num': 141, 'address': 16.1, 'data_type': 7, 'area': 1, 'is_analog': False, 'analog_low_range': 0.0,
     'analog_high_range': 0.0, 'digital_low_range': 0.0, 'digital_high_range': 0.0, 'offset': 0.0},
    {'id': 328, 'db_num': 141, 'address': 16.2, 'data_type': 7, 'area': 1, 'is_analog': False, 'analog_low_range': 1.0,
     'analog_high_range': 1.0, 'digital_low_range': 1.0, 'digital_high_range': 1.0, 'offset': 0.0},
    {'id': 329, 'db_num': 141, 'address': 6.0, 'data_type': 2, 'area': 1, 'is_analog': False, 'analog_low_range': 1.0,
     'analog_high_range': 1.0, 'digital_low_range': 1.0, 'digital_high_range': 1.0, 'offset': 0.0},
    {'id': 331, 'db_num': 141, 'address': 30.0, 'data_type': 3, 'area': 1, 'is_analog': False, 'analog_low_range': 1.0,
     'analog_high_range': 1.0, 'digital_low_range': 1.0, 'digital_high_range': 1.0, 'offset': 0.0},
    {'id': 344, 'db_num': 141, 'address': 26.0, 'data_type': 3, 'area': 1, 'is_analog': False, 'analog_low_range': 1.0,
     'analog_high_range': 1.0, 'digital_low_range': 1.0, 'digital_high_range': 1.0, 'offset': 0.0},
    {'id': 332, 'db_num': 151, 'address': 16.0, 'data_type': 7, 'area': 1, 'is_analog': False, 'analog_low_range': 1.0,
     'analog_high_range': 1.0, 'digital_low_range': 1.0, 'digital_high_range': 1.0, 'offset': 0.0},
    {'id': 333, 'db_num': 151, 'address': 16.2, 'data_type': 7, 'area': 1, 'is_analog': False, 'analog_low_range': 1.0,
     'analog_high_range': 1.0, 'digital_low_range': 1.0, 'digital_high_range': 1.0, 'offset': 0.0},
    {'id': 334, 'db_num': 151, 'address': 6.0, 'data_type': 2, 'area': 1, 'is_analog': False, 'analog_low_range': 1.0,
     'analog_high_range': 1.0, 'digital_low_range': 1.0, 'digital_high_range': 1.0, 'offset': 0.0},
    {'id': 335, 'db_num': 151, 'address': 26.0, 'data_type': 3, 'area': 1, 'is_analog': False, 'analog_low_range': 1.0,
     'analog_high_range': 1.0, 'digital_low_range': 1.0, 'digital_high_range': 1.0, 'offset': 0.0},
    {'id': 336, 'db_num': 151, 'address': 30.0, 'data_type': 3, 'area': 1, 'is_analog': False, 'analog_low_range': 1.0,
     'analog_high_range': 1.0, 'digital_low_range': 1.0, 'digital_high_range': 1.0, 'offset': 0.0},
    {'id': 337, 'db_num': 161, 'address': 16.0, 'data_type': 7, 'area': 1, 'is_analog': False, 'analog_low_range': 1.0,
     'analog_high_range': 1.0, 'digital_low_range': 1.0, 'digital_high_range': 1.0, 'offset': 0.0},
    {'id': 338, 'db_num': 161, 'address': 16.2, 'data_type': 7, 'area': 1, 'is_analog': False, 'analog_low_range': 1.0,
     'analog_high_range': 1.0, 'digital_low_range': 1.0, 'digital_high_range': 1.0, 'offset': 0.0},
    {'id': 339, 'db_num': 161, 'address': 6.0, 'data_type': 2, 'area': 1, 'is_analog': False, 'analog_low_range': 1.0,
     'analog_high_range': 1.0, 'digital_low_range': 1.0, 'digital_high_range': 1.0, 'offset': 0.0},
    {'id': 340, 'db_num': 161, 'address': 26.0, 'data_type': 3, 'area': 1, 'is_analog': False, 'analog_low_range': 1.0,
     'analog_high_range': 1.0, 'digital_low_range': 1.0, 'digital_high_range': 1.0, 'offset': 0.0},
    {'id': 341, 'db_num': 161, 'address': 30.0, 'data_type': 3, 'area': 1, 'is_analog': False, 'analog_low_range': 1.0,
     'analog_high_range': 1.0, 'digital_low_range': 1.0, 'digital_high_range': 1.0, 'offset': 0.0}]
