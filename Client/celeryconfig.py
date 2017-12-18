# coding=utf-8
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
result_expires = 10
# 可接受的内容格式
accept_content = ['json', 'msgpack']
# 设置时区
timezone = 'Asia/Shanghai'
# worker并发数
worker_concurrency = 4
# 忽略任务执行状态
task_ignore_result = True
# Worker任务数
# worker_max_tasks_per_child = 10
# 任务默认执行速度
task_default_rate_limit = '1/s'
# worker_disable_rate_limits = True
broker_pool_limit = 0

task_queues = (
    Queue('basic', Exchange('basic', type='topic'), routing_key='basic.#'),
    Queue('check', Exchange('check', type='direct'), routing_key='check.#'),
    Queue('gather', Exchange('var', type='direct'), routing_key='gather'),
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
    'app.tasks.check_upload': {
        'queue': 'upload',
        'routing_key': 'upload',
    },
    'app.tasks.check_gather': {
        'queue': 'gather',
        'routing_key': 'gather',
    },
    'app.tasks.self_check': {
        'queue': 'check',
        'routing_key': 'check.self_check',
    },
}

# 定时任务
beat_schedule = {
    'check_gather': {
        'task': 'task.check_gather',
        'schedule': 1,
        'options': {
            'queue': 'gather'
        }
    },
    'ntpdate': {
        'task': 'task.ntpdate',
        # 每天凌晨执行
        'schedule': crontab(minute=0, hour=0),
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
        'schedule': 5,
        'options': {
            'queue': 'check'
        }
    },
    'beats': {
        'task': 'task.beats',
        'schedule': 10,
        'options': {
            'queue': 'check'
        }
    },
    'check_upload': {
        'task': 'task.check_upload',
        'schedule': 5,
        'options': {
            'queue': 'upload'
        }
    },
    'self_check': {
        'task': 'task.self_check',
        'schedule': 300,
        'options': {
            'queue': 'basic'
        }
    },
}

# 任务消费速率
task_annotations = {
    'task.check_gather': {'rate_limit': '60/m'},
    'task.ntpdate': {'rate_limit': '1/h'},
    'task.db_clean': {'rate_limit': '1/h'},
    'task.check_upload': {'rate_limit': '12/m'},
    'task.check_alarm': {'rate_limit': '12/m'},
    'task.self_check': {'rate_limit': '12/h'},
    'task.beats': {'rate_limit': '6/m'}
}
