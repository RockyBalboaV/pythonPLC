# coding=utf-8
from datetime import timedelta

from kombu import Queue

# 指定消息代理
broker_url = 'pyamqp://pyplc:123456@localhost:5672/pyplc'
# broker_url = 'pyamqp://yakumo17s:touhou@localhost:5672/pyplc'
# 指定结果存储数据库
result_backend = 'redis://localhost'
# 序列化方案
task_serializer = 'msgpack'
# 任务结果读取格式
result_serializer = 'json'
# 任务过期时间
result_expires = 60 * 60 * 24
# 可接受的内容格式
accept_content = ['json', 'msgpack']
# 设置时区
timezone = 'Asia/Shanghai'
# worker并发数
worker_concurrency = 2
# 忽略任务执行状态
task_ignore_result = True
# Worker任务数
worker_max_tasks_per_child = 40

CELERY_QUEUE = (
    Queue('basic', routing_key='basic.#'),
    Queue('check', routing_key='check.#'),
)
task_default_exchange = 'basic'
task_default_exchange_type = 'topic'
task_default_routing_key = 'basic.default'

task_routes = {
    'app.tasks.ntpdate': {
        'queue': 'basic',
        'routing_key': 'basic.ntpdate'
    },
    'app.tasks.check_alarm': {
        'queue': 'check',
        'routing_key': 'check.check_alarm'
    }
}

# 定时任务
beat_schedule = {
    'ntpdate': {
        'task': 'app.ntpdate',
        'schedule': timedelta(seconds=10)
    },
    'check_alarm': {
        'task': 'app.check_alarm',
        'schedule': timedelta(seconds=5)
    }
}

# 任务速率
task_annotations = {
    'app.ntpdate': {'rate_limit': '6/m'}
}

"""
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
        'app.tasks.self_check': {
            'queue': 'check',
            'routing_key': 'check.self_check',
        },
        'app.tasks.server_confirm': {
            'queue': 'basic',
            'routing_key': 'basic.server_confirm'
        },
        
        'beats': {
            'task': 'app.beats',
            'schedule': timedelta(seconds=60),
        },
        'check_group_upload_time': {
            'task': 'app.check_group_upload_time',
            'schedule': timedelta(seconds=5)
        },
        'check_variable_get_time': {
            'task': 'app.check_variable_get_time',
            'schedule': timedelta(seconds=1)
        },
        'self_check': {
            'task': 'app.self_check',
            'schedule': timedelta(seconds=30)
        },
        """