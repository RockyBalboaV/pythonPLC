# coding=utf-8
import datetime
import time

from flask import abort, jsonify

from web_server.models import *
from web_server.rest.parsers import status_parser, status_put_parser
from api_templete import ApiResource
from err import err_not_found
from response import rp_create, rp_delete, rp_modify


class StatusResource(ApiResource):
    def __init__(self):
        self.args = status_parser.parse_args()
        super(StatusResource, self).__init__()

    def search(self, model_id=None):

        if not model_id:
            model_id = self.args['id']

        station_id = self.args['station_id']

        min_time = self.args['min_time']
        max_time = self.args['max_time']
        order_time = self.args['order_time']
        limit = self.args['limit']
        page = self.args['page']
        per_page = self.args['per_page'] if self.args['per_page'] else 10

        query = TransferLog.query
        # print query.all()

        if model_id:
            query = query.filter_by(id=model_id)

        if station_id:
            query = query.filter(TransferLog.station_id.in_(station_id))

        if min_time:
            query = query.filter(TransferLog.time > min_time)

        if max_time:
            query = query.filter(TransferLog.time < max_time)

        if order_time:
            query = query.order_by(TransferLog.time.desc())

        # if limit:
        #     query = query.limit(limit)

        if page:
            query = query.paginate(page, per_page, False).items
        elif limit:
            # time1 = time.time()
            # station_id_list = set((a.station_id for a in query))
            station_id_list = station_id
            query = [model
                     for s_id in station_id_list
                     for model in query.filter(TransferLog.station_id == s_id).limit(limit).all()
                     ]
            # time2 = time.time()
            # print time2 - time1
        else:
            query = query.all()

        # print query.all()

        return query

    def information(self, models):
        if not models:
            return err_not_found()

        info = [dict(id=m.id,
                     station_id=m.station_id,
                     level=m.level,
                     note=m.note,
                     time=m.time)
                for m in models
                ]

        response = jsonify({"ok": 1, "data": info})

        return response

    def put(self, model_id=None):
        args = status_put_parser.parse_args()

        if not model_id:
            model_id = args['id']

        if model_id:
            model = TransferLog.query.get(model_id)

            if not model:
                return err_not_found()

            if args['station_id']:
                model.station_name = args['station_id']

            if args['level']:
                model.level = args['level']

            if args['time']:
                model.time = args['time']

            if args['note']:
                model.note = args['note']

            db.session.add(model)
            db.session.commit()
            return rp_modify()

        else:
            model = TransferLog(
                station_id=args['station_id'],
                level=args['level'],
                time=args['time'],
                note=args['note'],
            )
            db.session.add(model)
            db.session.commit()
            return rp_create()
