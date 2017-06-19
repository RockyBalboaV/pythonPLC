# coding=utf-8

from flask import abort, current_app
from flask_restful import Resource
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer

from web_server.rest.parsers import plc_put_parser
from web_server.models import *


class AuthApi(Resource):
    """
        :param
        username 用户名
        password 密码

        :return
        token 访问令牌
    """

    def post(self):
        args = plc_put_parser.parse_args()
        user = User.query.filter_by(username=args['username']).first()

        if user.check_password(args['password']):
            s = Serializer(current_app.config['SECRET_KEY'], expires_in=600)
            return {"token": s.dumps({'id': user.id})}
        else:
            abort(401)


