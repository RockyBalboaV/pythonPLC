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
            query = query.join(YjGroupInfo).filter(YjGroupInfo.plc_id == plc_id)

        if plc_name:
            query = query.join(YjGroupInfo, YjPLCInfo).filter(YjPLCInfo.plc_name == plc_name)

        if page:
            query = query.paginate(page, per_page, False).items
        else:
            query = query.all()

        return query

    def information(self, models):
        if not models:
            return err_not_found()

        # time1 = time.time()
        # info = [
        #     dict(
        #         id=m.id,
        #         variable_name=m.variable_name,
        #         group_id=m.group_id,
        #         db_num=m.db_num,
        #         address=m.address,
        #         area=m.area,
        #         write_value=m.write_value,
        #         data_type=m.data_type,
        #         rw_type=m.rw_type,
        #         upload=m.upload,
        #         acquisition_cycle=m.acquisition_cycle,
        #         server_record_cycle=m.server_record_cycle,
        #         note=m.note,
        #         ten_id=m.ten_id,
        #         item_id=m.item_id,
        #         group_name=m.yjgroupinfo.group_name if m.yjgroupinfo else None,
        #         plc_id=m.yjgroupinfo.yjplcinfo.id if m.yjgroupinfo and m.yjgroupinfo.yjplcinfo else None,
        #         plc_name=m.yjgroupinfo.yjplcinfo.plc_name if m.yjgroupinfo and m.yjgroupinfo.yjplcinfo else None,
        #     )
        #     for m in models
        # ]

        # time2 = time.time()
        # print(time2 - time1)

        time1 = time.time()
        info = []
        for m in models:

            data = dict()
            data['id'] = m.id
            data['variable_name'] = m.variable_name
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

            group = m.yjgroupinfo
            if group:
                data['group_name'] = group.group_name
                data['plc_id'] = group.plc_id
                plc = group.yjplcinfo
            else:
                data['group_name'] = None
                data['plc_id'] = None
                plc = None

            if plc:
                data['plc_name'] = plc.plc_name
            else:
                data['plc_name'] = None

            info.append(data)

        time2 = time.time()
        print(time2 - time1)

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

            if args['variable_name'] is not None:
                variable.variable_name = args['variable_name']

            if args['group_id'] is not None:
                variable.group_id = args['group_id']

            if args['db_num'] is not None:
                variable.db_num = args['db_num']

            if args['address'] is not None:
                variable.address = args['address']

            if args['data_type'] is not None:
                variable.data_type = args['data_type']

            if args['rw_type'] is not None:
                variable.rw_type = args['rw_type']

            if args['upload'] is not None:
                variable.upload = args['upload']

            if args['acquisition_cycle'] is not None:
                variable.acquisition_cycle = args['acquisition_cycle']

            if args['server_record_cycle'] is not None:
                variable.server_record_cycle = args['server_record_cycle']

            if args['note'] is not None:
                variable.note = args['note']

            if args['ten_id'] is not None:
                variable.ten_id = args['ten_id']

            if args['item_id'] is not None:
                variable.item_id = args['item_id']

            if args['write_value'] is not None:
                variable.write_value = args['write_value']

            if args['area'] is not None:
                variable.area = args['area']

            db.session.add(variable)
            db.session.commit()

            return rp_modify()

        else:
            variable = YjVariableInfo(
                variable_name=args['variable_name'],
                group_id=args['group_id'],
                db_num=args['db_num'],
                address=args['address'],
                area=args['area'],
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
