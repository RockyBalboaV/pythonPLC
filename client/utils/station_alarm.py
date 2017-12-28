import time
import logging

from sqlalchemy.exc import IntegrityError

from models import Session, StationAlarm


def station_err(id_num, code, note):
    session = Session()
    try:
        alarm = StationAlarm(
            id_num=id_num,
            code=code,
            time=int(time.time()),
            note=note
        )
        session.add(alarm)
        session.commit()
    except IntegrityError as e:
        logging.warning('alarm db commit err' + str(e))
    finally:
        session.close()


def check_time_err(id_num, note=None):
    """
    program has been interrupted
    :param id_num: 
    :param note:
    """
    station_err(id_num, 1, note)


def connect_server_err(id_num, note=None):
    """
    can not connect to server
    :param id_num: 
    :param note:
    """
    station_err(id_num, 2, note)


def server_return_err(id_num, note=None):
    """
    server return infomation is not in expect
    :param id_num: 
    :param note:
    """
    station_err(id_num, 3, note)


def db_commit_err(id_num, note=None):
    """
    database commit operation failed
    :param id_num: 
    :param note: 
    """
    station_err(id_num, 4, note)


def ntpdate_err(id_num, note):
    station_err(id_num, 5, note)
