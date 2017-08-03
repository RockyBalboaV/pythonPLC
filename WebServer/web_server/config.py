# coding=utf-8
from datetime import timedelta
import tempfile

from celery.schedules import crontab


class Config(object):
    # 终端连接超时
    STATION_TIMEOUT = 60

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # csrf secret key
    SECRET_KEY = 'yakumo17s'

    # flask-cache
    CACHE_TYPE = 'redis'
    CACHE_REDIS_HOST = 'localhost'
    CACHE_REDIS_PORT = '6379'
    # CACHE_REDIS_PASSWORD = 'password'
    CACHE_REDIS_DB = 0

    # flask-restful
    BUNDLE_ERRORS = True

    # flask-debugtoolbar
    DEBUG_TB_INTERCEPT_REDIRECTS = False
    DEBUG_TB_PROFILER_ENABLED = True
    DEBUG_TB_TEMPLATE_EDITOR_ENABLED = True

    # wtform
    WTF_CSRF_CHECK_DEFAULT = True

    # 指定结果存储数据库
    CELERY_BACKEND_URL = 'redis://localhost'
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
        'check_station': {
            'task': 'web_server.tasks.check_station',
            'schedule': timedelta(seconds=10),
        }
    }


# crontab(minute=0) +

class DevConfig(Config):
    # database
    SQLALCHEMY_DATABASE_URI = 'mysql://web:web@localhost:3306/pyplc'

    # 指定消息代理
    CELERY_BROKER_URL = 'pyamqp://yakumo17s:123456@localhost:5672/web_develop'

    # 开启调试模式
    DEBUG = True


class ProdConfig(Config):
    SQLALCHEMY_DATABASE_URI = 'mysql://web:web@localhost:3306/pythonPLC'

    # 指定消息代理
    CELERY_BROKER_URL = 'pyamqp://yakumo17s:touhou@localhost:5672/web_develop'


class TestConfig(Config):
    db_file = tempfile.NamedTemporaryFile()

    DEBUG = True
    DEBUG_TB_ENABLED = False

    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + db_file.name

    CACHE_TyPE = 'null'
    WTF_CSRF_ENABLED = False

    CELERY_BROKER_URL = 'pyamqp://yakumo17s:123456@localhost:5672/web_develop'
    CELERY_BACKEND_URL = 'pyamqp://yakumo17s:123456@localhost:5672/web_develop'

    CELERYBEAT_SCHEDULE = {
        'test': {
            'task': 'web_server.tasks.test',
            'schedule': timedelta(seconds=5),
            'args': ("It's test",)
        }
    }
