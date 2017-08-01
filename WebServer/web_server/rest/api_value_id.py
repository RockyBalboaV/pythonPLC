from flask_restful import reqparse, Resource, marshal_with, fields

from web_server.models import YjVariableInfo, db

value_id = {
    'variable_id': fields.List
}


class VariableIDResource(Resource):
    def get(self):
        models = db.session.query(YjVariableInfo.id).all()
        variable_id = [model[0] for model in models]
        return variable_id
