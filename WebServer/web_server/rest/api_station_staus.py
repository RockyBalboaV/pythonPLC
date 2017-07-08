# coding=utf-8
import datetime
import time

from flask import abort, jsonify
from flask_restful import reqparse, Resource, marshal_with, fields

from web_server.models import *
from web_server.rest.parsers import status_parser, status_put_parser
from api_templete import ApiResource
from err import err_not_found
from response import rp_create, rp_delete, rp_modify


class StatusResource(ApiResource):
    def __init__(self):
        super(StatusResource, self).__init__()
        self.args = status_parser.parse_args()

    def search(self, model_id=None):

        if not model_id:
            model_id = self.args['id']

        min_time = self.args['min_time']
        max_time = self.args['max_time']
        order_time = self.args['order_time']
        limit = self.args['limit']
        page = self.args['page']
        per_page = self.args['per_page'] if self.args['per_page'] else 10

        query = TransferLog.query

        if model_id:
            query = query.filter_by(id=model_id)

        if min_time:
            query = query.filter(Value.time > min_time)

        if max_time:
            query = query.filter(Value.time < max_time)

        if order_time:
            query = query.order_by(Value.time.desc())

        # if limit:
        #     query = query.limit(limit)

        if page:
            query = query.paginate(page, per_page, False).items
        elif limit:
            query = db.session.query(TransferLog.station_id).distinct().group_by(TransferLog.station_id).all()
            l = list()
            for q in query:
                model = TransferLog.query.filter_by(station_id=q[0]).order_by(TransferLog.time.desc()).limit(
                    limit).all()
                l += model
            query = l
        else:
            query = query.all()

        # print query

        return query

    def information(self, models):
        if not models:
            return err_not_found()

        info = []
        for m in models:
            data = dict()
            data['id'] = m.id
            data['station_id'] = m.station_id
            data['level'] = m.level
            data['note'] = m.note
            data['time'] = m.time

            info.append(data)

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
            model = TransferLog(station_id=args['station_id'],
                                level=args['level'],
                                time=args['time'],
                                note=args['note'],
                                )
            db.session.add(model)
            db.session.commit()
            return rp_create()
