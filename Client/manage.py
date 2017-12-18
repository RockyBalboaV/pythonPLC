# coding=utf-8
import os
import sys
import argparse
import subprocess
import psutil


os.environ['env'] = 'dev'
os.environ['url'] = 'dev-server'

here = os.getcwd()
python_path = sys.executable


def clean_up():
    # 清除未关闭的worker和beat
    close_celery = ['pkill', '-9', '-f', 'celery']
    # 清除未关闭的flower
    close_flower = ['pkill', '-9', '-f', 'flower']
    # 清除已发布的任务
    purge_task = [python_path, '-m', 'celery', 'purge', '-A', 'tasks', '-f']

    process_list = [close_celery, close_flower, purge_task]

    for process in process_list:
        subprocess.call(process)

    # 删除临时文件
    schedule_file = os.path.join(here, 'celerybeat-schedule')
    beat_file = os.path.join(here, 'celerybeat.pid')

    file_list = [schedule_file, beat_file, schedule_file]

    for file in file_list:
        if os.path.exists(file):
            subprocess.call(['rm', file])


# 命令行选项
parser = argparse.ArgumentParser()
# 重置数据库
parser.add_argument('--reset', action='store_true')
# 运行
parser.add_argument('-r', '--run', action='store_true')
# 清空已发布任务
parser.add_argument('-c', '--clean', action='store_true')
# 清空流量记录缓存
parser.add_argument('-n', '--clean-net-cache', action='store_true')
# 开启flower调试
parser.add_argument('-f', '--flower', action='store_true')
# 运行环境
parser.add_argument('-e', '--env')
# 服务器地址
parser.add_argument('-s', '--server')
args = parser.parse_args()

if args.env == 'prod':
    os.environ['env'] = 'prod'

if args.server == 'server':
    os.environ['url'] = 'server'

# import tasks
from utils.station_func import boot, before_running, database_reset
from utils.server_connect import get_config


if args.clean:
    clean_up()

if args.reset:
    database_reset()

if args.clean_net_cache:
    psutil.net_io_counters.cache_clear()

if args.flower:
    # 启动flower
    flower = subprocess.Popen([python_path, '-m', 'flower'])

if args.run:
    boot()
    get_config()
    before_running()

    # 启动celery beat worker
    try:
        worker = subprocess.Popen(
            '{0} -m celery -A tasks worker -P eventlet -c 10 -l warn -E  -n worker@%h'.format(
                python_path),
            shell=True)
        beat = subprocess.call([python_path, '-m', 'celery', 'beat', '-A', 'tasks'])

    except KeyboardInterrupt:
        print('Interrupted')
    finally:
        # close_celery = ['pkill', '-9', '-f', 'celery']
        clean_up()
