# coding=utf-8
from flask import abort, jsonify
from flask_restful import reqparse, Resource, marshal_with, fields

from models import *
from rest.parsers import variable_parser, variable_put_parser

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


class VariableResource(Resource):

    def __init__(self):
        self.args = variable_parser.parse_args()

    def search(self, variable_id=None):
        if not variable_id:
            variable_id = self.args['id']

        plc_id = self.args['plc_id']
        group_id = self.args['group_id']

        if variable_id:
            variable = YjVariableInfo.query.filter_by(id=variable_id).all()
        elif group_id:
            variable = YjVariableInfo.query.filter_by(group_id=group_id).all()
        elif plc_id:
            variable = YjVariableInfo.query.filter_by(plc_id=plc_id).all()
        else:
            variable = YjVariableInfo.query.all()

        if not variable:
            return make_error(404)

        info = []
        for v in variable:
            data = dict()
            data['id'] = v.id
            data['tag_name'] = v.tag_name
            data['plc_id'] = v.plc_id
            data['group_id'] = v.group_id
            data['address'] = v.address
            data['data_type'] = v.data_type
            data['rw_type'] = v.rw_type
            data['upload'] = v.upload
            data['acquisition_cycle'] = v.acquisition_cycle
            data['server_record_cycle'] = v.server_record_cycle
            data['note'] = v.note
            data['ten_id'] = v.ten_id
            data['item_id'] = v.item_id
            info.append(data)

        information = jsonify({"ok": 0, "data": info})

        return information

    def get(self, variable_id=None):

        variable = self.search(variable_id)

        return variable

    def post(self, variable_id=None):

        variable = self.search(variable_id)

        return variable

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

            #   db.session.query(YjVariableInfo).filter(YjVariableInfo.id == variable_id).update({
            #       YjVariableInfo.tag_name: args['tag_name'], YjVariableInfo.plc_id: args['plc_id'],
            #       YjVariableInfo.group_id: args['group_id'], YjVariableInfo.address: args['address'],
            #       YjVariableInfo.data_type: args['data_type'], YjVariableInfo.rw_type: args['rw_type'],
            #       YjVariableInfo.upload: args['upload'], YjVariableInfo.acquisition_cycle: args['acquisition_cycle'],
            #       YjVariableInfo.server_record_cycle: args['server_record_cycle'], YjVariableInfo.note: args['note'],
            #       YjVariableInfo.ten_id: args['ten_id'], YjVariableInfo.item_id: args['item_id']
            #   })

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

        variable = self.search(variable_id)

        for v in variable:
            db.session.delete(v)
        db.session.commit()

        return {'ok': 0}, 204

