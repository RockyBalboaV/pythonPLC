import time
from models import PLCAlarm


def connect_plc_err(id_num, level=0, plc_id=None,):
    """
    无法连接到PLC
    :param id_num: 
    :param plc_id: 
    :param plc_name: 
    :return: 
    """
    alarm = PLCAlarm(
        id_num=id_num,
        plc_id=plc_id,
        level=level,
        time=int(time.time())
    )
    return alarm


def read_err(id_num, level=0, plc_id=None, plc_name=None, area=None, db_num=None, start=None, data_type=None):
    """
    读取到错误的地址
    :param id_num: 
    :param level: 
    :param plc_id: 
    :param plc_name: 
    :param area: 
    :param db_num: 
    :param start: 
    :param data_type: 
    :return: 
    """
    alarm = PLCAlarm(
        id_num=id_num,
        plc_id=plc_id,
        level=level,
        note='读取到错误的地址： "plc:{}, area:{}, db_num:{}, start:{}, data_type:{}".'.format(
            plc_name, area, db_num, start, data_type),
        time=int(time.time())
    )
    return alarm
