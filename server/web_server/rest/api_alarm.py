# coding=utf-8
import datetime
import time

from flask import jsonify

from web_server.models import *
from web_server.rest.parsers import alarm_now_parser, alarm_now_put_parser
from api_templete import ApiResource
from err import err_not_found
from response import rp_create, rp_modify


class AlarmResource(ApiResource):
    def __init__(self):

        self.args = alarm_now_parser.parse_args()
        super(AlarmResource, self).__init__()

    def search(self):

        model_id = self.args['id']

        status = self.args['status']
        alarm_id = self.args['alarm_id']
        variable_id = self.args['variable_id']

        page = self.args['page']
        per_page = self.args['per_page'] if self.args['per_page'] else 10

        query = VarAlarm.query

        if model_id is not None:
            query = query.filter_by(id=model_id)

        if variable_id is not None:
            query = query.join(VarAlarmInfo, YjVariableInfo).filter(YjVariableInfo.id.in_(variable_id))

        if alarm_id is not None:
            query = query.filter(VarAlarm.alarm_id.in_(alarm_id))

        if status is not None:
            query = query.filter_by(status=status)

        # if limit:
        #     query = query.limit(limit)

        if page:
            query = query.paginate(page, per_page, False).items
        else:
            query = query.all()

        # print query.all()

        return query

    def information(self, models):
        if not models:
            return err_not_found()

        info = list()

        for m in models:
            data = dict()
            data['id'] = m.id
            data['alarm_id'] = m.alarm_id
            data['time'] = m.time
            data['status'] = m.status

            alarm_info = m.var_alarm_info
            data['note'] = m.var_alarm_info.note if alarm_info else None
            data['alarm_type'] = m.var_alarm_info.alarm_type if alarm_info else None
            data['variable_id'] = m.var_alarm_info.variable_id if alarm_info else None

            var = m.var_alarm_info.yjvariableinfo if alarm_info else None

            data['variable_name'] = m.var_alarm_info.yjvariableinfo.variable_name if var else None

            group = m.var_alarm_info.yjvariableinfo.yjgroupinfo if var else None
            data['plc_id'] = group.plc_id if group else None

            plc = m.var_alarm_info.yjvariableinfo.yjgroupinfo.yjplcinfo if group else None
            data['plc_name'] = plc.plc_name if plc else None
            data['station_id'] = plc.station_id if plc else None

            station = plc.yjstationinfo if plc else None
            data['station_name'] = station.station_name if station else None

            info.append(data)

        response = jsonify({"ok": 1, "data": info})

        return response

    def put(self):
        args = alarm_now_put_parser.parse_args()

        model_id = args['id']

        if model_id:
            model = VarAlarm.query.get(model_id)

            if not model:
                return err_not_found()

            if args['alarm_id']:
                model.alarm_id = args['alarm_id']

            if args['time']:
                model.time = args['time']

            db.session.add(model)
            db.session.commit()
            return rp_modify()

        else:
            model = VarAlarm(
                alarm_id=args['alarm_id'],
                time=args['time'],
            )
            db.session.add(model)
            db.session.commit()
            return rp_create()
