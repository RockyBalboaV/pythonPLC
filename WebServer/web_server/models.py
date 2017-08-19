# coding=utf-8
import os
import datetime
import time

from flask import current_app
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin, AnonymousUserMixin
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer, BadSignature, SignatureExpired
from sqlalchemy.orm import class_mapper

from ext import db


def check_int(column):
    if column:
        return int(column)
    else:
        return column


def serialize(model):
    """Transforms a model into a dictionary which can be dumped to JSON."""
    # first we get the names of all the columns on your model
    columns = [c.key for c in class_mapper(model.__class__).columns]
    # then we return their values in a dict
    return dict((c, getattr(model, c)) for c in columns)


roles = db.Table(
    'roles_users',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
    db.Column('role_id', db.Integer, db.ForeignKey('roles.id'), primary_key=True)
)

var_queries = db.Table(
    'variables_queries',
    db.Column('query_id', db.Integer, db.ForeignKey('query_group.id', onupdate="CASCADE", ondelete="CASCADE"),
              primary_key=True),
    db.Column('variable_id', db.Integer, db.ForeignKey('yjvariableinfo.id', onupdate="CASCADE", ondelete="CASCADE"),
              primary_key=True, )
)


class YjStationInfo(db.Model):
    __tablename__ = 'yjstationinfo'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    station_name = db.Column(db.String(30))
    mac = db.Column(db.String(20))
    ip = db.Column(db.String(20))
    note = db.Column(db.String(200))
    id_num = db.Column(db.String(200))
    plc_count = db.Column(db.Integer)
    ten_id = db.Column(db.String(255))
    item_id = db.Column(db.String(20))
    con_time = db.Column(db.Integer)
    modification = db.Column(db.Integer)
    version = db.Column(db.Integer)

    plcs = db.relationship('YjPLCInfo', backref='yjstationinfo', lazy='dynamic',
                           cascade="delete, delete-orphan")

    logs = db.relationship('TransferLog', backref='yjstationinfo', lazy='dynamic')

    def __init__(self, station_name=None, mac=None, ip=None, note=None, id_num=None,
                 plc_count=None, ten_id=None, item_id=None, con_time=int(time.time()), modification=0):
        self.station_name = station_name
        self.mac = mac
        self.ip = ip
        self.note = note
        self.id_num = id_num
        self.plc_count = check_int(plc_count)
        self.ten_id = ten_id
        self.item_id = item_id
        self.con_time = con_time
        self.modification = modification

    def __repr__(self):
        return '<Station : ID(%r) Name(%r) >'.format(self.id, self.name)


class YjPLCInfo(db.Model):
    __tablename__ = 'yjplcinfo'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    plc_name = db.Column(db.String(30))
    note = db.Column(db.String(200))
    ip = db.Column(db.String(30))
    mpi = db.Column(db.Integer)
    type = db.Column(db.Integer)
    plc_type = db.Column(db.String(20))
    ten_id = db.Column(db.String(255))
    item_id = db.Column(db.String(20))

    rack = db.Column(db.Integer)
    slot = db.Column(db.Integer)
    tcp_port = db.Column(db.Integer)

    station_id = db.Column(db.Integer, db.ForeignKey('yjstationinfo.id'))

    groups = db.relationship('YjGroupInfo', backref='yjplcinfo', lazy='dynamic',
                             cascade="delete, delete-orphan")

    def __init__(self, plc_name=None, station_id=None, note=None, ip=None,
                 mpi=None, type=None, plc_type=None,
                 ten_id=None, item_id=None, rack=0, slot=0, tcp_port=102):
        self.plc_name = plc_name
        self.station_id = station_id
        self.note = note
        self.ip = ip
        self.mpi = check_int(mpi)
        self.type = type
        self.plc_type = plc_type
        self.ten_id = ten_id
        self.item_id = item_id
        self.rack = rack
        self.slot = slot
        self.tcp_port = tcp_port

    def __repr__(self):
        return '<PLC : ID(%r) Name(%r) >'.format(self.id, self.plc_name)


class YjGroupInfo(db.Model):
    __tablename__ = 'yjgroupinfo'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    group_name = db.Column(db.String(20))
    note = db.Column(db.String(100))
    upload = db.Column(db.Boolean)
    upload_cycle = db.Column(db.Integer)
    ten_id = db.Column(db.String(255))
    item_id = db.Column(db.String(20))

    plc_id = db.Column(db.Integer, db.ForeignKey('yjplcinfo.id'))

    variables = db.relationship('YjVariableInfo', backref='yjgroupinfo', lazy='dynamic',
                                cascade="delete, delete-orphan")

    def __init__(self, group_name=None, plc_id=None, note=None,
                 upload_cycle=None, upload=True, ten_id=None, item_id=None):
        self.group_name = group_name
        self.plc_id = check_int(plc_id)
        self.note = note
        self.upload_cycle = check_int(upload_cycle)
        self.ten_id = ten_id
        self.item_id = item_id
        self.upload = upload

    def __repr__(self):
        return '<Group :ID(%r) Name(%r) >'.format(self.id, self.group_name)


class YjVariableInfo(db.Model):
    __tablename__ = 'yjvariableinfo'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    variable_name = db.Column(db.String(20))
    db_num = db.Column(db.Integer)
    address = db.Column(db.Float)
    data_type = db.Column(db.String(10))
    rw_type = db.Column(db.Integer)
    upload = db.Column(db.Integer)
    acquisition_cycle = db.Column(db.Integer)
    server_record_cycle = db.Column(db.Integer)
    note = db.Column(db.String(50))
    ten_id = db.Column(db.String(200))
    item_id = db.Column(db.String(20))
    write_value = db.Column(db.Integer)
    area = db.Column(db.Integer)

    group_id = db.Column(db.Integer, db.ForeignKey('yjgroupinfo.id'))

    values = db.relationship('Value', backref='yjvariableinfo', lazy='dynamic', cascade="delete, delete-orphan")
    alarms = db.relationship('VarAlarmInfo', backref='yjvariableinfo', lazy='dynamic', cascade="delete, delete-orphan")
    params = db.relationship('Parameter', backref='yjvariableinfo', lazy='dynamic', cascade="delete, delete-orphan")

    def __init__(self, variable_name=None, group_id=None, db_num=None, address=None,
                 data_type=None, rw_type=None, upload=None,
                 acquisition_cycle=None, server_record_cycle=None,
                 note=None, ten_id=None, item_id=None, write_value=None, area=None):
        self.variable_name = variable_name
        self.group_id = group_id
        self.db_num = db_num
        self.address = address
        self.data_type = data_type
        self.rw_type = rw_type
        self.upload = upload
        self.acquisition_cycle = acquisition_cycle
        self.server_record_cycle = server_record_cycle
        self.note = note
        self.ten_id = ten_id
        self.item_id = item_id
        self.write_value = write_value
        self.area = area

    def __repr__(self):
        return '<Variable :ID(%r) Name(%r) >'.format(self.id, self.tag_name)


class Value(db.Model):
    __tablename__ = 'values'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    variable_id = db.Column(db.Integer, db.ForeignKey('yjvariableinfo.id'))
    value = db.Column(db.String(128))
    time = db.Column(db.Integer)

    def __init__(self, variable_id, value, time):
        self.variable_id = variable_id
        self.value = value
        self.time = time

    def __repr__(self):
        return '<Value {} {} {} {}'.format(self.id, self.variable_id, self.value, self.time)


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(32), nullable=False)
    email = db.Column(db.String(32))
    pw_hash = db.Column(db.String(128))
    login_count = db.Column(db.Integer, default=0)
    last_login_ip = db.Column(db.String(64), default='unknown')
    last_login_time = db.Column(db.Integer)

    roles = db.relationship(
        'Role',
        secondary=roles,
        backref=db.backref('user', lazy='dynamic'),
        passive_deletes=True
    )

    def __init__(self, username, password, email=None):
        self.username = username
        # self.set_password(password)
        self.pw_hash = password
        self.email = email

    def __repr__(self):
        return '<User {}'.format(self.username)

    @staticmethod
    def verify_auth_token(token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except SignatureExpired:
            return None
        except BadSignature:
            return None
        except TypeError:
            return None
        user_id = data['id']
        user = User.query.get(user_id)

        try:
            assert (data['time'] == user.last_login_time)
        except AssertionError:
            return None

        return user

    def is_authenticated(self):
        if isinstance(self, AnonymousUserMixin):
            return False
        else:
            return True

    def is_active(self):
        return True

    def is_anonymous(self):
        if isinstance(self, AnonymousUserMixin):
            return True
        else:
            return False

    def get_id(self):
        return unicode(self.id)

    def set_password(self, password):
        self.pw_hash = generate_password_hash(password)

    def check_password(self, password):
        # return check_password_hash(self.pw_hash, password)
        return self.pw_hash == password


class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(30), unique=True)
    description = db.Column(db.String(64))

    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return '<Role {}>'.format(self.name)


class TransferLog(db.Model):
    __tablename__ = 'logs'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    station_id = db.Column(db.Integer, db.ForeignKey('yjstationinfo.id'))
    level = db.Column(db.Integer)
    time = db.Column(db.Integer)
    note = db.Column(db.String(200))

    def __init__(self, station_id, level, time, note):
        self.station_id = station_id
        self.level = level
        self.time = time
        self.note = note


class QueryGroup(db.Model):
    __tablename__ = 'query_group'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(32))

    vars = db.relationship(
        'YjVariableInfo',
        secondary=var_queries,
        backref=db.backref('querys', lazy='dynamic'),
        cascade="delete, delete-orphan",
        single_parent=True,
    )


class VarAlarm(db.Model):
    __tablename__ = 'var_alarm'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    alarm_id = db.Column(db.Integer, db.ForeignKey('var_alarm_info.id'))
    time = db.Column(db.Integer)


class VarAlarmLog(db.Model):
    __tablename__ = 'var_alarm_log'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    alarm_id = db.Column(db.Integer, db.ForeignKey('var_alarm_info.id'))
    time = db.Column(db.Integer)
    status = db.Column(db.Integer)


class VarAlarmInfo(db.Model):
    __tablename__ = 'var_alarm_info'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    variable_id = db.Column(db.Integer, db.ForeignKey('yjvariableinfo.id'))
    alarm_type = db.Column(db.Integer)
    note = db.Column(db.String(128))

    logs = db.relationship('VarAlarmLog', backref='var_alarm_info', lazy='dynamic', cascade="delete, delete-orphan")
    alarms = db.relationship('VarAlarm', backref='var_alarm_info', lazy='dynamic', cascade="delete, delete-orphan")



class InterfaceLog(db.Model):
    __tablename__ = 'interface_log'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(32))
    host_url = db.Column(db.String(32))
    method = db.Column(db.String(8))
    time = db.Column(db.Integer)
    param = db.Column(db.Text)
    old_data = db.Column(db.Text)
    new_data_id = db.Column(db.Integer)
    endpoint = db.Column(db.String(32))


class Parameter(db.Model):
    __tablename__ = 'parameter'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    variable_id = db.Column(db.Integer, db.ForeignKey('yjvariableinfo.id'))
    param_name = db.Column(db.String(32))
    unit = db.Column(db.String(16))
