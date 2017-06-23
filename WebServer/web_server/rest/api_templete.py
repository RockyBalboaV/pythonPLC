from flask import abort, jsonify
from flask_restful import reqparse, Resource, marshal_with, fields

from web_server.models import *
from web_server.rest.parsers import station_parser, station_put_parser
from err import err_not_found
from response import rp_create, rp_delete, rp_modify


class ApiResource(Resource):
    def __init__(self, ):
        pass

    def search(self, id):
        pass

    def information(self, models):
        pass

    def get(self, id=None):

        models = self.search(id)

        response = self.information(models)

        return response

    def post(self, id=None):

        models = self.search(id)

        response = self.information(models)

        return response

    def put(self, id=None):
        pass

    def delete(self, id=None):

        models = self.search(id)
        count = len(models)

        if not models:
            return err_not_found()

        for m in models:
            db.session.delete(m)
        db.session.commit()

        return rp_delete(count)
