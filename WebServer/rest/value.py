# coding=utf-8
import datetime
import time

from flask import abort, jsonify
from flask_restful import reqparse, Resource, marshal_with, fields

from models import *
from rest.parsers import value_parser, value_put_parser

value_field = {
    'id': fields.Integer,
    'value_name': fields.String,
    'plc_id': fields.Integer,
    'note': fields.String,
    'upload_cycle': fields.Integer,
    'ten_id': fields.String,
    'item_id': fields.String
}


def make_error(status_code):
    response = jsonify({
        'ok': 0,
        'data': ""
    })
    response.status_code = status_code
    return response


class ValueResource(Resource):

    def __init__(self):
        self.args = value_parser.parse_args()

    def search(self, value_id=None):

        if not value_id:
            value_id = self.args['id']

        variable_id = self.args['variable_id']
        variable_name = self.args['variable_name']
        plc_id = self.args['plc_id']
        plc_name = self.args['plc_name']
        group_id = self.args['group_id']
        group_name = self.args['group_name']
        min_time = self.args['min_time']
        max_time = self.args['max_time']
        limit = self.args['limit']

        value = Value.query

        if value_id:
            value = value.filter_by(id=value_id)

        if variable_name:
            value = value.join(YjVariableInfo).filter(YjVariableInfo.id == variable_id)

        if variable_name:
            value = value.join(YjVariableInfo).filter(YjVariableInfo.tag_name == variable_name)

        if plc_id:
            value = value.join(YjVariableInfo, YjPLCInfo).filter(YjPLCInfo.id == plc_id)

        if plc_name:
            value = value.join(YjVariableInfo, YjPLCInfo).filter(YjPLCInfo.name == plc_name)

        if group_id:
            value = value.join(YjVariableInfo, YjGroupInfo).filter(YjGroupInfo.id == group_id)

        if group_name:
            value = value.join(YjVariableInfo, YjGroupInfo).filter(YjGroupInfo.group_name == group_name)

        if min_time:
            value = value.filter(Value.time > min_time)

        if max_time:
            value = value.filter(Value.time < max_time)

        if limit:
            value = value.limit(limit)

        value = value.all()

        if not value:
            return make_error(404)

        info = []
        for v in value:
            data = dict()
            data['id'] = v.id
            data['variable_id'] = v.variable_id
            data['variable_name'] = v.yjvariableinfo.tag_name
            data['group_id'] = v.yjvariableinfo.yjgroupinfo.id
            data['group_name'] = v.yjvariableinfo.yjgroupinfo.group_name
            data['plc_id'] = v.yjvariableinfo.yjplcinfo.id
            data['plc_name'] = v.yjvariableinfo.yjplcinfo.name
            data['value'] = v.value
            data['time'] = int(v.time)
            info.append(data)

        information = jsonify({"ok": 0, "data": info})

        return information

    def get(self, value_id=None):

        value = self.search(value_id)

        return value

    def post(self, value_id=None):

        value = self.search(value_id)

        return value

    def put(self, value_id=None):
        args = value_put_parser.parse_args()

        if not value_id:
            value_id = args['id']

        if value_id:

            value = Value.query.get(value_id)

            if not value:
                return make_error(404)

            if args['variable_name']:
                value.value_name = args['variable_name']

            if args['value']:
                value.plc_id = args['value']

            if args['time']:
                value.note = args['time']

            db.session.add(value)
            db.session.commit()
            return {'ok': 0}, 200

        else:
            value = Value(variable_name=args['variable_name'], value=args['value'], time=args['time'])

            db.session.add(value)
            db.session.commit()
            return {'ok': 0}, 201

    def delete(self, value_id=None):

        value = self.search(value_id)

        for v in value:
            db.session.delete(v)
        db.session.commit()

        return {'ok': 0}, 204

