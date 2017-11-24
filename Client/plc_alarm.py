import time
from models import PLCAlarm


def connect_plc_err(id_num, level=0, plc_id=None, plc_name=None):
    alarm = PLCAlarm(
        id_num=id_num,
        plc_id=plc_id,
        level=level,
        note='无法连接到PLC： "{}".'.format(plc_name),
        time=int(time.time())
    )
    return alarm


def read_err(id_num, level=0, plc_id=None, plc_name=None, area=None, db_num=None, start=None, data_type=None):
    alarm = PLCAlarm(
        id_num=id_num,
        plc_id=plc_id,
        level=level,
        note='读取到错误的地址： "plc:{}, area:{}, db_num:{}, start:{}, data_type:{}".'.format(
            plc_name, area, db_num, start, data_type),
        time=int(time.time())
    )
    return alarm
