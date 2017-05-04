# coding=utf-8
from datetime import timedelta

# 指定消息代理
BROKER_URL = 'pyamqp://pyplc:123456@localhost:5672/pyplc'
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
# 定时任务
CELERYBEAT_SCHEDULE = {
    'beats': {
        'task': 'app.beats',
        'schedule': timedelta(seconds=5),
    },
    'fake_data': {
        'task': 'app.fake_data',
        'schedule': timedelta(seconds=999)
    },
    'check_group_upload_time': {
        'task': 'app.check_group_upload_time',
        'schedule': timedelta(seconds=1)
    },
    'check_variable_get_time': {
        'task': 'app.check_variable_get_time',
        'schedule': timedelta(seconds=1)
    }

}