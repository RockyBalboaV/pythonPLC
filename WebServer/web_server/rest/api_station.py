# coding=utf-8
from flask import abort, jsonify
from flask_restful import reqparse, Resource, marshal_with, fields

from web_server.models import *
from web_server.rest.parsers import station_parser, station_put_parser


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


def make_error(status_code):
    response = jsonify({
        'ok': 0,
        'data': ''
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
        data['station_name'] = m.name
        data['mac'] = m.mac
        data['ip'] = m.ip
        data['note'] = m.note
        data['id_num'] = m.id_num
        data['plc_count'] = m.plc_count
        data['ten_id'] = m.ten_id
        data['item_id'] = m.item_id
        data['modification'] = m.modification

        info.append(data)

    response = jsonify({'ok': 0, "data": info})
    response.status_code = 200

    return response


class StationResource(Resource):
    def __init__(self, ):
        self.args = station_parser.parse_args()

    def search(self, station_id):
        if not station_id:
            station_id = self.args['id']

        station_name = self.args['station_name']

        station_query = YjStationInfo.query

        if station_id:
            station_query = station_query.filter_by(id=station_id)

        if station_name:
            station_query = station_query.filter_by(name=station_name)

        station = station_query.all()

        return station

    def get(self, station_id=None):

        station = self.search(station_id)

        response = information(station)

        return response

    def post(self, station_id=None):

        station = self.search(station_id)

        response = information(station)

        return response

    def put(self, station_id=None):
        args = station_put_parser.parse_args()

        if not station_id:
            station_id = args['id']

        if station_id:
            station = YjStationInfo.query.get(station_id)

            if not station:
                make_error(404)

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

        models = self.search(station_id)

        if not models:
            return make_error(404)

        for m in models:
            db.session.delete(m)
        db.session.commit()

        return {'ok': 0}, 200
