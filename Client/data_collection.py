# coding=utf-8
import struct
import platform

from snap7.snap7types import S7AreaDB, S7AreaMK, S7AreaPA, S7AreaPE
from snap7.util import get_bool, set_bool, get_real, get_dword, get_int, set_dword, set_int, set_real


def snap7_path():
    system_str = platform.system()
    lib_path = '/plc_connect_lib/snap7'

    # Mac os
    if system_str == 'Darwin':
        lib_path += '/Mac_OS/libsnap7.dylib'

    elif system_str == 'Linux':
        # raspberry
        if platform.node() == 'raspberrypi':
            lib_path += '/Raspberry_Pi/libsnap7.so'

        # ubuntu
        elif platform.machine() == 'x86_64':
            lib_path += '/Ubuntu/libsnap7.so'

    else:
        lib_path += '/Win64/snap7.dll'

    return lib_path


def variable_size(data_type):
    # 'FLOAT'
    if data_type == 1:
        return 4

    # 'INT'
    elif data_type == 2:
        return 2

    # 'DINT'
    elif data_type == 3:
        return 4

    # 'WORD'
    elif data_type == 4:
        return 2

    # 'DWORD'
    elif data_type == 5:
        return 4

    # 'BYTE'
    elif data_type == 6:
        return 1

    # 'BOOL'
    elif data_type == 7:
        return 1

    else:
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
    # 'FLOAT'
    if data_type == 1:
        return get_real(result, byte_index)

    # 'INT'
    elif data_type == 2:
        return get_int(result, byte_index)

    # 'DINT'
    elif data_type == 3:
        return get_dint(result, byte_index)

    # 'WORD'
    elif data_type == 4:
        return get_word(result, byte_index)

    # 'DWORD'
    elif data_type == 5:
        return get_dword(result, byte_index)

    # 'BYTE'
    elif data_type == 6:
        return get_byte(result, byte_index)

    # 'BOOL'
    elif data_type == 7:
        return get_bool(result, byte_index, bool_index)

    else:
        assert ValueError, 'data_type is not useful'


def write_value(data_type, result, data, byte_index=0, bool_index=0):
    # 'FLOAT'
    if data_type == 1:
        set_real(result, byte_index, data)

    # 'INT'
    elif data_type == 2:
        set_int(result, byte_index, data)

    # 'DINT'
    elif data_type == 3:
        set_dint(result, byte_index, data)

    # 'WORD'
    elif data_type == 4:
        set_word(result, byte_index, data)

    # 'DWORD'
    elif data_type == 5:
        set_dword(result, byte_index, data)

    # 'BYTE'
    elif data_type == 6:
        set_byte(result, byte_index, data)

    # 'BOOL'
    elif data_type == 7:
        set_bool(result, byte_index, bool_index, data)


def analog2digital(analog_value, analog_low_range, analog_high_range, digital_low_range, digital_high_range):
    analog_low_range = analog_low_range if isinstance(analog_low_range, (float, int)) else 0
    analog_high_range = analog_high_range if isinstance(analog_high_range, (float, int)) else 0
    digital_high_range = digital_high_range if isinstance(digital_high_range, (float, int)) else 0
    digital_low_range = digital_low_range if isinstance(digital_low_range, (float, int)) else 0

    try:
        digital_value = ((analog_value - analog_low_range) / (analog_high_range - analog_low_range)) * (
            digital_high_range - digital_low_range)
    except ZeroDivisionError:
        digital_value = 0

    return digital_value
