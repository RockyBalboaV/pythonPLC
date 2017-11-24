# coding=utf-8
import os
import sys
import time
import argparse
import subprocess

import configparser

# 命令行选项
parser = argparse.ArgumentParser()
parser.add_argument('--reset', action='store_true')
parser.add_argument('--start', action='store_true')
parser.add_argument('--config')
parser.add_argument('--url')
args = parser.parse_args()

os.environ['env'] = 'dev'
os.environ['url'] = 'dev-server'

if args.config == 'prod':
    os.environ['env'] = 'prod'

if args.url == 'server':
    os.environ['url'] = 'server'

from app import first_running, database_reset, app
from param import cf, here

python_path = cf.get(os.environ.get('env'), 'python')

if args.reset:
    database_reset()

if args.start:
    first_running()

    # 清空上次运行的残留数据
    if os.path.exists(here + '/celerybeat-schedule'):
        delete_schedule = subprocess.call('rm {}/celerybeat-schedule'.format(here), shell=True)

    # 启动flower
    flower = subprocess.Popen('{}flower --broker="{}"'.format(python_path, app.conf['broker_url']), shell=True)

    # 启动celery beat worker
    celery = subprocess.call('{}celery -B -A app worker -l warn'.format(python_path), shell=True)

    # 关闭flower
    flower.kill()
