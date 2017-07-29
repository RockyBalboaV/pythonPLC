# coding=utf-8

from os import path

from flask import Blueprint, request, jsonify, render_template, redirect, url_for, current_app, flash, Config

from flask_login import login_user, logout_user, user_logged_in, login_required, current_user
from flask_principal import identity_loaded, identity_changed, UserNeed, RoleNeed, Identity, AnonymousIdentity

from web_server.ext import csrf, api
from web_server.models import *
from web_server.util import get_data_from_query, get_data_from_model

client_blueprint = Blueprint('client',
                             __name__,
                             template_folder=path.join(path.pardir, 'templates', 'client'),
                             url_prefix='/client')


def make_response(status, status_code, **kwargs):
    msg = {
        'status': status
    }
    msg.update(kwargs)
    response = jsonify(msg)
    response.status_code = status_code

    return response


def configuration(station_model):
    # 读取staion表数据,根据外链,读出该station下的plc、group variable的数据.每一项数据为一个字典,每个表中所有数据存为一个列表.
    plcs_config = []
    groups_config = []
    variables_config = []

    station_config = get_data_from_model(station_model)

    plcs = station_model.plcs.all()
    if plcs:
        plcs_config = get_data_from_query(plcs)
        for plc in plcs:

            groups = plc.groups.all()
            if groups:
                groups_config += get_data_from_query(groups)

            variables = plc.variables.all()
            if variables:
                variables_config += get_data_from_query(variables)

    # 包装数据
    data = {"YjStationInfo": station_config, "YjPLCInfo": plcs_config,
            "YjGroupInfo": groups_config, "YjVariableInfo": variables_config}

    return data


# def station_config(station_model):
#     station_dict = dict()
#     station_dict['id'] = station_model.id
#     station_dict['station_name'] = station_model.station_name
#     station_dict['id_num'] = station_model.id_num
#     station_dict['ip'] = station_model.ip
#     station_dict['item_id'] = station_model.item_id
#     station_dict['ten_id'] = station_model.ten_id
#     station_dict['version'] = station_model.version
#     station_dict['plc_count'] = station_model.plc_count
#     station_dict['mac'] = station_model.mac
#     station_dict['note'] = station_model.note
#     return station_dict
#
#
# def plc_config(plc_model):
#     plc_dict = dict()
#     plc_dict['id'] = plc_model.id
#     plc_dict['plc_name'] = plc_model.plc_name
#     plc_dict['station_id'] = plc_model.station_id
#     plc_dict['ip'] = plc_model.ip
#     plc_dict['item_id'] = plc_model.item_id
#     plc_dict['ten_id'] = plc_model.ten_id
#     plc_dict['note'] = plc_model.note
#     plc_dict['plc_type'] = plc_model.plc_type
#     plc_dict['mpi'] = plc_model.mpi
#     plc_dict['type'] = plc_model.type
#     plc_dict['rack'] = plc_model.rack
#     plc_dict['slot'] = plc_model.slot
#     plc_dict['tcp_port'] = plc_model.tcp_port
#     return plc_dict
#
#
# def group_config(group_model):
#     group_dict = dict()
#     group_dict['id'] = group_model.id
#     group_dict['group_name'] = group_model.group_name
#     group_dict['plc_id'] = group_model.plc_id
#     group_dict['item_id'] = group_model.item_id
#     group_dict['ten_id'] = group_model.ten_id
#     group_dict['note'] = group_model.note
#     group_dict['upload_cycle'] = group_model.upload_cycle
#     return group_dict
#
#
# def variable_config(variable_model):
#     variable_dict = dict()
#     variable_dict['id'] = variable_model.id
#     variable_dict['variable_name'] = variable_model.variable_name
#     variable_dict['plc_id'] = variable_model.plc_id
#     variable_dict['group_id'] = variable_model.group_id
#     variable_dict['db_num'] = variable_model.db_num
#     variable_dict['item_id'] = variable_model.item_id
#     variable_dict['ten_id'] = variable_model.ten_id
#     variable_dict['note'] = variable_model.note
#     variable_dict['address'] = variable_model.address
#     variable_dict['upload'] = variable_model.upload
#     variable_dict['data_type'] = variable_model.data_type
#     variable_dict['rw_type'] = variable_model.rw_type
#     variable_dict['acquisition_cycle'] = variable_model.acquisition_cycle
#     variable_dict['server_record_cycle'] = variable_model.server_record_cycle
#     variable_dict['write_value'] = variable_model.write_value
#     return variable_dict


@client_blueprint.route('/beats', methods=['GET', 'POST'])
def beats():
    data = request.get_json(force=True)
    # data = decryption(rv)

    station = YjStationInfo.query.filter_by(id_num=data["station_id_num"]).first()
    station.con_date = int(time.time())

    if station.version != data["version"]:
        station.modification = 1

    db.session.add(station)
    db.session.commit()

    data = {"modification": station.modification, "status": 'OK'}
    # data = encryption(data)
    return jsonify(data)


@client_blueprint.route('/config', methods=['GET', 'POST'])
def set_config():
    if request.method == 'POST':
        data = request.get_json(force=True)

        station = db.session.query(YjStationInfo).filter_by(id_num=data["station_id_num"]).first_or_404()
        # data = decryption(data)

        # data = configuration(station)
        data = {"YjStationInfo": serialize(station),
                "YjPLCInfo": [serialize(plc) for plc in station.plcs],
                "YjGroupInfo": [serialize(group) for plc in station.plcs for group in plc.groups],
                "YjVariableInfo": [serialize(variable) for plc in station.plcs for variable in plc.variables]}

        # 将本次发送过配置的站点数据表设置为无更新
        station.modification = 0

        db.session.add(station)
        db.session.commit()

        # data = encryption(data)
        response = make_response('OK', 200, data=data)
        return response


@client_blueprint.route('/upload', methods=['POST'])
def upload():
    if request.method == 'POST':
        data = request.get_json(force=True)
        # data = decryption(data)

        # 验证上传数据
        station_id_num = data["station_id_num"]
        version = data["version"]

        # 查询服务器是否有正在上传的站信息
        station = YjStationInfo.query.filter_by(id_num=station_id_num).first_or_404()

        # 查询上传信息的版本是否匹配
        try:
            assert (station.version == version)
        except AssertionError:
            response = make_response('version error', 403)
        else:
            for v in data["value"]:
                value = Value(variable_id=v["variable_id"],
                              value=v["value"],
                              time=v["time"]
                              )
                db.session.add(value)
            db.session.commit()

            response = make_response('OK', 200, station_id_num=station_id_num, version=version)
        return response
