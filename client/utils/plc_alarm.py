import time
import logging

from sqlalchemy.exc import IntegrityError
from snap7.snap7exceptions import Snap7Exception

from models import Session, PLCAlarm


class Snap7ConnectException(Snap7Exception):
    pass


class Snap7ReadException(Snap7Exception):
    pass


def plc_err(id_num, plc_id, code, note):
    session = Session()
    try:
        alarm = PLCAlarm(
            id_num=id_num,
            plc_id=plc_id,
            time=int(time.time()),
            code=code,
            note=note
        )
        session.add(alarm)
    except IntegrityError as e:
        logging.warning('alarm db commit err' + str(e))
    finally:
        session.close()


def connect_plc_err(id_num, plc_id=None, note=None):
    """
    无法连接到PLC
    :param id_num: 
    :param plc_id: 
    :param note: 
    """
    plc_err(id_num, plc_id, 1, note)


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
    """
    note = '读取错误： "plc_id:{}, plc_name: {}, area:{}, db_num:{}, address:{}, data_type:{}".'.format(
        plc_id, plc_name, area, db_num, address, data_type),
    plc_err(id_num, plc_id, 2, note)
