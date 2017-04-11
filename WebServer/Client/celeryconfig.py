# coding=utf-8
from datetime import timedelta

# 指定消息代理
BROKER_URL = 'pyamqp://yakumo17s:123456@localhost:5672/web_develop'
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

CELERYBEAT_SCHEDULE = {
    '__test__beats': {
        'task': 'app.__test__beats',
        'schedule': timedelta(seconds=15),
    }
}