# coding=utf-8
from flask import abort, jsonify
from flask_restful import reqparse, Resource, marshal_with, fields

from web_server.models import *
from web_server.rest.parsers import variable_parser, variable_put_parser

variable_field = {
    'id': fields.Integer,
    'tag_name': fields.String,
    'plc_id': fields.Integer,
    'group_id': fields.Integer,
    'address': fields.String,
    'data_type': fields.String,
    'rw_type': fields.Integer,
    'upload': fields.Boolean,
    'acquisition_cycle': fields.Integer,
    'server_record_cycle': fields.Integer,
    'note': fields.String,
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


def information(models):
    if not models:
        return make_error(404)

    info = []
    for m in models:

        data = dict()
        data['id'] = m.id
        data['tag_name'] = m.tag_name
        data['plc_id'] = m.plc_id
        data['group_id'] = m.group_id
        data['address'] = m.address
        data['data_type'] = m.data_type
        data['rw_type'] = m.rw_type
        data['upload'] = m.upload
        data['acquisition_cycle'] = m.acquisition_cycle
        data['server_record_cycle'] = m.server_record_cycle
        data['note'] = m.note
        data['ten_id'] = m.ten_id
        data['item_id'] = m.item_id

        plc = m.yjplcinfo
        if plc:
            data['plc_name'] = plc.name
        else:
            data['plc_name'] = None

        group = m.yjgroupinfo
        if group:
            data['group_name'] = group.group_name
        else:
            data['group_name'] = None

        info.append(data)

    response = jsonify({'ok': 0, "data": info})
    response.status_code = 200

    return response


class VariableResource(Resource):

    def __init__(self):
        self.args = variable_parser.parse_args()

    def search(self, variable_id=None):
        if not variable_id:
            variable_id = self.args['id']

        variable_name = self.args['variable_name']
        plc_id = self.args['plc_id']
        plc_name = self.args['plc_name']
        group_id = self.args['group_id']
        group_name = self.args['group_name']

        variable_query = YjVariableInfo.query

        if variable_id:
            variable_query = variable_query.filter_by(id=variable_id)

        if variable_name:
            variable_query = variable_query.filter_by(tag_name=variable_name)

        if group_id:
            variable_query = variable_query.filter_by(group_id=group_id)

        if group_name:
            variable_query = variable_query.join(YjGroupInfo, YjGroupInfo.group_name == group_name)

        if plc_id:
            variable_query = variable_query.filter_by(plc_id=plc_id)

        if plc_name:
            variable_query = variable_query.join(YjPLCInfo, YjPLCInfo.name == plc_name)

        variable = variable_query.all()

        return variable

    def get(self, variable_id=None):

        variable = self.search(variable_id)

        response = information(variable)

        return response

    def post(self, variable_id=None):

        variable = self.search(variable_id)

        response = information(variable)

        return response

    def put(self, variable_id=None):
        args = variable_put_parser.parse_args()

        if not variable_id:
            variable_id = args['id']

        if variable_id:

            variable = YjVariableInfo.query.get(variable_id)

            if not variable:
                return make_error(404)

            if args['tag_name']:
                variable.tag_name = args['tag_name']

            if args['plc_id']:
                variable.plc_id = args['plc_id']

            if args['group_id']:
                variable.group_id = args['group_id']

            if args['address']:
                variable.address = args['address']

            if args['data_type']:
                variable.data_type = args['data_type']

            if args['rw_type']:
                variable.rw_type = args['rw_type']

            if args['upload']:
                variable.upload = args['upload']

            if args['acquisition_cycle']:
                variable.acquisition_cycle = args['acquisition_cycle']

            if args['server_record_cycle']:
                variable.server_record_cycle = args['server_record_cycle']

            if args['note']:
                variable.note = args['note']

            if args['ten_id']:
                variable.ten_id = args['ten_id']

            if args['item_id']:
                variable.item_id = args['item_id']

            db.session.add(variable)
            db.session.commit()

            return {'ok': 0}, 200

        else:
            variable = YjVariableInfo(tag_name=args['tag_name'], plc_id=args['plc_id'],
                                      group_id=args['group_id'], address=args['address'],
                                      data_type=args['data_type'], rw_type=args['rw_type'],
                                      upload=args['upload'], acquisition_cycle=args['acquisition_cycle'],
                                      server_record_cycle=args['server_record_cycle'], note=args['note'],
                                      ten_id=args['ten_id'], item_id=args['item_id'])

            db.session.add(variable)
            db.session.commit()

        return {'ok': 0}, 201

    def delete(self, variable_id=None):

        models = self.search(variable_id)

        if not models:
            return make_error(404)

        for m in models:
            db.session.delete(m)
        db.session.commit()

        return {'ok': 0}, 200

