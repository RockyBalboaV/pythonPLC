# coding=utf-8
import datetime
import time

import json

from flask import jsonify, url_for
from flask_restful import abort

from web_server.models import db, Parameter, Value
from web_server.rest.parsers import param_parser
from api_templete import ApiResource
from err import err_not_found, err_not_contain
from response import rp_create, rp_delete, rp_modify, rp_delete_ration


class ParameterResource(ApiResource):
    def __init__(self):
        self.args = param_parser.parse_args()
        super(ParameterResource, self).__init__()
        self.query = Parameter.query

        self.model_id = self.args['id']

        self.param_name = self.args['param_name']
        self.variable_id = self.args['variable_id']
        self.unit = self.args['unit']

        self.limit = self.args['limit']
        self.page = self.args['page']
        self.per_page = self.args['per_page'] if self.args['per_page'] else 10

    def search(self):

        if self.model_id:
            self.query = self.query.filter_by(id=self.model_id)

        if self.param_name:
            self.query = self.query.filter_by(param_name=self.param_name)

        if self.variable_id:
            self.query = self.query.filter_by(variable_id=self.variable_id)

        if self.unit:
            self.query = self.query.filter_by(unit=self.unit)

        if self.limit:
            self.query = self.query.limit(self.limit)

        if self.page:
            self.query = self.query.paginate(self.page, self.per_page, False).items
        else:
            self.query = self.query.all()

        if not self.query:
            abort(404, msg='查询结果为空', ok=0)

        return self.query

    def information(self, models):
        info = [
            dict(
                id=m.id,
                param_name=m.param_name,
                variable_id=m.variable_id,
                unit=m.unit,
            )
            for m in models
        ]

        for m in info:
            try:
                value = db.session.query(Value.value).filter(
                    Value.variable_id == m['variable_id']).order_by(Value.time.desc()).first()[0]
            except TypeError:
                value = None
            m['value'] = value

        response = jsonify({"ok": 1, "data": info})

        return response

    def put(self):

        if self.model_id:

            model = Parameter.query.get(self.model_id)

            if not model:
                return err_not_found()

            if self.param_name:
                model.param_name = self.param_name

            if self.variable_id:
                model.variable_id = self.variable_id

            if self.unit:
                model.unit = self.unit

            db.session.add(model)
            db.session.commit()
            return rp_modify()

        else:
            model = Parameter(
                variable_id=self.variable_id,
                param_name=self.param_name,
                unit=self.unit
            )
            db.session.add(model)
            db.session.commit()
            return rp_create()
