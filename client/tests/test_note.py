# coding=u8
import logging
import datetime

# 日志
# logging.basicConfig(filename='logger.log', level=logging.INFO)
logging.basicConfig(level=logging.INFO)
logging.getLogger(__name__).addHandler(logging.NullHandler())

now = datetime.datetime.now()

logging.info('测试info {}'.format(now).encode())
logging.warning('测试warning'.encode())
logging.error('测试error'.encode())
logging.critical('测试critical'.encode())
