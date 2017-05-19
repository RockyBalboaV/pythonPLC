# coding=utf-8
from flask_restful import reqparse, Resource, marshal_with, fields

from models import *

groups_field = {
    'id': fields.Integer,
    'groupname': fields.String,
    'plcid': fields.Integer,
    'note': fields.String,
    'uploadcycle': fields.Integer,
    'tenid': fields.String,
    'itemid': fields.String
}


class GroupResource(Resource):
    @marshal_with(groups_field)
    def get(self, name):
        groups = YjGroupInfo.query.filter_by(groupname=name).first()
        return groups