# coding=utf-8
from flask import abort, jsonify
from flask_restful import reqparse, Resource, marshal_with, fields

from models import *
from rest.parsers import group_parser, group_put_parser

group_field = {
    'id': fields.Integer,
    'group_name': fields.String,
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


class GroupResource(Resource):

    def __init__(self):
        self.args = group_parser.parse_args()

    def search(self, group_id=None):

        if not group_id:
            group_id = self.args['id']
        plc_id = self.args['plc_id']

        if group_id:
            group = YjGroupInfo.query.filter_by(id=group_id).all()
        elif plc_id:
            group = YjGroupInfo.query.filter_by(plc_id=plc_id).all()
        else:
            group = YjGroupInfo.query.all()

        if not group:
            return make_error(404)

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
            data['plc_name'] = g.yjplcinfo.name
            info.append(data)

        information = jsonify({"ok": 0, "data": info})

        return information

    def get(self, group_id=None):

        group = self.search(group_id)

        return group

    def post(self, group_id=None):

        group = self.search(group_id)

        return group

    def put(self, group_id=None):
        args = group_put_parser.parse_args()

        if not group_id:
            group_id = args['id']

        if group_id:

            group = YjGroupInfo.query.get(group_id)

            if not group:
                return make_error(404)

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

            # db.session.query(YjGroupInfo).filter(YjGroupInfo.id == group_id).update({
            #     YjGroupInfo.group_name: args['group_name'], YjGroupInfo.plc_id: args['plc_id'],
            #     YjGroupInfo.note: args['note'], YjGroupInfo.upload_cycle: args['upload_cycle'],
            #     YjGroupInfo.ten_id: args['ten_id'], YjGroupInfo.item_id: args['item_id']})

            db.session.add(group)
            db.session.commit()
            return {'ok': 0}, 200

        else:
            group = YjGroupInfo(group_name=args['group_name'], plc_id=args['plc_id'], note=args['note'],
                                upload_cycle=args['upload_cycle'], ten_id=args['ten_id'], item_id=args['item_id'])

            db.session.add(group)
            db.session.commit()
            return {'ok': 0}, 201

    def delete(self, group_id=None):

        group = self.search(group_id)

        for g in group:
            db.session.delete(g)
        db.session.commit()

        return {'ok': 0}, 204

