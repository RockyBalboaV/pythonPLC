# coding=utf-8
from flask import abort, jsonify
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
        station = p.yjstationinfo

        data = dict()
        data['id'] = m.id
        data['name'] = m.name
        data['station_id'] = m.station_id
        data['note'] = m.note
        data['ip'] = m.ip
        data['mpi'] = m.mpi
        data['type'] = m.type
        data['plc_type'] = m.plc_type
        data['ten_id'] = m.ten_id
        data['item_id'] = m.item_id

        if station:
            data['station_id_num'] = station.id_num
        else:
            data['station_id_num'] = None

        info.append(data)

    response = jsonify({'ok': 0, "data": info})
    response.status_code = 200

    return response


class PLCResource(Resource):

    def __init__(self):
        self.args = plc_parser.parse_args()

    def search(self, plc_id=None):

        if not plc_id:
            plc_id = self.args['id']
        plc_name = self.args['plc_name']
        station_id = self.args['station_id']
        station_name = self.args['station_name']

        plc_query = YjPLCInfo.query

        if plc_id:
            plc_query = plc_query.filter_by(id=plc_id)

        if plc_name:
            plc_query = plc_query.filter_by(name=plc_name)

        if station_id:
            plc_query = plc_query.filter_by(station_id=station_id)

        if station_name:
            plc_query = plc_query.join(YjStationInfo, YjStationInfo.name == station_name)

        plc = plc_query.all()

        return plc

    def verify(self):

        token = self.args['token']
        user = User.verify_auth_token(token)

        if not user:
            abort(401)

    def get(self, plc_id=None):

        plc = self.search(plc_id)

        response = information(plc)

        return response

    def post(self, plc_id=None):

        plc = self.search(plc_id)

        response = information(plc)

        return response

    def put(self, plc_id=None):
        args = plc_put_parser.parse_args()

        if not plc_id:
            plc_id = args['id']

        if plc_id:

            plc = YjPLCInfo.query.get(plc_id)
            if not plc:
                return make_error(404)

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

        models = self.search(plc_id)

        if not models:
            return make_error(404)

        for m in models:
            db.session.delete(m)
        db.session.commit()

        return {'ok': 0}, 200
