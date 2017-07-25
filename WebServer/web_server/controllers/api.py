from os import path

from flask import Blueprint, request, jsonify, render_template, redirect, url_for, current_app, flash, Config

from web_server.ext import csrf, Api

from web_server.rest.api_plc import PLCResource
from web_server.rest.api_station import StationResource
from web_server.rest.api_group import GroupResource
from web_server.rest.api_variable import VariableResource
from web_server.rest.api_value import ValueResource
from web_server.rest.api_station_staus import StatusResource
from web_server.rest.api_query import QueryResource
from web_server.rest.api_alarm_log import AlarmLogResource
from web_server.rest.api_alarm_info import AlarmInfoResource
from web_server.rest.auth import AuthApi

api_blueprint = Blueprint('api',
                          __name__,
                          template_folder=path.join(path.pardir, 'templates', 'api'),
                          url_prefix='/api')

api = Api(api_blueprint)
api.add_resource(AuthApi, '/auth')
api.add_resource(StationResource, '/station', '/station/<int:id>')
api.add_resource(PLCResource, '/plc', '/plc/<int:id>')
api.add_resource(GroupResource, '/group', '/group/<int:id>')
api.add_resource(VariableResource, '/variable', '/variable/<int:id>')
api.add_resource(ValueResource, '/value', '/value/<int:id>')
api.add_resource(StatusResource, '/status', '/status/<int:id>')
api.add_resource(QueryResource, '/query', '/query/<int:id>')
api.add_resource(AlarmInfoResource, '/alarm_info', '/alarm_info/<int:id>')
api.add_resource(AlarmLogResource, '/alarm_log', '/alarm_log/<int:id>')
