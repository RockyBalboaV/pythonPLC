import time
from app import station_info
from models import PLCAlarm


def connect_plc_err(level=0, plc_id=None, plc_name=None):
    alarm = PLCAlarm(
        id_num=station_info,
        plc_id=plc_id,
        level=level,
        note='can not connect to plc "{}".'.format(plc_name),
        time=int(time.time())
    )
    return alarm
