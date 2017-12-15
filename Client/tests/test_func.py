import os
import subprocess
import getpass
import requests
import time
import json
import psutil

import pytest

os.environ['env'] = 'dev'
os.environ['url'] = 'server'
# os.environ['url'] = 'dev-server'

from task import r, server_confirm, get_config, beats, before_running, boot, check_alarm, redis_alarm_variables, \
    ntpdate, db_clean
from utils.station_data import station_info, beats_data
from util import encryption_client, decryption_client
from data_collection import analog2digital
from param import CONFIRM_CONFIG_URL
from models import session
from tests.test_data import post_data

import sys
# print(sys.path)

class TestFunc:
    @pytest.mark.skip
    def ntpdate(self):
        ntpdate()

    @pytest.mark.skip
    def test_badblock(self):
        cmd = 'sudo badblocks -v /dev/mmcblk0p2'
        proc = subprocess.Popen(
            cmd,
            shell=True,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        stdout, stderr = proc.communicate()
        print(stdout.decode('utf-8'), '**', stderr.decode('utf-8'))

    # @pytest.mark.skip
    def test_encryption_decryption(self):
        time1 = time.time()
        data = encryption_client(post_data)
        time2 = time.time()
        str_data = json.dumps(post_data)
        print('压缩数据量', len(str_data))
        print('压缩时间', time2 - time1)

        rp = requests.post('http://127.0.0.1:11000/client/test', data=data)
        assert rp.status_code == 200

        print(len(rp.content))

        time1 = time.time()
        data = decryption_client(rp.content)
        time2 = time.time()
        print(time2 - time1)

        str_data = json.dumps(data)
        print('解压数据量', len(str_data))
        print('解压时间', time2 - time1)

        assert data == post_data

    def test_analog2digital(self):
        analog_low_range = 0
        analog_high_range = 30000
        digital_low_range = 0
        digital_high_range = 100

        raw_value = 15000
        value = analog2digital(raw_value, analog_low_range, analog_high_range, digital_low_range, digital_high_range)

        assert int(value) == 50

        raw_value = 10000
        value = analog2digital(raw_value, analog_low_range, analog_high_range, digital_low_range, digital_high_range)

        assert round(value, 1) == 33.3

    def test_sys_info(self):
        station_info()

    def test_beats(self):
        beats()

    def test_beats_data(self):
        id_num = r.get('id_num')
        con_time = r.get('con_time')
        current_time = int(time.time())
        print(beats_data(id_num, con_time, current_time))

    def test_before_running(self):
        before_running()
        print(r.get('id_num'))
        print(r.get('plc'))
        print(r.get('group_upload'))
        print(r.get('group_read'))
        print(r.get('variable'))

    def test_check_alarm(self):
        check_alarm()

    def test_confirm_config(self):
        assert server_confirm(CONFIRM_CONFIG_URL)

    def test_db_clean(self):
        db_clean()


class TestTask(object):
    def test_get_config(self):
        get_config()


