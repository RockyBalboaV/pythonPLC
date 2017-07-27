# coding=utf-8

import functools

from flask import jsonify
from flask_restful import HTTPException


class ModelNotFound(HTTPException):
    pass

custom_errors = {
    'ModelNotFound': {
        'data': "",
        'ok': 0,
    }
}


def make_error(msg, status_code=400):
    response = jsonify({
        'ok': 0,
        'msg': msg
    })
    response.status_code = status_code
    return response

err_not_found = functools.partial(make_error, msg='查询结果为空', status_code=404)
err_not_contain = functools.partial(make_error, msg='查询的结果不包含选择的值', status_code=400)
err_user_not_exist = functools.partial(make_error, msg='用户名不存在', status_code=404)
err_pw = functools.partial(make_error, msg='密码不正确', status_code=401)
err_user_token = functools.partial(make_error, msg='用户验证错误')
err_user_already_exist = functools.partial(make_error, msg='该用户已存在', status_code=400)