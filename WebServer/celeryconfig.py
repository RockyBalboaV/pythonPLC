# coding=utf-8

BROKER_URL = 'pyamqp://yakumo17s:123456@localhost:5672/web_develop'
CELERY_RESULT_BACKEND = 'redis://localhost'
CELERY_TASK_SERIALIZER = 'msgpack'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TASK_RESULT_EXPIRES = 60 * 60 * 24
CELERY_ACCEPT_CONTENT = ['json', 'msgpack']