# coding=utf-8
from flask_restful import reqparse, Resource, marshal_with, fields

from models import *

plc_field = {
    'id': fields.Integer,
    'name': fields.String,
    'station_id': fields.Raw,
    'note': fields.String,
    'ip': fields.String,
    'mpi': fields.Integer,
    'type': fields.Integer,
    'plc_type': fields.String,
    'ten_id': fields.String,
    'item_id': fields.String
}

plc_parser = reqparse.RequestParser()
plc_parser.add_argument('id', type=int)
plc_parser.add_argument('station_id', type=str, help='plc从属的station')

plc_put_parser = reqparse.RequestParser()
plc_put_parser.add_argument('id', type=int)
plc_put_parser.add_argument('name', type=str)
plc_put_parser.add_argument('station_id', type=str, help='plc从属的station')
plc_put_parser.add_argument('note', type=str)
plc_put_parser.add_argument('ip', type=str)
plc_put_parser.add_argument('mpi', type=int)
plc_put_parser.add_argument('type', type=int)
plc_put_parser.add_argument('plc_type', type=str)
plc_put_parser.add_argument('ten_id', type=str)
plc_put_parser.add_argument('item_id', type=str)


class PLCResource(Resource):

    def __init__(self, **kwargs):
        self.args = plc_parser.parse_args()

    @staticmethod
    def search(plc_id=None, station_id=None):
        if plc_id:
            plc = YjPLCInfo.query.filter_by(id=plc_id).all()
        elif station_id:
            plc = YjPLCInfo.query.filter_by(station_id=station_id).all()
        else:
            plc = YjPLCInfo.query.all()
        return plc

    @marshal_with(plc_field)
    def get(self, id=None):
        if id:
            plc = YjPLCInfo.query.filter_by(id=id).first()
        else:
            plc = YjPLCInfo.query.all()
        return plc

    @marshal_with(plc_field)
    def post(self, **kwargs):
        station_id = self.args['station_id']
        plc_id = self.args['id']

        plc = self.search(plc_id, station_id)

        return plc

    def put(self):
        args = plc_put_parser.parse_args()
        print args.values(), args.keys()
        # plc = YjPLCInfo(args.values())

        plc = YjPLCInfo(name=args['name'], station_id=args['station_id'], note=args['note'], ip=args['ip'],
                        mpi=args['mpi'], type=args['type'], plc_type=args['plc_type'], ten_id=args['ten_id'],
                        item_id=args['item_id'])
        
        db.session.add(plc)
        db.session.commit()
        return {'ok': 0}, 201

    def delete(self, **kwargs):
        station_id = self.args['station_id']
        plc_id = self.args['id']

        plc = self.search(station_id, plc_id)

        for p in plc:
            db.session.delete(p)
        db.session.commit()
        return {'ok': 0}
