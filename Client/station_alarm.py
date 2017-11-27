import time
from models import (StationAlarm)


def station_err(id_num, code):
    alarm = StationAlarm(
        id_num=id_num,
        code=code,
        time=int(time.time())
    )
    return alarm


def check_time_err(id_num):
    """
    program has been interrupted
    :param id_num: 
    :return: 
    """
    return station_err(id_num, 1)


def connect_server_err(id_num):
    """
    can not connect to server
    :param id_num: 
    :return: 
    """
    return station_err(id_num, 2)


def server_return_err(id_num):
    """
    server return infomation is not in expect
    :param id_num: 
    :return: 
    """
    return station_err(id_num, 3)
