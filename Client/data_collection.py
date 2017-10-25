# coding=utf-8
import struct

from snap7.snap7types import S7AreaDB, S7AreaMK, S7AreaPA, S7AreaPE
from snap7.util import get_bool, set_bool, get_real, get_dword, get_int, set_dword, set_int, set_real


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
