# coding=utf-8
from datetime import timedelta
from celery.schedules import crontab
from kombu import Queue, Exchange

# 指定消息代理
broker_url = 'pyamqp://yakumo17s:touhou@localhost:5672/pyplc'
# 指定结果存储数据库
result_backend = 'redis://localhost'
# 序列化方案
task_serializer = 'msgpack'
# 任务结果读取格式
result_serializer = 'json'
# 任务过期时间
result_expires = 60
# 可接受的内容格式
accept_content = ['json', 'msgpack']
# 设置时区
timezone = 'Asia/Shanghai'
# worker并发数
worker_concurrency = 4
# 忽略任务执行状态
task_ignore_result = True
# Worker任务数
worker_max_tasks_per_child = 20
# 任务默认执行速度
task_default_rate_limit = '1/s'
# worker_disable_rate_limits = True

task_queues = (
    Queue('basic', Exchange('basic', type='topic'), routing_key='basic.#'),
    Queue('check', Exchange('check', type='direct'), routing_key='check.#'),
    Queue('var', Exchange('var', type='direct'), routing_key='var'),
    Queue('upload', Exchange('upload', type='direct'), routing_key='upload')
)

task_default_exchange = 'basic'
task_default_exchange_type = 'topic'
task_default_routing_key = 'basic.default'

task_routes = {
    'app.tasks.ntpdate': {
        'queue': 'basic',
        'routing_key': 'basic.ntpdate'
    },
    'app.tasks.db_clean': {
        'queue': 'basic',
        'routing_key': 'basic.db_clean'
    },
    'app.tasks.check_alarm': {
        'queue': 'check',
        'routing_key': 'check.alarm'
    },
    'app.tasks.get_config': {
        'queue': 'basic',
        'routing_key': 'basic.get_config',
    },
    'app.tasks.beats': {
        'queue': 'check',
        'routing_key': 'check.beats',
    },
    'app.tasks.check_group_upload_time': {
        'queue': 'upload',
        'routing_key': 'upload',
    },
    'app.tasks.check_variable_get_time': {
        'queue': 'var',
        'routing_key': 'var',
    },
    'app.tasks.self_check': {
        'queue': 'check',
        'routing_key': 'check.self_check',
    },
}

# 定时任务
beat_schedule = {
    'ntpdate': {
        'task': 'task.ntpdate',
        # 每天凌晨执行
        'schedule': crontab(minute=0, hour=0),
        # 'schedule': timedelta(seconds=10),
        'options': {
            'queue': 'basic'
        }
    },
    'db_clean': {
        'task': 'task.db_clean',
        'schedule': crontab(minute=0, hour=0),
        'options': {
            'queue': 'basic'
        }
    },
    'check_alarm': {
        'task': 'task.check_alarm',
        'schedule': timedelta(seconds=6),
        'options': {
            'queue': 'check'
        }
    },
    'beats': {
        'task': 'task.beats',
        'schedule': timedelta(seconds=6),
        'options': {
            'queue': 'check'
        }
    },
    'check_group_upload_time': {
        'task': 'task.check_group_upload_time',
        'schedule': timedelta(seconds=5),
        'options': {
            'queue': 'upload'
        }
    },
    'check_variable_get_time': {
        'task': 'task.check_variable_get_time',
        'schedule': timedelta(seconds=1),
        'options': {
            'queue': 'var'
        }
    },
    'self_check': {
        'task': 'task.self_check',
        'schedule': timedelta(seconds=300),
        'options': {
            'queue': 'basic'
        }
    },
}

# 任务消费速率
task_annotations = {
    'task.ntpdate': {'rate_limit': '1/h'},
    'task.db_clean': {'rate_limit': '1/h'},
    'task.check_group_upload_time': {'rate_limit': '12/m'},
    'task.check_variable_get_time': {'rate_limit': '60/m'},
    'task.check_alarm': {'rate_limit': '12/m'},
    'task.self_check': {'rate_limit': '12/h'},
    'task.beats': {'rate_limit': '6/m'}
}
