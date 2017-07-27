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
        self.args = value_parser.parse_args()
        super(ValueResource, self).__init__()

    def search(self, value_id=None):

        if not value_id:
            value_id = self.args['id']

        variable_id = self.args['variable_id']
        variable_name = self.args['variable_name']
        plc_id = self.args['plc_id']
        plc_name = self.args['plc_name']
        group_id = self.args['group_id']
        group_name = self.args['group_name']
        query_id = self.args['query_id']
        query_name = self.args['query_name']

        min_time = self.args['min_time']
        max_time = self.args['max_time']
        order_time = self.args['order_time']
        limit = self.args['limit']
        page = self.args['page']
        per_page = self.args['per_page'] if self.args['per_page'] else 10

        # query = db.session.query(db.distinct(Value.variable_id).label('variable_id'), Value)
        # query = db.session.query(Value, Value.variable_id)
        query = Value.query
        # query = db.session.query(Value.cls).group_by(Value.variable_id)

        # a = [a[0] for a in db.session.query(Value.variable_id).distinct()]
        # query = db.session.query(Value).filter(Value.variable_id.in_(a))
        if value_id:
            query = query.filter_by(id=value_id)

        if variable_id:
            query = query.join(YjVariableInfo).filter(YjVariableInfo.id.in_(variable_id))

        if variable_name:
            query = query.join(YjVariableInfo).filter(YjVariableInfo.variable_name == variable_name)

        if plc_id:
            query = query.join(YjVariableInfo, YjPLCInfo).filter(YjPLCInfo.id == plc_id)

        if plc_name:
            query = query.join(YjVariableInfo, YjPLCInfo).filter(YjPLCInfo.plc_name == plc_name)

        if group_id:
            query = query.join(YjVariableInfo, YjGroupInfo).filter(YjGroupInfo.id == group_id)

        if group_name:
            query = query.join(YjVariableInfo, YjGroupInfo).filter(YjGroupInfo.group_name == group_name)

        if query_id:
            query = query.join(var_queries, var_queries.columns.query_id == query_id).filter(
                var_queries.columns.variable_id == Value.variable_id)

        if query_name:
            query = query.join(QueryGroup, QueryGroup.name == query_name).\
                join(var_queries, var_queries.columns.query_id == QueryGroup.id).filter(
                var_queries.columns.variable_id == Value.variable_id)

        if min_time:
            query = query.filter(Value.time > min_time)

        if max_time:
            query = query.filter(Value.time < max_time)

        if order_time:
            query = query.order_by(Value.time.desc())

        # if limit:
        #     q = q.limit(limit)

        if page:
            query = query.paginate(page, per_page, False).items
        elif limit:
            # time1 = time.time()
            # variable_id_list = set((v.variable_id for v in query))
            variable_id_list = variable_id
            query = [model
                     for variable_id in variable_id_list
                     for model in
                     query.filter(Value.variable_id == variable_id).order_by(Value.time.desc()).limit(limit).all()
                     ]
            # time2 = time.time()
            # print time2 - time1
        else:
            query = query.all()

        # print query

        return query

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
                data['variable_name'] = variable.variable_name
                plc = variable.yjplcinfo
                group = variable.yjgroupinfo
            else:
                data['variable_name'] = None
                plc = None
                group = None

            if plc:
                data['plc_id'] = plc.id
                data['plc_name'] = plc.plc_name
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
            value = Value(variable_id=args['variable_id'],
                          value=args['value'],
                          time=args['time']
                          )

            db.session.add(value)
            db.session.commit()
            return rp_create()
