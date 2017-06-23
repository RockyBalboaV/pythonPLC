import os

from flask import Flask
from flask_script import Manager, Server
from flask_migrate import Migrate, MigrateCommand

from web_server import create_app
from web_server.models import *
from web_server.ext import db, socketio

env = os.environ.get('WEBAPP_ENV', 'dev')
app = create_app('web_server.config.{}Config'.format(env.capitalize()))

migrate = Migrate(app, db)
manager = Manager(app)
manager.add_command('db', MigrateCommand)
manager.add_command('server', Server(port=11000))


@manager.shell
def make_shell_context():
    return dict(app=app, db=db)
# def Server():
#     socketio.run(app, host='0.0.0.0', port=11000, debug=True)

if __name__ == "__main__":
    manager.run()
