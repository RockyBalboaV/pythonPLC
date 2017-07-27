# coding=utf-8
import datetime
import time

from flask import abort, jsonify

from web_server.models import *
from web_server.rest.parsers import alarm_parser
from api_templete import ApiResource
from err import err_not_found
from response import rp_create, rp_delete, rp_modify


class AlarmLogResource(ApiResource):
    def __init__(self):

        self.args = alarm_parser.parse_args()
        super(AlarmLogResource, self).__init__()

    def search(self, model_id=None):

        if not model_id:
            model_id = self.args['id']

        confirm = self.args['confirm']
        alarm_id = self.args['alarm_id']
        plc_id = self.args['plc_id']
        alarm_type = self.args['alarm_type']

        min_time = self.args['min_time']
        max_time = self.args['max_time']
        order_time = self.args['order_time']
        limit = self.args['limit']
        page = self.args['page']
        per_page = self.args['per_page'] if self.args['per_page'] else 10

        query = VarAlarmLog.query

        if model_id:
            query = query.filter_by(id=model_id)

        if alarm_type:
            query = query.join(VarAlarmInfo, VarAlarmInfo.alarm_type.in_(alarm_type))

        if plc_id:
            query = query.join(VarAlarmInfo, VarAlarmInfo.plc_id.in_(plc_id))

        if alarm_id:
            query = query.filter(VarAlarmLog.alarm_id.in_(alarm_id))

        if confirm:
            query = query.filter_by(confirm=confirm)

        if min_time:
            query = query.filter(VarAlarmLog.time > min_time)

        if max_time:
            query = query.filter(VarAlarmLog.time < max_time)

        if order_time:
            query = query.order_by(VarAlarmLog.time.desc())

        # if limit:
        #     query = query.limit(limit)

        if page:
            query = query.paginate(page, per_page, False).items
        elif limit:
            plc_id_list = plc_id
            print plc_id_list
            query = [model
                     for plc_id in plc_id_list
                     # for model in query.join(VarAlarmInfo, VarAlarmInfo.id == VarAlarmLog.alarm_id).filter(VarAlarmInfo.plc_id == plc_id).limit(limit).all()
                     for model in VarAlarmLog.query.join(VarAlarmInfo).filter(VarAlarmInfo.plc_id == plc_id).limit(limit)
                     # if model.var_alarm_info.plc_id == plc_id
                     ]
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
                alarm_id=m.alarm_id,
                plc_id=m.var_alarm_info.plc_id,
                db_num=m.var_alarm_info.db_num,
                address=m.var_alarm_info.address,
                alarm_type=m.var_alarm_info.alarm_type,
                note=m.var_alarm_info.note,
                time=m.time,
                confirm=m.confirm

            )
            for m in models
        ]

        response = jsonify({"ok": 1, "data": info})

        return response

    def put(self, model_id=None):
        args = alarm_parser.parse_args()

        if not model_id:
            model_id = args['id']

        if model_id:
            model = VarAlarmLog.query.get(model_id)

            if not model:
                return err_not_found()

            if args['alarm_id']:
                model.alarm_id = args['alarm_id']

            if args['confirm']:
                model.confirm = args['confirm']

            if args['time']:
                model.time = args['time']

            db.session.add(model)
            db.session.commit()
            return rp_modify()

        else:
            model = VarAlarmLog(
                alarm_id=args['alarm_id'],
                confirm=args['confirm'],
                time=args['time'],
            )
            db.session.add(model)
            db.session.commit()
            return rp_create()
