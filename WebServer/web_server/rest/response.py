# coding=utf-8

import functools

from flask import jsonify


def make_response(msg, status_code):
    response = jsonify({
        'ok': 1,
        'msg': msg
    })
    response.status_code = status_code
    print response
    return response


rp_create = functools.partial(make_response, msg='创建成功', status_code=200)
rp_modify = functools.partial(make_response, msg='修改成功', status_code=201)
# rp_delete = functools.partial(make_response, msg='成功删除{}条'.format(count), status_code=201)
rp_delete_ration = functools.partial(make_response, msg='成功删除关系', status_code=200)
rp_user_create = functools.partial(make_response, msg='用户创建成功', status_code=200)


def rp_delete(count):
    msg = '成功删除{}条'.format(count)
    status_code = 201
    return make_response(msg, status_code)
