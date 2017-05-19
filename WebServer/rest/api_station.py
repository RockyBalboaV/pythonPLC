# coding=utf-8
from flask_restful import reqparse, Resource, marshal_with, fields

from models import *

station_parser = reqparse.RequestParser()
station_parser.add_argument('admin', type=bool, help='Use super manager mode',
                    default=False)
station_parser.add_argument('station_id', type=str, help='plc从属的station')
station_parser.add_argument('id', type=int, help='该数据的主键')


station_field = {
    'idnum': fields.Integer,
    'plcnum': fields.Integer,
    'name': fields.String,
    'mac': fields.String,
    'ip': fields.String,
    'note': fields.String,
    'tenid': fields.String,
    'itemid': fields.String
}


class StationResource(Resource):
    def __init__(self):
        self.args = station_parser.parse_args()

    @marshal_with(station_field)
    def get(self, **kwargs):
        station = YjStationInfo.query.all()
        return station

    @marshal_with(station_field)
    def post(self, **kwargs):
        idnum = self.args['id']
        station = YjStationInfo.query.filter_by(idnum=idnum).first()
        return station

    def put(self, **kwargs):
        print "1"
        idnum = self.args['id']
        print "2"
        station = YjStationInfo(idnum=idnum, plcnum=1, name="test", mac="test", ip="test", note="test", tenid="0", itemid="test")
        db.session.add(station)
        db.session.commit()
        return {'ok': 0}, 201