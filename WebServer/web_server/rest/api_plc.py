# coding=utf-8
from flask import abort, jsonify
from flask_restful import reqparse, Resource, marshal_with, fields

from web_server.models import *
from web_server.rest.parsers import plc_parser, plc_put_parser
from api_templete import ApiResource
from err import err_not_found
from response import rp_create, rp_delete, rp_modify

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


class PLCResource(ApiResource):
    def __init__(self):
        super(PLCResource, self).__init__()
        self.args = plc_parser.parse_args()

    def search(self, plc_id=None):

        if not plc_id:
            plc_id = self.args['id']
        plc_name = self.args['plc_name']
        station_id = self.args['station_id']
        station_name = self.args['station_name']


        page = self.args['page']
        per_page = self.args['per_page'] if self.args['per_page'] else 10

        query = YjPLCInfo.query

        if plc_id:
            query = query.filter_by(id=plc_id)

        if plc_name:
            query = query.filter_by(plc_name=plc_name)

        if station_id:
            query = query.filter_by(station_id=station_id)

        if station_name:
            query = query.join(YjStationInfo, YjStationInfo.station_name == station_name)

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
            station = m.yjstationinfo

            data = dict()
            data['id'] = m.id
            data['plc_name'] = m.plc_name
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
                data['station_name'] = station.station_name
            else:
                data['station_id_num'] = None

            info.append(data)

        response = jsonify({'ok': 1, "data": info})
        response.status_code = 200

        return response

    def verify(self):

        token = self.args['token']
        user = User.verify_auth_token(token)

        if not user:
            abort(401)

    def put(self, plc_id=None):
        args = plc_put_parser.parse_args()

        if not plc_id:
            plc_id = args['id']

        if plc_id:

            plc = YjPLCInfo.query.get(plc_id)
            if not plc:
                return err_not_found()

            print args['plc_name']

            if args['plc_name']:
                plc.plc_name = args['plc_name']

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

            return rp_modify()

        else:
            plc = YjPLCInfo(plc_name=args['plc_name'], station_id=args['station_id'], note=args['note'], ip=args['ip'],
                            mpi=args['mpi'], type=args['type'], plc_type=args['plc_type'], ten_id=args['ten_id'],
                            item_id=args['item_id'])

            db.session.add(plc)
            db.session.commit()

            return rp_create()
