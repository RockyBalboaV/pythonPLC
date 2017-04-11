# coding=utf-8
from __future__ import absolute_import

from celery import Celery

app = Celery('Web2', include=['Web2.tasks'])
app.config_from_object('Web2.celeryconfig')


if __name__ == '__main__':
    app.start()