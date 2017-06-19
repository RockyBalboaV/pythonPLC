import os

from flask import Flask
from flask_script import Manager
from flask_migrate import Migrate, MigrateCommand

from web_server.ext import db

app = Flask(__name__)
here = os.path.abspath(os.path.dirname(__file__))

if os.path.exists('config_dev'):
    app.config.from_pyfile(os.path.join(here, 'config_dev/config.py'))
    app.config.from_pyfile(os.path.join(here, 'config_dev/celery_config.py'))
else:
    app.config.from_pyfile(os.path.join(here, 'config_server/config.py'))
    app.config.from_pyfile(os.path.join(here, 'config_server/celery_config.py'))

db.init_app(app)
import web_server.models
migrate = Migrate(app, db)
manager = Manager(app)
manager.add_command('db', MigrateCommand)

if __name__ == '__main__':
    manager.run()
