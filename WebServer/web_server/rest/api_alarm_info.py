# coding=utf-8
import datetime
import time

from flask import abort, jsonify
from flask_restful import reqparse, Resource, marshal_with, fields, marshal

from web_server.models import *
from web_server.rest.parsers import alarm_info_parser, alarm_info_put_parser
from api_templete import ApiResource
from err import err_not_found
from response import rp_create, rp_delete, rp_modify


class AlarmInfoResource(ApiResource):
    def __init__(self):
        super(AlarmInfoResource, self).__init__()
        self.args = alarm_info_parser.parse_args()

    def search(self, model_id=None):

        if not model_id:
            model_id = self.args['id']

        plc_id = self.args['plc_id']
        alarm_type = self.args['alarm_type']

        limit = self.args['limit']
        page = self.args['page']
        per_page = self.args['per_page'] if self.args['per_page'] else 10

        query = VarAlarmInfo.query

        if model_id:
            query = query.filter_by(id=model_id)

        if alarm_type:
            query = query.filter(VarAlarmInfo.alarm_type.in_(alarm_type))

        if plc_id:
            query = query.filter(VarAlarmInfo.plc_id.in_(plc_id))

        if limit:
            query = query.limit(limit)

        if page:
            query = query.paginate(page, per_page, False).items

        else:
            query = query.all()

        # print query.all()

        return query

    def information(self, models):
        if not models:
            return err_not_found()

        info = [
            dict(
                id=m.id,
                plc_id=m.plc_id,
                db_num=m.db_num,
                address=m.address,
                alarm_type=m.alarm_type,
                note=m.note,
            )
            for m in models
        ]

        response = jsonify({"ok": 1, "data": info})

        return response

    def put(self, model_id=None):
        args = alarm_info_put_parser.parse_args()

        if not model_id:
            model_id = args['id']

        if model_id:
            model = VarAlarmLog.query.get(model_id)

            if not model:
                return err_not_found()

            if args['plc_id']:
                model.alarm_num = args['plc_id']

            if args['db_num']:
                model.alarm_type = args['db_num']

            if args['address']:
                model.time = args['address']

            if args['alarm_type']:
                model.time = args['alarm_type']

            if args['note']:
                model.time = args['note']

            db.session.add(model)
            db.session.commit()
            return rp_modify()

        else:
            model = VarAlarmInfo(
                plc_id=args['plc_id'],
                db_num=args['db_num'],
                address=args['address'],
                alarm_type=args['alarm_type'],
                note=args['note']
            )
            db.session.add(model)
            db.session.commit()
            return rp_create()
