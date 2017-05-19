# coding=utf-8
from flask_restful import reqparse, Resource, marshal_with, fields

from models import *

variable_field = {
    'id': fields.Integer,
    'tagname': fields.String,
    'plcid': fields.Integer,
    'groupid': fields.Integer,
    'address': fields.String,
    'datatype': fields.String,
    'rwtype': fields.Integer,
    'upload': fields.Integer,
    'acquisitioncycle': fields.Integer,
    'serverrecordcycle': fields.Integer,
    'writevalue': fields.String,
    'note': fields.String,
    'tenid': fields.String,
    'itemid': fields.String
}


class VariableResource(Resource):
    @marshal_with(variable_field)
    def get(self, name):
        variable = YjVariableInfo.query.filter_by(tagname=name).first()
        return variable