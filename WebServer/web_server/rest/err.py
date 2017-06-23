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


def make_error(msg, status_code):
    response = jsonify({
        'ok': 0,
        'msg': msg
    })
    response.status_code = status_code
    return response

err_not_found = functools.partial(make_error, msg='查询结果为空', status_code=404)
