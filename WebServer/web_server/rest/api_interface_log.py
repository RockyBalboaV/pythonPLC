# coding=utf-8
import datetime
import time

import json

from flask import abort, jsonify, url_for

from web_server.models import db, InterfaceLog
from web_server.rest.parsers import interface_parser
from api_templete import ApiResource
from err import err_not_found, err_not_contain
from response import rp_create, rp_delete, rp_modify, rp_delete_ration


class InterfaceLogResource(ApiResource):
    def __init__(self):
        self.args = interface_parser.parse_args()
        super(InterfaceLogResource, self).__init__()
        self.query = InterfaceLog.query

        # time1 = time.time()
        self.model_id = self.args['id']

        self.username = self.args['username']
        self.host_url = self.args['host_url']
        self.method = self.args['method']
        self.repeal = self.args['repeal']

        self.min_time = self.args['min_time']
        self.max_time = self.args['max_time']
        self.order_time = self.args['order_time']

        self.limit = self.args['limit']
        self.page = self.args['page']
        self.per_page = self.args['per_page'] if self.args['per_page'] else 10

        # time2 = time.time()
        # print(time2 - time1)

    def search(self):

        if self.model_id:
            self.query = self.query.filter_by(id=self.model_id)

        if self.username:
            self.query = self.query.filter_by(username=self.username)

        if self.host_url:
            self.query = self.query.filter_by(host_url=self.host_url)

        if self.method:
            self.query = self.query.filter_by(method=self.method)

        if self.min_time:
            self.query = self.query.filter(InterfaceLog.time > self.min_time)

        if self.max_time:
            self.query = self.query.filter(InterfaceLog.time < self.max_time)

        if self.order_time:
            self.query = self.query.order_by(InterfaceLog.time.desc())

        if self.limit:
            self.query = self.query.limit(self.limit)

        if self.page:
            self.query = self.query.paginate(self.page, self.per_page, False).items
        else:
            self.query = self.query.all()

        if not self.query:
            abort(404, msg='查询结果为空', ok=0)

    def information(self, models):

        info = [
            dict(
                id=m.id,
                username=m.username,
                host_url=m.host_url,
                method=m.method,
                time=m.time,
                param=m.param,
                old_data=m.old_data,
                new_data_id=m.new_data_id
            )
            for m in models
        ]

        response = jsonify({"ok": 1, "data": info})

        return response

    def post(self):
        self.search()
        if self.repeal:

            for model in self.query:
                model_dict_list = json.loads(model.old_data)
                model_class = model.endpoint.split('.')[1]

                if model.method == 'put':
                    for m in db.Model.__subclasses__():
                        if m.__name__.lower() == model_class:
                            # 修改
                            print model.new_data_id
                            if hasattr(json.loads(model.param), 'id'):

                                for model_dict in model_dict_list:
                                    model = m.query.get(model_dict['id'])
                                    for item in model_dict.items():
                                        model.__setattr__(item[0], item[1])
                                    db.session.add(model)
                                    db.session.commit()

                            # 新建
                            else:
                                model = m.query.get(model.new_data_id)
                                print model
                                db.session.delete(model)
                                db.session.commit()

                elif model.method == 'delete':
                    for m in db.Model.__subclasses__():
                        if m.__name__.lower() == model_class:
                            for model_dict in model_dict_list:
                                repeal_instance = m()
                                for item in model_dict.items():
                                    print item
                                    repeal_instance.__setattr__(item[0], item[1])
                                db.session.add(repeal_instance)
                                db.session.commit()
                            break
        else:
            response = self.information(self.query)
            return response

    def put(self):

        if self.model_id:

            model = InterfaceLog.query.get(self.model_id)

            if not model:
                return err_not_found()

            if self.username:
                model.username = self.username

            if self.host_url:
                model.host_url = self.host_url

            if self.method:
                model.method = self.method

            db.session.add(model)
            db.session.commit()
            return rp_modify()

    def delete(self):

        self.search()
        count = len(self.query)

        for m in self.query:
            db.session.delete(m)
        db.session.commit()

        return rp_delete(count)
