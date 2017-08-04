# coding=utf-8
from flask import abort, jsonify

from web_server.models import *
from web_server.rest.parsers import group_parser, group_put_parser
from api_templete import ApiResource
from err import err_not_found
from response import rp_create, rp_delete, rp_modify


class GroupResource(ApiResource):
    def __init__(self):
        self.args = group_parser.parse_args()
        super(GroupResource, self).__init__()

    def search(self):

        group_id = self.args['id']

        group_name = self.args['group_name']
        plc_id = self.args['plc_id']
        plc_name = self.args['plc_name']

        limit = self.args['limit']
        page = self.args['page']
        per_page = self.args['per_page'] if self.args['per_page'] else 10

        query = YjGroupInfo.query

        if group_id:
            query = query.filter_by(id=group_id)

        if group_name:
            query = query.filter_by(group_name=group_name)

        if plc_id:
            query = query.filter_by(plc_id=plc_id)

        if plc_name:
            query = query.join(YjPLCInfo, YjPLCInfo.plc_name == plc_name)

        if limit:
            query = query.limit(limit)

        if page:
            query = query.paginate(page, per_page, False).items
        else:
            query = query.all()

        return query

    def information(self, group):
        if not group:
            return err_not_found()

        info = []
        for g in group:

            data = dict()
            data['id'] = g.id
            data['group_name'] = g.group_name
            data['plc_id'] = g.plc_id
            data['upload_cycle'] = g.upload_cycle
            data['note'] = g.note
            data['ten_id'] = g.ten_id
            data['item_id'] = g.item_id
            data['upload'] = g.upload

            plc = g.yjplcinfo
            if plc:
                data['plc_name'] = plc.plc_name
            else:
                data['plc_name'] = None

            info.append(data)

        response = jsonify({'ok': 1, "data": info})
        response.status_code = 200

        return response

    def put(self):
        args = group_put_parser.parse_args()

        group_id = args['id']

        if group_id:

            group = YjGroupInfo.query.get(group_id)

            if not group:
                return err_not_found()

            if args['group_name']:
                group.group_name = args['group_name']

            if args['plc_id']:
                group.plc_id = args['plc_id']

            if args['note']:
                group.note = args['note']

            if args['upload_cycle']:
                group.upload_cycle = args['upload_cycle']

            if args['ten_id']:
                group.ten_id = args['ten_id']

            if args['item_id']:
                group.item_id = args['item_id']

            if args['upload']:
                group.item_id = args['upload']

            db.session.add(group)
            db.session.commit()
            return rp_modify()

        else:
            group = YjGroupInfo(
                group_name=args['group_name'],
                plc_id=args['plc_id'],
                note=args['note'],
                upload_cycle=args['upload_cycle'],
                ten_id=args['ten_id'],
                item_id=args['item_id'],
                upload=args['upload']
            )

            db.session.add(group)
            db.session.commit()
            return rp_create()
