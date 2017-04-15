# coding=utf-8
import json, hmac, base64, os, random, zlib
from flask import Flask, abort, request, jsonify, redirect, g, render_template
from flask_socketio import SocketIO
from celery import Celery
from ext import mako, hashing
from models import *

import MySQLdb
from pandas.io.sql import read_sql

import eventlet
eventlet.monkey_patch()

app = Flask(__name__, template_folder='templates')
app.config.from_object('config')
here = os.path.abspath(os.path.dirname(__file__))
app.config.from_pyfile(os.path.join(here, 'celeryconfig.py'))

mako.init_app(app)
db.init_app(app)
hashing.init_app(app)

SOCKETIO_REDIS_URL = app.config['CELERY_RESULT_BACKEND']
socketio = SocketIO(
    app, async_mode='eventlet',
    message_queue=SOCKETIO_REDIS_URL
)

celery = Celery(app.name)
celery.conf.update(app.config)


def value2dict(std):
    return {
        "id": std.id,
        "variable_id": std.variable_id,
        "value": std.value
    }


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
    else:
        data = {"status": "Error"}
    return data


@app.before_first_request
def setup():
    # db.drop_all()
    # db.create_all()
    # fake_users = [
    #     User('xiaoming', '3'),
    #     User('wangzhe', '2'),
    #     User('admin', '1')
    # ]
    # db.session.add_all(fake_users)
    # db.session.commit()
    pass


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


@celery.task
def station_check():
    with app.app_context():
        current_time = datetime.datetime.now()
        stations = db.session.query(YjStationInfo)
        for s in stations:
            s_log = TransferLog.query.filter_by(idnum=s.idnum).order_by(TransferLog.time.desc()).first()
            if s_log:
                last_time = s_log.time
                last_level = s_log.level
                if (current_time - last_time).seconds > 5 and (current_time - last_time).days == 0:
                    warn_level = last_level + 1
                    if warn_level > 2:
                        warn = TransferLog(idnum=s.idnum, level=3, time=current_time, note='ERROR')
                    else:
                        warn = TransferLog(idnum=s.idnum, level=last_level + 1, time=current_time, note='WARNING')
                else:
                    warn = TransferLog(idnum=s.idnum, level=0, time=current_time, note='OK')
            else:
                warn = TransferLog(idnum=s.idnum, level=0, time=current_time, note='OK')
            db.session.add(warn)
            db.session.commit()


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        data = request.get_json(force=True)
        # data = decryption(rv)
        uploaded_data = YjPLCInfo.query.filter_by(id=data["id"]).first()
        if uploaded_data:
            uploaded_data = YjPLCInfo.query.all()
            return render_template('index_post.html', uploaded_data=uploaded_data)
        else:
            uploaded_data = YjPLCInfo(name=data["name"], id=data["id"], tenid=data["tenid"])
            # todo 当输入值的键不存在时,怎么使用默认值代替
        db.session.add(uploaded_data)
        db.session.commit()
        uploaded_data = YjPLCInfo.query.all()
        return render_template('index_post.html', uploaded_data=uploaded_data)
    users = User.query.all()
    return render_template('index.html', users=users)


@app.route('/beats', methods=['GET', 'POST'])
def beats():
    data = request.get_json(force=True)
    # data = decryption(rv)
    station = YjStationInfo.query.filter_by(idnum=data["idnum"]).first()
    station.con_date = datetime.datetime.now()
    db.session.add(station)
    db.session.commit()
    data = {"modification": station.modification, "status": "OK"}
    # data = encryption(data)
    return jsonify(data)


@app.route('/config', methods=['GET', 'POST'])
def set_config():
    if request.method == 'POST':
        data = request.get_json(force=True)
        # 将本次发送过配置的站点数据表设置为无更新
        db.session.query(YjStationInfo).filter(YjStationInfo.idnum == data["idnum"]).update({YjStationInfo.modification: 0})
        # data = decryption(data)
        # 读取数据库中staion数据,再根据外链,读出该station下的plc数据,以及group variable的数据.每一项数据为一个字典,每个表中所有数据存为一个列表.
        config_station = YjStationInfo.query.filter_by(idnum=data["idnum"]).first()
        station_config = {}
        for c in config_station.__table__.columns:
            station_config[c.name] = str(getattr(config_station, c.name, None))

        plcs_config = []
        groups_config = []
        variables_config = []
        # print config_station.plcs.all()
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

        # get value into list
        # (1)a=[]
        #     a.append([value for key, value in plc_config.items()])

        # (2)out_list = []
        # for a in station_config.keys():
        #     out_list.append(station_config.get(a))

        data = {"YjStationInfo": station_config, "YjPLCInfo": plcs_config,
                "YjGroupInfo": groups_config, "YjVariableInfo": variables_config,
                "status": "OK"}
        # data = encryption(data)
        return jsonify(data)


@app.route('/upload', methods=['POST'])
def upload():
    if request.method == 'POST':
        data = request.get_json(force=True)
        # data = decryption(data)
        for v in data["Value"]:
            # 如何使用字典方式,使得在建立Value实例时可以获取任意多少的键值
            # for key, value in v.items():
            #    print key, value
            # upload_data = Value({}={}).format(key, value) for key, value in v.items()
            upload_data = Value(variable_name=v["variable_name"], value=v["value"], get_time=v["get_time"])
            db.session.add(upload_data)
        db.session.commit()
        values = data["Value"]
        return jsonify({"input": [json.dumps(v, default=value2dict) for v in values],
                        "status": "OK",
                        "station_id": "123456"})


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
    socketio.run(app, host='0.0.0.0', port=11000, debug=True)
    # app.run(host='0.0.0.0', port=11000, debug=True)
