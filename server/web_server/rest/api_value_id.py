import time
from flask_restful import reqparse, Resource, marshal_with, fields, marshal

from web_server.models import YjVariableInfo, db

value_id = {
    'variable_id': fields.List(fields.Integer)
}


class VariableIDResource(Resource):
    def get(self):
        # time1 = time.time()
        # models = db.session.query(YjVariableInfo.id)
        # variable_id = [model[0] for model in models]
        sql = 'select yjvariableinfo.id from yjvariableinfo'
        models = db.engine.execute(sql).fetchall()
        variable_id = [model[0] for model in models]
        # time2 = time.time()
        # print(time2 - time1)
        return variable_id

#     def get(self):
#         import time
#
#         time1 = time.time()
#         models = db.session.query(YjVariableInfo.id).all()
#         variable_id = dict(variable_id=[model[0] for model in models])
#         time2 = time.time()
#         print(time2 - time1)
#         return variable_id
