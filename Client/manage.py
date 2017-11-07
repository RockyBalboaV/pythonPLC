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

here = os.path.abspath(os.path.dirname(__file__))
sys.path.append(here)

# 根据环境变量选择配置,或者启动时添加参数
os.environ['pythonoptimize'] = '1'

os.environ['env'] = 'dev'
os.environ['url'] = 'dev-server'

if args.config == 'prod':
    os.environ['env'] = 'prod'

if args.url == 'server':
    os.environ['url'] = 'server'


# 获取配置信息
cf = configparser.ConfigParser()
cf.read_file(open(os.path.join(here, 'config.ini'), encoding='utf-8'))
python_path = cf.get(os.environ.get('env'), 'python')
db_uri = cf.get(os.environ.get('env'), 'db_uri')

# app中import了model，model创建时需要获取mysql数据地址，地址根据环境变量从ini文件中读取，导入app放在输入环境变量后
from app import database_reset, first_running, app

if args.reset:
    database_reset()

if args.start:
    first_running()

    # 清空上次运行的残留数据
    delete_schedule = subprocess.call('rm {}/celerybeat-schedule.*'.format(here), shell=True)

    # 启动flower
    flower = subprocess.Popen('{}flower --broker="{}"'.format(python_path, app.conf['broker_url']), shell=True)

    # 启动celery beat worker
    celery = subprocess.call('{}celery -B -A app worker -l warn'.format(python_path), shell=True)

    # 关闭flower
    flower.kill()
