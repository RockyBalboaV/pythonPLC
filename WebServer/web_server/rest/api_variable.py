# coding=utf-8
from flask import abort, jsonify
from flask_restful import reqparse, Resource, marshal_with, fields

from web_server.models import *
from web_server.rest.parsers import variable_parser, variable_put_parser
from api_templete import ApiResource
from err import err_not_found
from response import rp_create, rp_delete, rp_modify

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


class VariableResource(ApiResource):
    def __init__(self):
        self.args = variable_parser.parse_args()
        super(VariableResource, self).__init__()

    def search(self, variable_id=None):
        if not variable_id:
            variable_id = self.args['id']

        variable_name = self.args['variable_name']
        plc_id = self.args['plc_id']
        plc_name = self.args['plc_name']
        group_id = self.args['group_id']
        group_name = self.args['group_name']
        page = self.args['page']
        per_page = self.args['per_page'] if self.args['per_page'] else 10

        query = YjVariableInfo.query

        if variable_id:
            query = query.filter_by(id=variable_id)

        if variable_name:
            query = query.filter_by(variable_name=variable_name)

        if group_id:
            query = query.filter_by(group_id=group_id)

        if group_name:
            query = query.join(YjGroupInfo, YjGroupInfo.group_name == group_name)

        if plc_id:
            query = query.filter_by(plc_id=plc_id)

        if plc_name:
            query = query.join(YjPLCInfo, YjPLCInfo.plc_name == plc_name)

        if page:
            query = query.paginate(page, per_page, False).items
        else:
            query = query.all()

        return query

    def information(self, models):
        if not models:
            return err_not_found()

        info = []
        for m in models:

            data = dict()
            data['id'] = m.id
            data['variable_name'] = m.variable_name
            data['plc_id'] = m.plc_id
            data['group_id'] = m.group_id
            data['db_num'] = m.db_num
            data['address'] = m.address
            data['data_type'] = m.data_type
            data['rw_type'] = m.rw_type
            data['upload'] = m.upload
            data['acquisition_cycle'] = m.acquisition_cycle
            data['server_record_cycle'] = m.server_record_cycle
            data['note'] = m.note
            data['ten_id'] = m.ten_id
            data['item_id'] = m.item_id
            data['write_value'] = m.write_value

            plc = m.yjplcinfo
            if plc:
                data['plc_name'] = plc.plc_name
            else:
                data['plc_name'] = None

            group = m.yjgroupinfo
            if group:
                data['group_name'] = group.group_name
            else:
                data['group_name'] = None

            info.append(data)

        response = jsonify({'ok': 1, "data": info})
        response.status_code = 200

        return response

    def put(self, variable_id=None):
        args = variable_put_parser.parse_args()

        if not variable_id:
            variable_id = args['id']

        if variable_id:

            variable = YjVariableInfo.query.get(variable_id)

            if not variable:
                return err_not_found()

            if args['variable_name']:
                variable.variable_name = args['variable_name']

            if args['plc_id']:
                variable.plc_id = args['plc_id']

            if args['group_id']:
                variable.group_id = args['group_id']

            if args['db_num']:
                variable.db_num = args['db_num']

            if args['address']:
                variable.address = args['address']

            if args['data_type']:
                variable.data_type = args['data_type']

            if args['rw_type']:
                variable.rw_type = args['rw_type']

            if 'upload' in args.keys():
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

            if args['write_value']:
                variable.write_value = args['write_value']

            db.session.add(variable)
            db.session.commit()

            return rp_modify()

        else:
            variable = YjVariableInfo(variable_name=args['variable_name'],
                                      plc_id=args['plc_id'],
                                      group_id=args['group_id'],
                                      db_num=args['db_num'],
                                      address=args['address'],
                                      data_type=args['data_type'],
                                      rw_type=args['rw_type'],
                                      upload=args['upload'],
                                      acquisition_cycle=args['acquisition_cycle'],
                                      server_record_cycle=args['server_record_cycle'],
                                      note=args['note'],
                                      ten_id=args['ten_id'],
                                      item_id=args['item_id'],
                                      write_value=args['write_value']
                                      )

            db.session.add(variable)
            db.session.commit()

        return rp_create()
