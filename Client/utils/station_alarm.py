import time
from models import StationAlarm


def station_err(id_num, code, note):
    alarm = StationAlarm(
        id_num=id_num,
        code=code,
        time=int(time.time()),
        note=note
    )
    return alarm


def check_time_err(id_num, note=None):
    """
    program has been interrupted
    :param id_num: 
    :param note:
    :return: 
    """
    return station_err(id_num, 1, note)


def connect_server_err(id_num, note=None):
    """
    can not connect to server
    :param id_num: 
    :param note:
    :return: 
    """
    return station_err(id_num, 2, note)


def server_return_err(id_num, note=None):
    """
    server return infomation is not in expect
    :param id_num: 
    :param note:
    :return: 
    """
    return station_err(id_num, 3, note)


def db_commit_err(id_num, note=None):
    """
    database commit operation failed
    :param id_num: 
    :param note: 
    :return: 
    """
    return station_err(id_num, 4, note)


def ntpdate_err(id_num, note):
    return station_err(id_num, 5, note)

