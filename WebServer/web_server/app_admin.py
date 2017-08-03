import os

from flask import Flask, redirect, url_for
from flask_admin import Admin
from flask_login import (current_user, UserMixin, LoginManager,
                         login_user, logout_user)
from flask_admin.contrib.sqla import ModelView
from flask_admin.contrib.fileadmin import FileAdmin
from flask_admin.base import MenuLink, BaseView, expose

from ext import db
from models import User as _User

app = Flask(__name__, template_folder='templates', static_folder='static')
here = os.path.abspath(os.path.dirname(__file__))
app.config.from_pyfile(os.path.join(here, 'config_dev/config.py'))

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)


class User(_User, UserMixin):
    pass


USERNAME = 'xiaoming'


@app.route('/')
def index():
    return '<a href="/admin/">go to admin</a>'


@app.route('/login/')
def login_view():
    user = User.query.filter_by(name=USERNAME).first()
    login_user(user)
    return redirect(url_for('admin.index'))


@app.route('/logout/')
def logout_view():
    login_user()
    return redirect(url_for('admin.index'))


class AuthenticatedMenuLink(MenuLink):
    def is_accessible(self):
        return current_user.is_authenticated


class NotAuthenticatedMenuLink(MenuLink):
    def is_accessible(self):
        return not current_user.is_authenticated


admin = Admin(app, name='web_develop', template_mode='bootstrap3')
admin.add_link(NotAuthenticatedMenuLink(name='Login', endpoint='login_view'))
admin.add_link(AuthenticatedMenuLink(name='Logout', endpoint='logout_view'))


class MyAdminView(BaseView):
    @expose('/')
    def index(self):
        return self.render('authenticated-admin.html')

    def is_accessible(self):
        return current_user.is_authenticated


admin.add_view(ModelView(User, db.session))

path = os.path.join(os.path.dirname(__file__), 'static')
admin.add_view(FileAdmin(path, '/static/', name='Static Files'))

admin.add_view(MyAdminView(name='Authenticated'))

if __name__ == '__main__':
    app.run()
