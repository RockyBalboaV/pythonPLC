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

mako = MakoTemplates()
db = SQLAlchemy()
hashing = Hashing()
admin = Admin()
csrf = CSRFProtect()
api = Api(decorators=[csrf.exempt])  # decorators参数，给所有api的url加上装饰器，免于csrf检查
cache = Cache()
debug_toolbar = DebugToolbarExtension()


principlas = Principal()
admin_permission = Permission(RoleNeed('admin'))

login_manager = LoginManager()
login_manager.login_view = "login"
login_manager.session_protection = "strong"
login_manager.login_message = "Please login to access this page"
login_manager.login_message_category = "info"


