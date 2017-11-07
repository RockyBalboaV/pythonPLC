import os
import configparser as ConfigParser

import pytest
import requests

# 获取当前目录位置
here = os.path.abspath(os.path.dirname(__file__))

# 配置环境变量
os.environ['env'] = 'dev'
os.environ['url'] = 'server'

# 读取配置文件
cf = ConfigParser.ConfigParser()
cf.read_file(open(os.path.join(os.path.dirname(here), 'config.ini'), encoding='utf-8'))

# 从配置表中读取通用变量
BEAT_URL = cf.get(os.environ.get('url'), 'beat_url')
CONFIG_URL = cf.get(os.environ.get('url'), 'config_url')
UPLOAD_URL = cf.get(os.environ.get('url'), 'upload_url')
CONNECT_TIMEOUT = float(cf.get('client', 'connect_timeout'))
REQUEST_TIMEOUT = float(cf.get('client', 'request_timeout'))
MAX_RETRIES = int(cf.get('client', 'max_retries'))
CHECK_DELAY = cf.get('client', 'check_delay')
SERVER_TIMEOUT = cf.get('client', 'server_timeout')
PLC_TIMEOUT = cf.get('client', 'plc_timeout')


# test 'http://127.0.0.1:11000/client/upload'

class TestServer():
    def test_upload(self):

        data = {
            'id_num': 'test',
            'version': '1',
            'value': []
        }

        rp = requests.post(url=UPLOAD_URL, json=data)
        assert rp.status_code == 200
        print(rp, rp.content)
        print(rp.json())


