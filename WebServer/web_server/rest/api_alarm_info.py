# coding=utf-8
import datetime
import time

from flask import abort, jsonify

from web_server.models import *
from web_server.rest.parsers import alarm_info_parser, alarm_info_put_parser
from api_templete import ApiResource
from err import err_not_found
from response import rp_create, rp_delete, rp_modify


class AlarmInfoResource(ApiResource):
    def __init__(self):
        self.args = alarm_info_parser.parse_args()
        super(AlarmInfoResource, self).__init__()

    def search(self):

        model_id = self.args['id']

        plc_id = self.args['plc_id']
        variable_id = self.args['variable_id']
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
            query = query.join(YjVariableInfo, YjGroupInfo).filter(YjGroupInfo.plc_id.in_(plc_id))

        if variable_id:
            query = query.filter(VarAlarmInfo.variable_id.in_(variable_id))

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
                plc_id=m.yjvariableinfo.yjgroupinfo.plc_id if m.yjvariableinfo and m.yjvariableinfo.yjgroupinfo else None,
                variable_id=m.variable_id,
                variable_name=m.yjvariableinfo.variable_name if m.yjvariableinfo else None,
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
            model = VarAlarmInfo.query.get(model_id)

            if not model:
                return err_not_found()

            if args['variable_id']:
                model.variable_id = args['variable_id']

            if args['alarm_type']:
                model.alarm_type = args['alarm_type']

            if args['note']:
                model.note = args['note']

            db.session.add(model)
            db.session.commit()
            return rp_modify()

        else:
            model = VarAlarmInfo(
                variable_id=args['variable_id'],
                alarm_type=args['alarm_type'],
                note=args['note']
            )
            db.session.add(model)
            db.session.commit()
            return rp_create()
