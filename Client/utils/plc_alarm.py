import time
from models import PLCAlarm


def plc_err(id_num, plc_id, code, note):
    alarm = PLCAlarm(
        id_num=id_num,
        plc_id=plc_id,
        time=int(time.time()),
        code=code,
        note=note
    )
    return alarm


def connect_plc_err(id_num, plc_id=None, note=None):
    """
    无法连接到PLC
    :param id_num: 
    :param plc_id: 
    :param note: 
    :return: 
    """
    return plc_err(id_num, plc_id, 1, note)


def read_err(id_num, plc_id=None, plc_name=None, area=None, db_num=None, address=None, data_type=None):
    """
    读取错误
    :param id_num: 
    :param plc_id: 
    :param plc_name: 
    :param area: 
    :param db_num: 
    :param address: 
    :param data_type: 
    :return: 
    """
    note = '读取错误： "plc_id:{}, plc_name: {}, area:{}, db_num:{}, address:{}, data_type:{}".'.format(
        plc_id, plc_name, area, db_num, address, data_type),
    return plc_err(id_num, plc_id, 2, note)
