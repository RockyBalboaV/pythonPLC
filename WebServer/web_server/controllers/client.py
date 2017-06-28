# coding=utf-8

from os import path

from flask import Blueprint, request, jsonify, render_template, redirect, url_for, current_app, flash, Config

from flask_login import login_user, logout_user, user_logged_in, login_required, current_user
from flask_principal import identity_loaded, identity_changed, UserNeed, RoleNeed, Identity, AnonymousIdentity

from web_server.ext import csrf, api
from web_server.models import *

client_blueprint = Blueprint('client',
                           __name__,
                           template_folder=path.join(path.pardir, 'templates', 'client'),
                           url_prefix='/client')


@client_blueprint.route('/beats', methods=['GET', 'POST'])
def beats():
    data = request.get_json(force=True)
    # data = decryption(rv)

    station = YjStationInfo.query.filter_by(id=data["station_id"]).first()
    station.con_date = int(time.time())

    if station.version != data["version"]:
        station.modification = 1

    db.session.add(station)
    db.session.commit()

    data = {"modification": station.modification, "status": 0}
    # data = encryption(data)
    return jsonify(data)
