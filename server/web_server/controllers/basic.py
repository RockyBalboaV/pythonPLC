# coding=utf-8

from os import path

from flask import Blueprint, request, jsonify, render_template, redirect, url_for, current_app, flash, Config

from flask_login import login_user, logout_user, user_logged_in, login_required, current_user
from flask_principal import identity_loaded, identity_changed, UserNeed, RoleNeed, Identity, AnonymousIdentity

from web_server.ext import csrf, api
from web_server.models import *

basic_blueprint = Blueprint(
    'basic',
    __name__,
    template_folder=path.join(path.pardir, 'templates', 'basic')
)


@basic_blueprint.route('/', methods=['GET', 'POST'])
# @cache.cached(timeout=60)
def index():
    users = User.query.all()
    return render_template('index.html', users=users)


@basic_blueprint.route('/test')
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


@basic_blueprint.route('/register', methods=['GET', 'POST'])
@csrf.exempt
def register():
    if request.method == 'POST':
        user = User(username=request.form.get('username'), password=request.form.get('password'))
        db.session.add(user)
        db.session.commit()
        flash(u'注册成功!', category='success')
        return redirect(url_for('login'))
    return render_template('register_user.html')


@basic_blueprint.route('/login', methods=['GET', 'POST'])
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


@basic_blueprint.route('/logout')
@login_required
def logout():
    logout_user()
    identity_changed.send(
        current_app._get_current_object(),
        identity=AnonymousIdentity()
    )
    flash(u"成功退出", category='success')
    return redirect(url_for('basic.login'))
