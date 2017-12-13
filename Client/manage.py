# coding=utf-8
import os
import argparse
import subprocess
import psutil
import sys

# 命令行选项
parser = argparse.ArgumentParser()
# 重置数据库
parser.add_argument('--reset', action='store_true')
# 运行
parser.add_argument('--start', action='store_true')
# 清空已发布任务
parser.add_argument('--clean-beat', action='store_true')
# 清空流量记录缓存
parser.add_argument('--clean-net-cache', action='store_true')
# 运行环境
parser.add_argument('--config')
# 服务器地址
parser.add_argument('--url')
args = parser.parse_args()

os.environ['env'] = 'dev'
os.environ['url'] = 'dev-server'

if args.config == 'prod':
    os.environ['env'] = 'prod'

if args.url == 'server':
    os.environ['url'] = 'server'

from app import boot, database_reset, app, get_config, before_running
from param import cf, here

python_path = sys.executable

if args.reset:
    database_reset()

if args.clean_beat:
    subprocess.call('{} -m celery purge -A app -f'.format(python_path), shell=True)

if args.clean_net_cache:
    psutil.net_io_counters.cache_clear()

if args.start:
    # 清空上次运行的残留数据
    # 清除已发布的任务
    # subprocess.call('celery purge -A app -f', shell=True)
    subprocess.call([python_path, '-m', 'celery', 'purge', '-A', 'app', '-f'])

    # 清除未关闭的celery
    subprocess.call('pkill -9 -f "celery"', shell=True)

    if os.path.exists(here + '/celerybeat-schedule'):
        delete_schedule = subprocess.call('rm {}/celerybeat-schedule'.format(here), shell=True)

    boot()

    get_config()

    before_running()

    # 启动flower
    flower = subprocess.Popen([python_path, '-m', 'flower', '--broker=', app.conf['broker_url']])

    # 启动celery beat worker
    celery = subprocess.call('{} -m celery -B -A app worker -l warn -E --autoscale=4,2 --concurrency=5 -n worker@%h'.format(python_path), shell=True)

    # 关闭flower
    flower.kill()
