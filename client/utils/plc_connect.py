import logging
import math
import ctypes
from contextlib import contextmanager

from snap7.client import Client
from snap7.snap7exceptions import Snap7Exception
from snap7.snap7types import S7DataItem, S7WLByte

from models import Session, Value
from utils.plc_alarm import read_err, connect_plc_err, Snap7ReadException, Snap7ConnectException
from data_collection import variable_size, variable_area, read_value, analog2digital, write_value, load_snap7
from utils.redis_middle_class import r

import time
# 读取snap7 C库
load_snap7()


@contextmanager
def plc_client(ip, rack, slot, plc_id):
    """
    建立plc连接的上下文管理器
    :param ip: 
    :param rack: 
    :param slot: 
    :return: 
    """
    client = Client()
    try:
        client.connect(ip, rack, slot)
    except Snap7Exception as e:
        logging.warning('连接plc失败' + str(e))
        session = Session()
        id_num = r.get('id_num')
        alarm = connect_plc_err(id_num, plc_id)
        session.add(alarm)
        session.commit()
    yield client
    client.disconnect()
    client.destroy()


def read_multi(plc, variables, current_time, client=None):
    # time1 = time.time()
    # print('采集')
    value_list = list()
    var_num = len(variables)
    # print('采集数量：{}'.format(var_num))
    bool_indexes = list()
    data_items = (S7DataItem * var_num)()

    for num in range(var_num):
        area = variable_area(variables[num]['area'])
        db_number = variables[num]['db_num']
        size = variable_size(variables[num]['data_type'])
        address = int(math.modf(variables[num]['address'])[1])
        bool_index = round(math.modf(variables[num]['address'])[0] * 10)
        bool_indexes.append(bool_index)

        data_items[num].Area = ctypes.c_int32(area)
        data_items[num].WordLen = ctypes.c_int32(S7WLByte)
        data_items[num].Result = ctypes.c_int32(0)
        data_items[num].DBNumber = ctypes.c_int32(db_number)
        data_items[num].Start = ctypes.c_int32(address)
        data_items[num].Amount = ctypes.c_int32(size)  # reading a REAL, 4 bytes

    for di in data_items:
        # create the buffer
        buffer = ctypes.create_string_buffer(di.Amount)

        # cast the pointer to the buffer to the required type
        pBuffer = ctypes.cast(
            ctypes.pointer(buffer),
            ctypes.POINTER(ctypes.c_uint8)
        )
        di.pData = pBuffer

    if not client.get_connected():

        try:
            client.connect(
                address=plc['ip'],
                rack=plc['rack'],
                slot=plc['slot'],
            )
        except Snap7Exception as e:
            logging.warning('PLC连接失败 ip：{} rack：{} slot:{}'.format(plc['ip'], plc['rack'], plc['slot']) + str(e))
            raise Snap7ConnectException

    # time1 = time.time()
    result, data_items = client.read_multi_vars(data_items)
    # time2 = time.time()
    # print('读取时间', time2 - time1)

    for num in range(0, var_num):
        di = data_items[num]

        try:
            raw_value = read_value(
                variables[num]['data_type'],
                di.pData,
                bool_index=bool_indexes[num]
            )

            # print(raw_value)
        except Snap7Exception as e:
            logging.error('plc读取数据错误' + str(e))
            raise Snap7ReadException(
                variables[num]['area'],
                variables[num]['db_num'],
                variables[num]['address'],
                variables[num]['data_type']
            )
        else:
            # 数模转换
            if variables[num]['is_analog']:
                raw_value = analog2digital(
                    raw_value,
                    variables[num]['analog_low_range'],
                    variables[num]['analog_high_range'],
                    variables[num]['digital_low_range'],
                    variables[num]['digital_high_range']
                )
                # 数据量修改
                offset = variables[num]['offset'] if isinstance(variables[num]['offset'], float) else 0
                raw_value += + offset

            # 限制小数位数
            value = round(raw_value, 2)

            # value_info = (variables[num]['id'], value, current_time)
            value_info = (variables[num]['id'], value, current_time)

            value_list.append(value_info)
    # value_list = {'time': current_time, 'value': value_list}
    return value_list
    # print('采集数据', len(value_list), value_list)
    # time2 = time.time()

    # print('单次采集时间', time2 - time1)


def plc_write(variable_model, plc_cli, plc_model):
    id_num = r.get('id_num')
    # 获取变量读写类型
    rw_type = variable_model.rw_type
    value = variable_model.write_value

    # 判断变量存在写操作
    if rw_type == 2 or rw_type == 3 and value is not None:

        # 获取写入变量值所需信息
        data_type = variable_model.data_type
        db = variable_model.db_num
        area = variable_area(variable_model)
        address = int(math.modf(variable_model.address)[1])
        bool_index = round(math.modf(variable_model.address)[0] * 10)
        size = variable_size(data_type)

        # 获取当前字节
        try:
            result = plc_cli.read_area(
                area=area,
                dbnumber=db,
                start=address,
                size=size
            )
        except Snap7Exception as e:
            logging.error('plc_read', str(e))
            read_err(
                id_num=id_num,
                plc_id=plc_model.id,
                plc_name=plc_model.plc_name,
                area=area,
                db_num=db,
                address=address,
                data_type=data_type
            )

        else:

            # 将写入数据转为字节码
            byte_value = write_value(
                data_type,
                result,
                value,
                bool_index=bool_index
            )

            # 数据写入
            plc_cli.write_area(
                area=area,
                dbnumber=db,
                start=address,
                data=byte_value
            )


def plc_connect(plc):
    client = Client()
    try:
        client.connect(
            address=plc['ip'],
            rack=plc['rack'],
            slot=plc['slot'],
        )
    except Snap7Exception as e:
        logging.warning('PLC连接失败 ip：{} rack：{} slot:{}'.format(plc['ip'], plc['rack'], plc['slot']) + str(e))
        id_num = r.get('id_num')
        connect_plc_err(
            id_num,
            plc_id=plc['id'],
        )

    return client
