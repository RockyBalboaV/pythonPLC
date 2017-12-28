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
from web_server.rest.api_user import UserResource
from web_server.rest.api_interface_log import InterfaceLogResource
from web_server.rest.api_param import ParameterResource
from web_server.rest.api_value_id import VariableIDResource
from web_server.rest.err import custom_errors

api_blueprint = Blueprint(
    'api',
    __name__,
    template_folder=path.join(path.pardir, 'templates', 'api'),
    url_prefix='/api'
)

api = Api(api_blueprint)
api.add_resource(AuthApi, '/auth')
api.add_resource(StationResource, '/station', endpoint='yjstationinfo')
api.add_resource(PLCResource, '/plc', endpoint='yjplcinfo')
api.add_resource(GroupResource, '/group', endpoint='yjgroupinfo')
api.add_resource(VariableResource, '/variable', endpoint='yjvariableinfo')
api.add_resource(ValueResource, '/value', endpoint='value')
api.add_resource(StatusResource, '/status', endpoint='transferlog')
api.add_resource(QueryResource, '/query', endpoint='querygroup')
api.add_resource(AlarmInfoResource, '/alarm_info', endpoint='varalarminfo')
api.add_resource(AlarmLogResource, '/alarm_log', endpoint='varalarmlog')
api.add_resource(UserResource, '/user', endpoint='user')
api.add_resource(InterfaceLogResource, '/interface_log', endpoint='interfacelog')
api.add_resource(ParameterResource, '/param', endpoint='parameter')
api.add_resource(VariableIDResource, '/variable_id')
