import time
from app import station_info
from models import (eng, Base, Session, YjStationInfo, YjPLCInfo, YjGroupInfo, YjVariableInfo, TransferLog, \
                    Value, serialize, StationAlarm)


def check_time_err():
    alarm = StationAlarm(
        id_num=station_info.id_num,
        code=1,
        note='program has been interrupted',
        time=int(time.time())
    )
    return alarm


def connect_server_err():
    alarm = StationAlarm(
        id_num=station_info.id_num,
        code=2,
        note='can not connect to server',
        time=int(time.time())
    )
    return alarm



