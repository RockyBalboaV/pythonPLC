import time
from models import (StationAlarm)


def check_time_err(station_id_num):
    alarm = StationAlarm(
        id_num=station_id_num,
        code=1,
        note='program has been interrupted',
        time=int(time.time())
    )
    return alarm


def connect_server_err(station_id_num):
    alarm = StationAlarm(
        id_num=station_id_num,
        code=2,
        note='can not connect to server',
        time=int(time.time())
    )
    return alarm
