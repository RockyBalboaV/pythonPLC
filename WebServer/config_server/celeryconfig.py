# coding=utf-8
from kombu import Queue
from datetime import timedelta

# 指定消息代理
BROKER_URL = 'pyamqp://yakumo17s:touhou@localhost:5672/web_develop'
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
# 定义任务队列
# CELERY_QUEUES = (
#     Queue('default', routing_key='task.#'),
#     Queue('web_tasks', routing_key='web.#'),
# )
# CELERY_DEFAULT_EXCHANGE = 'tasks'
# CELERY_DEFAULT_EXCHANGE_TYPE = 'topic'
# CELERY_DEFAULT_ROUTING_KEY = 'task.default'
#
# CELERY_ROUTES ={
#     'WebServer.tasks.add': {
#         'queue': 'web_tasks',
#         'routing_key': 'web.add',
#     },
#     'WebServer.tasks.div': {
#         'queue': 'web_tasks',
#         'routing_key': 'web.div'
#     }
#
# }
CELERYBEAT_SCHEDULE = {
    'station_check': {
        'task': 'app.station_check',
        'schedule': timedelta(seconds=5),
    }
}
