from contextlib import contextmanager
import logging

import snap7
from snap7.snap7exceptions import Snap7Exception



@contextmanager
def plc_client(ip, rack, slot):
    """
    建立plc连接的上下文管理器
    :param ip: 
    :param rack: 
    :param slot: 
    :return: 
    """
    client = snap7.client.Client()
    try:
        client.connect(ip, rack, slot)
    except Snap7Exception as e:
        logging.warning('连接plc失败' + str(e))
    yield client
    client.disconnect()
    client.destroy()
