# coding=utf-8

import os
import base64
import hmac
import json
import random
import zlib
import time

import MySQLdb
import eventlet
from celery import Celery
from flask import Flask, request, jsonify, g, render_template, redirect, url_for, current_app, flash, Config, session
from flask import request_tearing_down, appcontext_tearing_down
from flask_security import url_for_security
from flask_login import login_user, logout_user, user_logged_in, login_required, current_user
from flask_socketio import SocketIO
from flask_principal import identity_loaded, identity_changed, UserNeed, RoleNeed, Identity, AnonymousIdentity
from pandas.io.sql import read_sql

from models import *
from ext import mako, hashing, api, admin, login_manager, csrf, cache, debug_toolbar, CSRFProtect, socketio
from forms import RegistrationForm, LoginForm
from config import DevConfig, ProdConfig

from rest.api_plc import PLCResource
from rest.api_station import StationResource
from rest.api_group import GroupResource
from rest.api_variable import VariableResource
from rest.value import ValueResource
from rest.auth import AuthApi

from web_server.admin_view import CustomView, CustomModelView, CustomFileAdmin

# 设置默认编码
# 不用这段会使得jinja渲染flash消息时产生编码错误
import sys

reload(sys)
sys.setdefaultencoding("utf-8")


def create_app(object_name):
    app = Flask(__name__, template_folder='templates')

    # here = os.path.abspath(os.path.dirname(__file__))

    if os.path.exists('dev'):
        app.config.from_object(DevConfig)
    else:
        app.config.from_object(ProdConfig)

    eventlet.monkey_patch()
    mako.init_app(app)
    db.init_app(app)
    hashing.init_app(app)
    admin.init_app(app)
    login_manager.init_app(app)
    # csrf.init_app(app)
    debug_toolbar.init_app(app)
    cache.init_app(app)

    SOCKETIO_REDIS_URL = app.config['CELERY_RESULT_BACKEND']
    socketio.init_app(
        app, async_mode='eventlet',
        message_queue=SOCKETIO_REDIS_URL
    )

    celery = Celery(app.name)
    celery.conf.update(app.config)

    api.add_resource(AuthApi, '/api/auth')
    api.add_resource(StationResource, '/api/station', '/api/station/<station_id>')
    api.add_resource(PLCResource, '/api/plc', '/api/plc/<plc_id>')
    api.add_resource(GroupResource, '/api/group', '/api/group/<group_id>')
    api.add_resource(VariableResource, '/api/variable', '/api/variable/<variable_id>')
    api.add_resource(ValueResource, '/api/value', '/api/value/<value_id>')
    api.init_app(app)

    admin.add_view(CustomView(name='Custom'))
    models = [YjStationInfo, YjPLCInfo, YjGroupInfo, YjVariableInfo, Value, TransferLog, User]
    
    for model in models:
        admin.add_view(
            CustomModelView(model, db.session,
                            category='models')
        )
    admin.add_view(CustomFileAdmin(os.path.join(os.path.dirname(__file__), 'static'),
                                   '/static/',
                                   name='Static File'))

    def value2dict(std):
        return {
            "id": std.id,
            "variable_id": std.variable_id,
            "value": std.value
        }

    def get_current_user():
        return session['username']

    def encryption(data):
        """
        :param data: dict
        :return: dict
        """

        h = hmac.new(b'poree')
        data = unicode(data)
        # data = base64.b64encode(data)
        h.update(bytes(data))
        data = zlib.compress(data)
        data = base64.b64encode(data)
        digest = h.hexdigest()
        data = {"data": data, "digest": digest}
        return data

    def decryption(rj):
        """
        :param rj: json
        :return: dict
        """

        data = rj['data']
        di = rj['digest']
        data = base64.b64decode(data)
        data = zlib.decompress(data)
        h = hmac.new(b'poree')
        h.update(bytes(data))
        test = h.hexdigest()
        if di == test:
            # data = base64.b64decode(data)
            data = json.loads(data.replace("'", '"'))
        else:
            data = {"status": "Error"}
        return data

    def get_data_from_query(models):
        # 输入session.query()查询到的模型实例列表,读取每个实例每个值,放入列表返回
        data_list = []
        for model in models:
            model_column = {}
            for c in model.__table__.columns:
                model_column[c.name] = str(getattr(model, c.name, None))
            data_list.append(model_column)
        return data_list

    def get_data_from_model(model):
        # 读取一个模型实例中的每一项与值，放入字典
        model_column = {}
        for c in model.__table__.columns:
            model_column[c.name] = str(getattr(model, c.name, None))
        return model_column

    @app.errorhandler(500)
    def server_inner_error(error):
        return u"内部代码错误 by yakumo17s"

    @app.before_first_request
    def setup():
        pass


    # 使用flask-login.current_user代替
    # @app.before_request
    # def before_request():
    #     if 'username' in session:
    #         g.current_user = User.query.filter_by(username=session['username']).first()
    #     else:
    #         g.current_user = None


    # @app.teardown_appcontext
    # def teardown(exc=None):
    #     if exc is None:
    #         db.session.commit()
    #     else:
    #         db.session.rollback()
    #     db.session.remove()
    #     g.current_user = None

    # @app.teardown_appcontext

    def close_db_connection(sender, **extra):
        db.session.close()
        # sender.logger.debug('Database close.')


    request_tearing_down.connect(close_db_connection, app)


    @app.context_processor
    def template_extras():
        return {'enumerate': enumerate, 'current_user': current_user}


    @app.template_filter('capitalize')
    def reverse_filter(s):
        return s.capitalize()


    @celery.task
    def station_check():
        with app.app_context():
            current_time = datetime.datetime.now()
            stations = db.session.query(YjStationInfo)
            for s in stations:
                s_log = TransferLog.query.filter_by(idnum=s.idnum).order_by(TransferLog.time.desc()).first()
                if s_log:
                    last_time = s_log.time
                    last_level = s_log.level
                    if (current_time - last_time).seconds > 5 and (current_time - last_time).days == 0:
                        warn_level = last_level + 1
                        if warn_level > 2:
                            warn = TransferLog(id_num=s.idnum, level=3, time=time.mktime(current_time.timetuple()),
                                               note='ERROR')
                        else:
                            warn = TransferLog(id_num=s.idnum, level=last_level + 1,
                                               time=time.mktime(current_time.timetuple()), note='WARNING')
                    else:
                        warn = TransferLog(id_num=s.idnum, level=0, time=time.mktime(current_time.timetuple()), note='OK')
                else:
                    warn = TransferLog(id_num=s.idnum, level=0, time=time.mktime(current_time.timetuple()), note='OK')
                db.session.add(warn)
                db.session.commit()


    @user_logged_in.connect_via(app)
    def _track_logins(sender, user, **extra):
        # 记录用户登录次数，登录IP
        user.login_count += 1
        user.last_login_ip = request.remote_addr
        user.last_login_time = int(time.time())
        db.session.add(user)
        db.session.commit()


    @login_manager.user_loader
    def user_loader(user_id):
        user = User.query.get(user_id)
        return user


    @app.route('/', methods=['GET', 'POST'])
    @cache.cached(timeout=60)
    # @login_required
    def index():
        users = User.query.all()
        return render_template('index.html', users=users)


    @app.route('/signin', methods=['GET', 'POST'])
    def signin():
        form = LoginForm(request.form)
        if request.method == 'GET':
            return render_template('signin.html', form=form)
        print 'a'
        username = request.form['username']
        print username, form.username.data
        password = request.form['password']
        error = 'password error'
        print 'b'
        if len(username) < 5:
            error = 'Username must be at least 6 characters'
        if len(password) < 5:
            error = 'Password must be at least 6 characters'
        # elif not any(c.isupper() for c in password):
        #     error = 'Your password needs at least 1 capital'
        user = User.query.filter_by(username=username).first()

        if not user:
            error = 'user is not exist'
        else:
            if user.check_password(password):
                print 'c'
                print [(a, b) for a, b in request.form.items()]
                print request.form.get('remember')
                login_user(user, remember=request.form.get('remember'))
                print 'b'
                # return redirect(url_for('index'))
                return jsonify({'r': 0, 'rs': 'ok', 'url': url_for('index')})
                # return jsonify({'url': '/login'})
        return jsonify({'r': 1, 'error': error})


    # @app.route('/register', methods=['GET', 'POST'])
    # def register():
    #     form = RegistrationForm(request.form)
    #     if request.method == 'POST' and form.validate_on_submit():
    #         user = User(username=form.username.data, email=form.email.data, password=form.password.data)
    #         db.session.add(user)
    #         db.session.commit()
    #         flash('registering successed!')
    #         return redirect(url_for('login'))
    #     return render_template('register.html', form=form)


    @app.route('/register', methods=['GET', 'POST'])
    @csrf.exempt
    def register():
        if request.method == 'POST':
            user = User(username=request.form.get('username'), password=request.form.get('password'))
            db.session.add(user)
            db.session.commit()
            flash(u'注册成功!', category='success')
            return redirect(url_for('login'))
        return render_template('register_user.html')


    @user_logged_in.connect_via(app)
    def _track_logins(sender, user, **extra):
        # 记录用户登录次数，登录IP
        user.login_count += 1
        user.last_login_ip = request.remote_addr
        user.last_login_time = int(time.time())
        db.session.add(user)
        db.session.commit()


    # @app.route('/login', methods=['GET', 'POST'])
    # def login():
    #     form = LoginForm(request.form)
    #     if request.method == 'GET':
    #         return render_template('login.html', form=form)
    #
    #     # name = request.form.get('name') or form.username.data
    #     # password = request.form.get('pw') or form.password.data
    #     # user = User.query.filter_by(username=name).first()
    #     # remember = request.form.get('remember')
    #     #if not user:
    #     #    return 'user is not exist'
    #     #if user.check_password(password):
    #     #    print 'True'
    #     #    # remember：是否记住用户登录状态
    #     #    login_user(user, remember=remember)
    #     #    return redirect(url_for('index'))
    #     if form.validate_on_submit():
    #         user = User.query.filter_by(username=form.username.data).first()
    #         if user.check_password(form.password.data):
    #             login_user(user, remember=form.remember.data)
    #             return redirect(url_for('index'))
    #     flash('password error')
    #     return redirect(url_for('login'))


    @app.route('/login', methods=['GET', 'POST'])
    @csrf.exempt
    def login():
        if request.method == 'POST':
            username = request.form.get('username')
            password = request.form.get('password')
            remember = request.form.get('remember-me')
            user = User.query.filter_by(username=username).first()
            if user:
                if user.check_password(password):
                    login_user(user, remember=remember)
                    identity_changed.send(
                        current_app._get_current_object(),
                        identity=Identity(user.id)
                    )
                    flash(u'登录成功。', category='success')
                    return redirect(url_for('index'))
            flash(u'用户名和密码不匹配。', category='error')

        return render_template('login_user.html')


    @app.route('/logout')
    @login_required
    def logout():
        logout_user()
        identity_changed.send(
            current_app._get_current_object(),
            identity=AnonymousIdentity()
        )
        flash(u"成功退出", category='success')
        return redirect(url_for('login'))


    @app.route('/beats', methods=['GET', 'POST'])
    def beats():
        data = request.get_json(force=True)
        # data = decryption(rv)

        station = YjStationInfo.query.filter_by(id=data["station_id"]).first()
        station.con_date = int(time.time())

        if station.version != data["version"]:
            station.modification = 1

        db.session.add(station)
        db.session.commit()

        data = {"modification": station.modification, "status": 0}
        # data = encryption(data)
        return jsonify(data)


    @app.route('/api/config', methods=['GET', 'POST'])
    def set_config():
        if request.method == 'POST':
            data = request.get_json(force=True)

            station = db.session.query(YjStationInfo).filter_by(id=data["station_id"]).first_or_404()
            # data = decryption(data)

            data = configuration(station)

            # 将本次发送过配置的站点数据表设置为无更新
            station.modification = 0

            db.session.add(station)
            db.session.commit()

            # data = encryption(data)
            return jsonify({'status': 0, 'data': data})


    @app.route('/api/upload', methods=['POST'])
    def upload():
        if request.method == 'POST':
            data = request.get_json(force=True)
            # data = decryption(data)

            # 验证上传数据
            station_id = data["station_id"]
            version = data["version"]

            # 查询服务器是否有正在上传的站信息
            station = YjStationInfo.query.filter_by(id=station_id).first_or_404()

            # 查询上传信息的版本是否匹配
            try:
                assert (station.version == version)
            except AssertionError:
                return jsonify({"status": "Version Error"})

            for v in data["data"]:
                value = Value(variable_id=v["variable_id"], value=v["value"], time=v["time"])
                db.session.add(value)
            db.session.commit()

            return jsonify({"status": 0,
                            "station": station_id,
                            "version": version})


    def _get_frame(date_string):
        db = MySQLdb.connect('localhost', 'web', 'web', 'pyplc')
        query = 'SELECT * FROM {}'.format(date_string)
        df = read_sql(query, db)
        df = df.head(100)
        return df


    @app.route('/db/<any(yjstationinfo, yjplcinfo, yjgroupinfo, yjvariableinfo):date_string>/')
    @cache.cached(timeout=10)
    def show_tables(date_string=None):
        df = _get_frame(date_string)
        if isinstance(df, bool) and not df:
            return 'Bad data format!'
        return render_template('show_data.html', df=df.to_html(classes='frame'), date_string=date_string)


    def configuration(station_model):
        # 读取staion表数据,根据外链,读出该station下的plc、group variable的数据.每一项数据为一个字典,每个表中所有数据存为一个列表.
        plcs_config = []
        groups_config = []
        variables_config = []

        station_config = get_data_from_model(station_model)

        plcs = station_model.plcs.all()
        if plcs:
            plcs_config = get_data_from_query(plcs)
            for plc in plcs:

                groups = plc.groups.all()
                if groups:
                    groups_config += get_data_from_query(groups)

                variables = plc.variables.all()
                if variables:
                    variables_config += get_data_from_query(variables)

        # 包装数据
        data = {"YjStationInfo": station_config, "YjPLCInfo": plcs_config,
                "YjGroupInfo": groups_config, "YjVariableInfo": variables_config}

        return jsonify(data)


    @app.route('/test')
    def test():
        config = db.session.query(YjStationInfo, YjPLCInfo, YjGroupInfo, YjVariableInfo). \
            filter(YjStationInfo.id == 1). \
            filter(YjStationInfo.id == YjPLCInfo.station_id). \
            filter(YjGroupInfo.plc_id == YjPLCInfo.id). \
            filter(YjPLCInfo.id == YjVariableInfo.id)

        print config
        for station, plc, group, variable in config:
            print station.id, plc.id, group.id, variable.id

        return jsonify({'a': '1'})

    return app
