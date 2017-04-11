# coding=utf-8
from flask import Flask, render_template
from flask_socketio import SocketIO
from celery import Celery
import os
import time
import eventlet
eventlet.monkey_patch()

app = Flask(__name__)
here = os.path.abspath(os.path.dirname(__file__)) # 获取文件的绝对路径
app.config.from_pyfile(os.path.join(here, 'WebServer/celeryconfig.py'))

SOCKETIO_REDIS_URL = app.config['CELERY_RESULT_BACKEND']
socketio = SocketIO(
    app, async_mode='eventlet',
    message_queue=SOCKETIO_REDIS_URL
)
celery = Celery(app.name)
celery.conf.update(app.config)


@celery.task
def background_task():
    socketio.emit(
        'my response', {'data': 'Task starting ...'},
        namespace='/task')
    time.sleep(1)
    socketio.emit(
        'my response', {'data': 'Task complete!'},
        namespace='/task')

@celery.task
def async_task():
    print 'Async!'
    time.sleep(5)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/async')
def async():
    async_task.delay()
    return 'Task Complete!'


@app.route('/task')
def start_background_task():
    background_task.delay()
    return 'Started'


if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=9000, debug=True)
