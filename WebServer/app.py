# coding=utf-8
import json, hmac, chardet, base64, os, random, simplejson, datetime, zlib

from flask import Flask, abort, request, jsonify, redirect, g, render_template
from ext import db, mako, hashing
from models import *

import MySQLdb
from pandas.io.sql import read_sql

app = Flask(__name__, template_folder='templates')
app.config.from_object('config')

mako.init_app(app)
db.init_app(app)
hashing.init_app(app)


def get_current_user():
    users = User.query.all()
    return random.choice(users)


def encryption(data):
    """
    :param data: dict
    :return: dict
    """

    h = hmac.new(b'poree')
    data = unicode(data)
    # data = base64.b64encode(data)
    h.update(bytes(data))
    data = zlib.compress(data)
    data = base64.b64encode(data)
    digest = h.hexdigest()
    data = {"data": data, "digest": digest}
    return data


def decryption(rj):
    """
    :param rj: json
    :return: dict
    """

    data = rj['data']
    di = rj['digest']
    data = base64.b64decode(data)
    data = zlib.decompress(data)
    h = hmac.new(b'poree')
    h.update(bytes(data))
    test = h.hexdigest()
    if di == test:
        # data = base64.b64decode(data)
        data = json.loads(data.replace("'", '"'))
    return data


@app.before_first_request
def setup():
    #db.drop_all()
    #db.create_all()
    fake_users = [
        User('xiaoming', '3'),
        User('wangzhe', '2'),
        User('admin', '1')
    ]
    db.session.add_all(fake_users)
    db.session.commit()


@app.before_request
def before_request():
    g.user = get_current_user()


@app.teardown_appcontext
def teardown(exc=None):
    if exc is None:
        db.session.commit()
    else:
        db.session.rollback()
    db.session.remove()
    g.user = None


@app.context_processor
def template_extras():
    return {'enumerate': enumerate, 'current_user': g.user}


@app.template_filter('capitalize')
def reverse_filter(s):
    return s.capitalize()


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        rv = request.get_json(force=True)
        data = decryption(rv)
        uploaded_data = YjPLCInfo.query.filter_by(id=data["id"]).first()
        if uploaded_data:
            uploaded_data = YjPLCInfo.query.all()
            return render_template('index_post.html', uploaded_data=uploaded_data)
        else:
        #    while su:
        #        try:
            uploaded_data = YjPLCInfo(name=data["name"], id=data["id"], tenid=data["tenid"])
            #todo 当输入值的键不存在时,怎么使用默认值代替
        #            su = True
        #        except KeyError as a:
        #            data[a] = None
        #print uploaded_data.id
        #print data
        #upload_data = YjPLCInfo.upload(data)
        db.session.add(uploaded_data)
        db.session.commit()
        uploaded_data = YjPLCInfo.query.all()
        return render_template('index_post.html', uploaded_data=uploaded_data)
    users = User.query.all()
    return render_template('index.html', users=users)


@app.route('/beats', methods=['POST'])
def beats():
    data = request.get_json(force=True)
    #data = decryption(rv)
    print data["idnum"]
    plc = YjStationInfo.query.filter_by(idnum=data["idnum"]).first()
    print plc
    plc.con_date = datetime.datetime.utcnow()
    db.session.add(plc)
    db.session.commit()
    print plc.modification
    if plc.modification:
        data = {"modification": "True"}
        #data = encryption(data)
        return jsonify(data)
    else:
        data = {"modification": "False"}
        #data = encryption(data)
    return jsonify(data)


@app.route('/config', methods=['GET', 'POST'])
def set_config():
    if request.method == 'POST':
        data = request.get_json(force=True)
        # data = decryption(data)
        config_station = YjStationInfo.query.filter_by(idnum=data["idnum"]).first()
        station_config = {}
        for c in config_station.__table__.columns:
            station_config[c.name] = str(getattr(config_station, c.name, None))
        print station_config

        plcs_config = []
        groups_config = []
        variables_config = []
        for plc in config_station.plcs.all():
            plc_config = {}
            for c in plc.__table__.columns:
                plc_config[c.name] = str(getattr(plc, c.name, None))
            plcs_config.append(plc_config)

            for group in plc.groups.all():
                group_config = {}
                for c in group.__table__.columns:
                    group_config[c.name] = str(getattr(group, c.name, None))
                groups_config.append(group_config)

            for variable in plc.variables.all():
                variable_config = {}
                for c in variable.__table__.columns:
                    variable_config[c.name] = str(getattr(variable, c.name, None))
                variables_config.append(variable_config)

        print plcs_config
        print groups_config
        print variables_config

        # get value into list
        # (1)a=[]
        #     a.append([value for key, value in plc_config.items()])

        # (2)out_list = []
        # for a in station_config.keys():
        #     out_list.append(station_config.get(a))

        data = {"YjStationInfo": station_config, "YjPLCInfo": plcs_config,
                "YjGroupInfo": groups_config, "YjVariableInfo": variables_config}
        # data = encryption(data)
        return jsonify(data)


def _get_frame(date_string):
    db = MySQLdb.connect('localhost', 'web', 'web', 'pyplc')
    query = 'SELECT * FROM {}'.format(date_string)
    df = read_sql(query, db)
    df = df.head(100)
    return df


@app.route('/db/<any(yjstationinfo, yjplcinfo, yjgroupinfo, yjvariableinfo):date_string>/')
def show_tables(date_string=None):
    df = _get_frame(date_string)
    if isinstance(df, bool) and not df:
        return 'Bad data format!'
    return render_template('show_data.html', df=df.to_html(classes='frame'), date_string=date_string)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=11000, debug=True)
