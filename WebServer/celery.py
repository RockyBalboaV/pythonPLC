from __future__ import absolute_import

from celery import Celery

app = Celery('WebServer', include=['WebServer.tasks'])
app.config_from_object('WebServer.celeryconfig')


if __name__ == '__main__':
    app.start()