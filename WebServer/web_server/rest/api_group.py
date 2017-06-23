# coding=utf-8
from flask import abort, jsonify
from flask_restful import reqparse, Resource, marshal_with, fields

from web_server.models import *
from web_server.rest.parsers import group_parser, group_put_parser
from err import err_not_found
from response import rp_create, rp_delete, rp_modify

group_field = {
    'id': fields.Integer,
    'group_name': fields.String,
    'plc_id': fields.Integer,
    'note': fields.String,
    'upload_cycle': fields.Integer,
    'ten_id': fields.String,
    'item_id': fields.String
}


def information(group):
    if not group:
        return err_not_found()

    info = []
    for g in group:

        data = dict()
        data['id'] = g.id
        data['group_name'] = g.group_name
        data['plc_id'] = g.plc_id
        data['upload_cycle'] = g.upload_cycle
        data['note'] = g.note
        data['ten_id'] = g.ten_id
        data['item_id'] = g.item_id

        plc = g.yjplcinfo
        if plc:
            data['plc_name'] = plc.name
        else:
            data['plc_name'] = None

        info.append(data)

    response = jsonify({'ok': 1, "data": info})
    response.status_code = 200

    return response


class GroupResource(Resource):

    def __init__(self):
        self.args = group_parser.parse_args()

    def search(self, group_id=None):

        if not group_id:
            group_id = self.args['id']

        group_name = self.args['group_name']
        plc_id = self.args['plc_id']
        plc_name = self.args['plc_name']

        group_query = YjGroupInfo.query

        if group_id:
            group_query = group_query.filter_by(id=group_id)

        if group_name:
            group_query = group_query.filter_by(group_name=group_name)

        if plc_id:
            group_query = group_query.filter_by(plc_id=plc_id)

        if plc_name:
            group_query = group_query.join(YjPLCInfo, YjPLCInfo.name == plc_name)

        group = group_query.all()

        return group

    def get(self, group_id=None):

        group = self.search(group_id)

        response = information(group)

        return response

    def post(self, group_id=None):

        group = self.search(group_id)

        response = information(group)

        return response

    def put(self, group_id=None):
        args = group_put_parser.parse_args()

        if not group_id:
            group_id = args['id']

        if group_id:

            group = YjGroupInfo.query.get(group_id)

            if not group:
                return err_not_found()

            if args['group_name']:
                group.group_name = args['group_name']

            if args['plc_id']:
                group.plc_id = args['plc_id']

            if args['note']:
                group.note = args['note']

            if args['upload_cycle']:
                group.upload_cycle = args['upload_cycle']

            if args['ten_id']:
                group.ten_id = args['ten_id']

            if args['item_id']:
                group.item_id = args['item_id']

            db.session.add(group)
            db.session.commit()
            return rp_modify()

        else:
            group = YjGroupInfo(group_name=args['group_name'], plc_id=args['plc_id'], note=args['note'],
                                upload_cycle=args['upload_cycle'], ten_id=args['ten_id'], item_id=args['item_id'])

            db.session.add(group)
            db.session.commit()
            return rp_create()

    def delete(self, group_id=None):

        models = self.search(group_id)
        count = models.count()

        if not models:
            return err_not_found()

        for m in models:
            db.session.delete(m)
        db.session.commit()

        return rp_delete(count)

