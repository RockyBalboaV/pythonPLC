# coding=utf-8
import datetime
import time

from flask import abort, jsonify
from flask_restful import reqparse, Resource, marshal_with, fields

from web_server.models import *
from web_server.rest.parsers import value_parser, value_put_parser
from api_templete import ApiResource
from err import err_not_found
from response import rp_create, rp_delete, rp_modify

value_field = {
    'id': fields.Integer,
    'value_name': fields.String,
    'plc_id': fields.Integer,
    'note': fields.String,
    'upload_cycle': fields.Integer,
    'ten_id': fields.String,
    'item_id': fields.String
}


class ValueResource(ApiResource):

    def __init__(self):
        super(ApiResource, self).__init__()
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

        return value

    def information(self, value):
        if not value:
            return err_not_found()

        info = []
        for v in value:

            data = dict()
            data['id'] = v.id
            data['variable_id'] = v.variable_id
            data['value'] = v.value
            data['time'] = v.time

            variable = v.yjvariableinfo
            if variable:
                data['variable_name'] = variable.tag_name
                plc = variable.yjplcinfo
                group = variable.yjgroupinfo
            else:
                data['variable_name'] = None
                plc = None
                group = None

            if plc:
                data['plc_id'] = plc.id
                data['plc_name'] = plc.name
            else:
                data['plc_id'] = None
                data['plc_name'] = None

            if group:
                data['group_id'] = group.id
                data['group_name'] = group.group_name
            else:
                data['group_id'] = None
                data['group_name'] = None

            info.append(data)

        response = jsonify({"ok": 1, "data": info})

        return response

    def put(self, value_id=None):
        args = value_put_parser.parse_args()

        if not value_id:
            value_id = args['id']

        if value_id:

            value = Value.query.get(value_id)

            if not value:
                return err_not_found()

            if args['variable_id']:
                value.variable_id = args['variable_id']

            if args['value']:
                value.value = args['value']

            if args['time']:
                value.time = args['time']

            db.session.add(value)
            db.session.commit()
            return rp_modify()

        else:
            value = Value(variable_id=args['variable_id'], value=args['value'], time=args['time'])

            db.session.add(value)
            db.session.commit()
            return rp_create()

