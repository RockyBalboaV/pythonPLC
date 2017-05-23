# coding=utf-8
from flask import abort
from flask_restful import reqparse, Resource, marshal_with, fields

from models import *
from parsers import station_parser, station_put_parser


station_field = {
    'name': fields.String,
    'mac': fields.String,
    'ip': fields.String,
    'note': fields.String,
    'id_num': fields.String,
    'plc_count': fields.Integer,
    'ten_id': fields.String,
    'item_id': fields.String
}


class StationResource(Resource):
    def __init__(self, ):
        self.args = station_parser.parse_args()

    def search(self, station_id):
        if not station_id:
            station_id = self.args['id']

        if station_id:
            station = YjStationInfo.query.filter_by(id=station_id).all()
        else:
            station = YjStationInfo.query.all()

        if not station:
            abort(404)

        return station

    @marshal_with(station_field)
    def get(self, station_id=None):

        station = self.search(station_id)

        return station

    @marshal_with(station_field)
    def post(self, station_id=None):

        station = self.search(station_id)

        return station

    def put(self, station_id=None):
        args = station_put_parser.parse_args()

        if not station_id:
            station_id = args['id']

        if station_id:
            station = YjStationInfo.query.get(station_id)

            if not station:
                abort(404)

            if args['name']:
                station.name = args['name']

            if args['mac']:
                station.mac = args['mac']

            if args['ip']:
                station.ip = args['mac']

            if args['note']:
                station.note = args['note']

            if args['id_num']:
                station.id_num = args['id_num']

            if args['plc_count']:
                station.plc_count = args['plc_count']

            if args['ten_id']:
                station.ten_id = args['plc_count']

            if args['item_id']:
                station.item_id = args['item_id']

            if args['modification']:
                station.modification = args['modification']

            db.session.add(station)
            db.session.commit()
            return {'ok': 0}, 200

        else:
            station = YjStationInfo(name=args['name'], mac=args['mac'], ip=args['ip'], note=args['note'],
                                    id_num=args['id_num'], plc_count=args['plc_count'], ten_id=args['ten_id'],
                                    item_id=args['item_id'], modification=args['modification'])
            db.session.add(station)
            db.session.commit()
            return {'ok': 0}, 201

    def delete(self, station_id=None):

        station = self.search(station_id)

        for s in station:
            db.session.delete(s)
        db.session.commit()
        return {'ok': 0}, 204
