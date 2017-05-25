# coding=utf-8
from flask import abort
from flask_restful import reqparse, Resource, marshal_with, fields

from models import *
from rest.parsers import plc_parser, plc_put_parser

plc_field = {
    'id': fields.Integer,
    'name': fields.String,
    'station_id': fields.Integer,
    'note': fields.String,
    'ip': fields.String,
    'mpi': fields.Integer,
    'type': fields.Integer,
    'plc_type': fields.String,
    'ten_id': fields.String,
    'item_id': fields.String
}


class PLCResource(Resource):

    def __init__(self):
        self.args = plc_parser.parse_args()

    def search(self, plc_id=None):

        if not plc_id:
            plc_id = self.args['id']

        station_id = self.args['station_id']

        if plc_id:
            plc = YjPLCInfo.query.filter_by(id=plc_id).all()
        elif station_id:
            plc = YjPLCInfo.query.filter_by(station_id=station_id).all()
        else:
            plc = YjPLCInfo.query.all()

        if plc:
            return plc
        else:
            abort(404)

    def verify(self):

        token = self.args['token']
        user = User.verify_auth_token(token)

        if not user:
            abort(401)

    @marshal_with(plc_field)
    def get(self, plc_id=None):

        plc = self.search(plc_id)

        return plc

    @marshal_with(plc_field)
    def post(self, plc_id=None):

        plc = self.search(plc_id)

        return plc

    def put(self, plc_id=None):
        args = plc_put_parser.parse_args()

        if not plc_id:
            plc_id = args['id']
        if plc_id:

            plc = YjPLCInfo.query.get(plc_id)
            if not plc:
                abort(404)

            if args['name']:
                plc.name = args['name']

            if args['station_id']:
                plc.station_id = args['station_id']

            if args['note']:
                plc.note = args['note']

            if args['ip']:
                plc.ip = args['ip']

            if args['mpi']:
                plc.mpi = args['mpi']

            if args['type']:
                plc.type = args['type']

            if args['plc_type']:
                plc.plc_type = args['plc_type']

            if args['ten_id']:
                plc.ten_id = args['ten_id']

            if args['item_id']:
                plc.item_id = args['item_id']

            # db.session.query(YjPLCInfo).filter(YjPLCInfo.id == plc_id).update({
            #     YjPLCInfo.name: args['name'], YjPLCInfo.station_id: args['station_id'],
            #     YjPLCInfo.note: args['note'], YjPLCInfo.ip: args['ip'], YjPLCInfo.mpi: args['mpi'],
            #     YjPLCInfo.type: args['type'], YjPLCInfo.plc_type: args['plc_type'],
            #     YjPLCInfo.ten_id: args['ten_id'], YjPLCInfo.item_id: args['item_id']
            # })

            db.session.add(plc)
            db.session.commit()
            return {'ok': 0}, 200

        else:
            plc = YjPLCInfo(name=args['name'], station_id=args['station_id'], note=args['note'], ip=args['ip'],
                            mpi=args['mpi'], type=args['type'], plc_type=args['plc_type'], ten_id=args['ten_id'],
                            item_id=args['item_id'])

            db.session.add(plc)
            db.session.commit()
            return {'ok': 0}, 201

    def delete(self, plc_id=None):

        plc = self.search(plc_id)

        for p in plc:
            db.session.delete(p)
        db.session.commit()
        return {'ok': 0}, 204
