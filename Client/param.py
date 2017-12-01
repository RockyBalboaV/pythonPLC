import os
import sys

import configparser

here = os.path.abspath(os.path.dirname(__file__))
sys.path.append(here)

# 根据环境变量选择配置,或者启动时添加参数
os.environ['pythonoptimize'] = '1'

# 获取配置信息
cf = configparser.ConfigParser()
cf.read_file(open(os.path.join(here, 'config.ini'), encoding='utf-8'))

# 从配置表中读取通用变量
ID_NUM = cf.get('client', 'id_num')
DB_URI = cf.get(os.environ.get('env'), 'db_uri')
BEAT_URL = cf.get(os.environ.get('url'), 'beat_url')
CONFIG_URL = cf.get(os.environ.get('url'), 'config_url')
UPLOAD_URL = cf.get(os.environ.get('url'), 'upload_url')
CONFIRM_CONFIG_URL = cf.get(os.environ.get('url'), 'confirm_config_url')
CONNECT_TIMEOUT = float(cf.get('client', 'connect_timeout'))
REQUEST_TIMEOUT = float(cf.get('client', 'request_timeout'))
MAX_RETRIES = int(cf.get('client', 'max_retries'))
CHECK_DELAY = int(cf.get('client', 'check_delay'))
SERVER_TIMEOUT = int(cf.get('client', 'server_timeout'))
PLC_TIMEOUT = int(cf.get('client', 'plc_timeout'))
START_TIMEDELTA = int(cf.get('client', 'START_TIMEDELTA'))
NTP_SERVER = cf.get('client', 'NTP_SERVER')
