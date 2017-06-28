# coding=utf-8
from flask_mako import MakoTemplates
from flask_sqlalchemy import SQLAlchemy
from flask_hashing import Hashing
from flask_restful import Api
from flask_admin import Admin
from flask_principal import Principal, Permission, RoleNeed
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from flask_cache import Cache
from flask_debugtoolbar import DebugToolbarExtension
from flask_socketio import SocketIO
from flask_celery import Celery

mako = MakoTemplates()
db = SQLAlchemy()
hashing = Hashing()
admin = Admin()
csrf = CSRFProtect()
api = Api(decorators=[csrf.exempt])  # decorators参数，给所有api的url加上装饰器，免于csrf检查
cache = Cache()
debug_toolbar = DebugToolbarExtension()
socketio = SocketIO()
celery = Celery()

principlas = Principal()
admin_permission = Permission(RoleNeed('admin'))
user_permission = Permission(RoleNeed('user'))

login_manager = LoginManager()
login_manager.login_view = "login"
login_manager.session_protection = "basic"
login_manager.login_message = u"需要登录才能进入"
login_manager.login_message_category = "warning"


