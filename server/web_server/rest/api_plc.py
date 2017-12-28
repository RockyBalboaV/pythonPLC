# coding=utf-8
from flask import jsonify, Response

from web_server.models import *
from web_server.rest.parsers import plc_parser, plc_put_parser
from api_templete import ApiResource
from err import err_not_found
from response import rp_create, rp_delete, rp_modify


class PLCResource(ApiResource):
    def __init__(self):
        self.args = plc_parser.parse_args()
        super(PLCResource, self).__init__()
        self.query = YjPLCInfo.query

    def search(self):

        plc_id = self.args['id']
        plc_name = self.args['plc_name']
        station_id = self.args['station_id']
        station_name = self.args['station_name']

        limit = self.args['limit']
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

        if limit:
            query = query.limit(limit)

        if page:
            query = query.paginate(page, per_page, False).items
        else:
            query = query.all()

        self.query = query

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
            data['rack'] = m.rack
            data['slot'] = m.slot
            data['tcp_port'] = m.tcp_port

            if station:
                data['station_id_num'] = station.id_num
                data['station_name'] = station.station_name
            else:
                data['station_id_num'] = None
                data['station_name'] = None

            info.append(data)

        response = jsonify({'ok': 1, "data": info})
        response.status_code = 200

        return response

    def put(self):
        args = plc_put_parser.parse_args()

        plc_id = args['id']

        if plc_id:

            plc = YjPLCInfo.query.get(plc_id)
            self.query = [].append(plc)
            print self.query
            if not plc:
                return err_not_found()

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

            if args['rack']:
                plc.rack = args['rack']

            if args['slot']:
                plc.slot = args['slot']

            if args['tcp_port']:
                plc.tcp_port = args['tcp_port']

            db.session.add(plc)
            db.session.commit()

            return rp_modify()

        else:
            self.query = []
            plc = YjPLCInfo(
                plc_name=args['plc_name'],
                station_id=args['station_id'],
                note=args['note'],
                ip=args['ip'],
                mpi=args['mpi'],
                type=args['type'],
                plc_type=args['plc_type'],
                ten_id=args['ten_id'],
                item_id=args['item_id'],
                rack=args['rack'],
                slot=args['slot'],
                tcp_port=args['tcp_port']
            )

            db.session.add(plc)
            db.session.commit()
            self.new_id = plc.id
            return rp_create()
