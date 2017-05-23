from flask import abort, current_app
from flask_restful import Resource
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer

from rest.parsers import plc_put_parser
from models import *


class AuthApi(Resource):
    def post(self):
        args = plc_put_parser.parse_args()
        user = User.query.filter_by(username=args['username']).first()

        if user.check_password(args['password']):
            s = Serializer(current_app.config['SECRET_KEY'], expires_in=600)
            return {"token": s.dumps({'id': user.id})}
        else:
            abort(401)


