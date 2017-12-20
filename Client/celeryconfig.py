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
# Worker最大累积任务数
# worker_max_tasks_per_child = 5
# 任务默认执行速度
task_default_rate_limit = '1/s'
# task_time_limit = 30
# task_soft_time_limit = 20
# worker_disable_rate_limits = True
# broker最大连接数
broker_pool_limit = 100

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
        'task': 'tasks.check_gather',
        'schedule': 1,
        'relative': True,
        # options可用参数基于apply_async()
        'options': {
            'queue': 'gather'
            # 'expires': 5
        }
    },
    'ntpdate': {
        'task': 'tasks.ntpdate',
        # 每天凌晨执行
        'schedule': crontab(minute=0, hour=0),
        'options': {
            'queue': 'basic'
        }
    },
    'db_clean': {
        'task': 'tasks.db_clean',
        'schedule': crontab(minute=0, hour=0),
        'options': {
            'queue': 'basic'
        }
    },
    'check_alarm': {
        'task': 'tasks.check_alarm',
        'schedule': 5,
        'options': {
            'queue': 'check'
        }
    },
    'beats': {
        'task': 'tasks.beats',
        'schedule': 10,
        'options': {
            'queue': 'check'
        }
    },
    'check_upload': {
        'task': 'tasks.check_upload',
        'schedule': 5,
        'options': {
            'queue': 'upload'
            # 'expires': 15
        }
    },
    'self_check': {
        'task': 'tasks.self_check',
        'schedule': 300,
        'options': {
            'queue': 'basic'
        }
    },
}

# 任务消费速率
task_annotations = {
    'tasks.check_gather': {'rate_limit': '60/m'},
    'tasks.ntpdate': {'rate_limit': '1/h'},
    'tasks.db_clean': {'rate_limit': '1/h'},
    'tasks.check_upload': {'rate_limit': '12/m'},
    'tasks.check_alarm': {'rate_limit': '12/m'},
    'tasks.self_check': {'rate_limit': '12/h'},
    'tasks.beats': {'rate_limit': '6/m'}
}
