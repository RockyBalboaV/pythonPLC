# coding=utf-8

from flask import current_app, jsonify, request
from flask_restful import Resource, abort
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer

from web_server.rest.parsers import auth_parser
from web_server.models import *
from web_server.rest.err import err_pw, err_user_not_exist, make_error
from web_server.rest.response import rp_user_create


class AuthApi(Resource):
    """
        :param
        username 用户名
        password 密码

        :return
        token 访问令牌
    """

    def post(self):
        current_time = int(time.time())
        args = auth_parser.parse_args()

        try:
            user = User.query.filter_by(username=args['username']).first()
        except:
            return err_user_not_exist()

        expires_time = args['expires'] if args['expires'] else 600

        if user.check_password(args['password']):
            s = Serializer(current_app.config['SECRET_KEY'], expires_in=expires_time)
            user.login_count += 1
            user.last_login_ip = request.remote_addr
            user.last_login_time = current_time
            db.session.add(user)
            db.session.commit()
            response = dict(token=s.dumps({'id': user.id, 'time': current_time}), ok=1)
            return jsonify(response)
        else:
            return err_pw()

    def put(self):
        args = auth_parser.parse_args()

        if args['password']:
            password = args['password']
        else:
            return make_error('请输入密码')

        if args['username']:
            username = args['username']
        else:
            return make_error('请输入用户名')

        user = User.query.filter_by(username=username).first()
        if user:
            return make_error('该用户已存在')

        if not password == args['pw_confirm']:
            return make_error('两次密码需要一致')

        user = User(username=args['username'], password=args['password'])
        role = args['role']
        print role
        if role:
            role_models = Role.query.filter(Role.id.in_(role))

            user.roles += role_models

        db.session.add(user)
        db.session.commit()

        return rp_user_create()
