# coding=utf-8
from datetime import timedelta

from kombu import Queue


class Config(object):
    # 设置终端信息

    # 指定消息代理
    BROKER_URL = 'pyamqp://pyplc:123456@localhost:5672/pyplc'
    # BROKER_URL = 'pyamqp://yakumo17s:touhou@localhost:5672/web_develop'
    # 指定结果存储数据库
    CELERY_RESULT_BACKEND = 'redis://localhost'
    # 序列化方案
    CELERY_TASK_SERIALIZER = 'msgpack'
    # 任务结果读取格式
    CELERY_RESULT_SERIALIZER = 'json'
    # 任务过期时间
    CELERY_TASK_RESULT_EXPIRES = 60 * 60 * 24
    # 可接受的内容格式
    CELERY_ACCEPT_CONTENT = ['json', 'msgpack']
    # 设置时区
    CELERY_TIMEZONE = 'Asia/Shanghai'
    # worker并发数
    CELERYD_CONCURRENCY = 1
    # 忽略任务执行状态
    CELERY_IGNORE_RESULT = True
    # Worker任务数
    CELERY_MAX_TASKS_PER_CHILD = 40

    CELERY_QUEUE = (
        Queue('basic', routing_key='basic.#'),
        Queue('check', routing_key='check.#')
    )
    CELERY_DEFAULT_EXCHANGE = 'basic'
    CELERY_DEFAULT_EXCHANGE_TYPE = 'topic'
    CELERY_DEFAULT_ROUTING_KEY = 'basic.default'

    CELERY_ROUTES = {
        'app.tasks.get_config': {
            'queue': 'basic',
            'routing_key': 'basic.get_config',
        },
        'app.tasks.beats': {
            'queue': 'check',
            'routing_key': 'check.beats',
        },
        'app.tasks.check_group_upload_time': {
            'queue': 'check',
            'routing_key': 'check.check_group_upload_time',
        },
        'app.tasks.check_variable_get_time': {
            'queue': 'check',
            'routing_key': 'check.check_variable_get_time',
        },
        'app.tasks.get_value': {
            'queue': 'check',
            'routing_key': 'check.get_value',
        }

    }
    # 定时任务
    CELERYBEAT_SCHEDULE = {
        'beats': {
            'task': 'app.beats',
            'schedule': timedelta(seconds=10),
        },

        'check_group_upload_time': {
            'task': 'app.check_group_upload_time',
            'schedule': timedelta(seconds=3)
        },
        'check_variable_get_time': {
            'task': 'app.check_variable_get_time',
            'schedule': timedelta(seconds=1)
        }

    }


class DevConfig(Config):
    HOSTNAME = '127.0.0.1'
    DATABASE = 'pyplc_client'
    USERNAME = 'client'
    PASSWORD = 'pyplc_client'
    DB_URI = 'mysql://{}:{}@{}/{}'.format(USERNAME, PASSWORD, HOSTNAME, DATABASE)

    # 设置服务器连接地址地址

    BEAT_URL = 'http://104.160.41.99:11000/client/beats'
    CONFIG_URL = 'http://104.160.41.99:11000/client/config'
    UPLOAD_URL = 'http://104.160.41.99:11000/client/upload'

    # BEAT_URL = 'http://127.0.0.1:11000/client/beats'
    # CONFIG_URL = 'http://127.0.0.1:11000/client/config'
    # UPLOAD_URL = 'http://127.0.0.1:11000/client/upload'


class ProdConfig(Config):
    HOSTNAME = '127.0.0.1'
    DATABASE = 'pyplc_client'
    USERNAME = 'root'
    PASSWORD = 'root'
    DB_URI = 'mysql://{}:{}@{}/{}'.format(USERNAME, PASSWORD, HOSTNAME, DATABASE)

    BEAT_URL = 'http://104.160.41.99:11000/client/beats'
    CONFIG_URL = 'http://104.160.41.99:11000/client/config'
    UPLOAD_URL = 'http://104.160.41.99:11000/client/upload'
