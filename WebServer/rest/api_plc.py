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
    'plctype': fields.String,
    'tenid': fields.String,
    'itemid': fields.String
}

plc_parser = reqparse.RequestParser()
plc_parser.add_argument('id', type=int)
plc_parser.add_argument('name', type=str)
plc_parser.add_argument('station_id', type=str, help='plc从属的station')
plc_parser.add_argument('note', type=str)
plc_parser.add_argument('ip', type=str)
plc_parser.add_argument('mpi', type=int)
plc_parser.add_argument('type', type=int)
plc_parser.add_argument('plctype', type=str)
plc_parser.add_argument('tenid', type=str)
plc_parser.add_argument('itemid', type=str)


class PLCResource(Resource):
    def __init__(self):
        self.args = plc_parser.parse_args()

    @marshal_with(plc_field)
    def get(self, id=None):
        if id:
            plc = YjPLCInfo.query.filter_by(id=id).first()
        else:
            plc = YjPLCInfo.query.all()
        return plc

    @marshal_with(plc_field)
    def post(self):
        station_id = self.args['station_id']
        plc_id = self.args['id']
        if plc_id:
            plc = YjPLCInfo.query.filter_by(id=plc_id).first()
        elif station_id:
            plc = YjPLCInfo.query.filter_by(station_id=station_id).all()
        else:
            plc = YjPLCInfo.query.all()
        return plc

    def put(self, **kwargs):
        args = self.args

        plc = YjPLCInfo(name=args['name'], station_id=args['station_id'], note=args['note'], ip=args['ip'],
                        mpi=args['mpi'], type=args['type'],
                        plctype=args['plctype'], tenid=args['tenid'], itemid=args['itemid'])
        db.session.add(plc)
        db.session.commit()
        return {'ok': 0}, 201

    def delete(self):
        station_id = self.args['station_id']
        plc_id = self.args['id']
        if plc_id:
            plc = YjPLCInfo.query.filter_by(id=plc_id).all()
        elif station_id:
            plc = YjPLCInfo.query.filter_by(station_id=station_id).all()
        else:
            plc = YjPLCInfo.query.all()
        for p in plc:
            db.session.delete(p)
        db.session.commit()
        return {'ok': 0}
