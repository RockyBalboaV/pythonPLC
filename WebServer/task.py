from __future__ import absolute_import

from WebServer.celery import app


@app.task()