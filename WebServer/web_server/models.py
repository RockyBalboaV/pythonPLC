#coding=utf-8
import os
import datetime
import time

from flask import current_app
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin, AnonymousUserMixin
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer, BadSignature, SignatureExpired

from ext import db


def check_int(column):
    if column:
        return int(column)
    else:
        return column


roles = db.Table('role_users',
                 db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
                 db.Column('role_id', db.Integer, db.ForeignKey('role.id')))


class YjStationInfo(db.Model):

    __tablename__ = 'yjstationinfo'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(30))
    mac = db.Column(db.String(20))
    ip = db.Column(db.String(20))
    note = db.Column(db.String(200))
    id_num = db.Column(db.String(200))
    plc_count = db.Column(db.Integer)
    ten_id = db.Column(db.String(255))
    item_id = db.Column(db.String(20))
    con_date = db.Column(db.Integer)
    modification = db.Column(db.Integer)
    version = db.Column(db.Integer, autoincrement=True)

    plcs = db.relationship('YjPLCInfo', backref='yjstationinfo', lazy='dynamic')

    logs = db.relationship('TransferLog', backref='yjstationinfo', lazy='dynamic')

    def __init__(self, name=None, mac=None, ip=None, note=None, id_num=None,
                 plc_count=None, ten_id=None, item_id=None, con_date=None, modification=0):
        self.name = name
        self.mac = mac
        self.ip = ip
        self.note = note
        self.id_num = id_num
        self.plc_count = check_int(plc_count)
        self.ten_id = ten_id
        self.item_id = item_id
        if con_date is None:
            con_date = int(time.time())
        self.con_date = con_date
        self.modification = modification

    def __repr__(self):
        return '<Station : ID(%r) Name(%r) >' % self.id, self.name


class YjPLCInfo(db.Model):

    __tablename__ = 'yjplcinfo'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(30))
    note = db.Column(db.String(200))
    ip = db.Column(db.String(30))
    mpi = db.Column(db.Integer)
    type = db.Column(db.Integer)
    plc_type = db.Column(db.String(20))
    ten_id = db.Column(db.String(255))
    item_id = db.Column(db.String(20))

    station_id = db.Column(db.Integer, db.ForeignKey('yjstationinfo.id'))

    variables = db.relationship('YjVariableInfo', backref='yjplcinfo', lazy='dynamic')
    groups = db.relationship('YjGroupInfo', backref='yjplcinfo', lazy='dynamic')

    def __init__(self, name=None, station_id=None, note=None, ip=None,
                 mpi=None, type=None, plc_type=None,
                 ten_id=0, item_id=None):

        self.name = name
        self.station_id = station_id
        self.note = note
        self.ip = ip
        self.mpi = check_int(mpi)
        self.type = type
        self.plc_type = plc_type
        self.ten_id = ten_id
        self.item_id = item_id

    def __repr__(self):
        return '<PLC : ID(%r) Name(%r) >' % (int(self.id), self.name)


class YjGroupInfo(db.Model):

    __tablename__ = 'yjgroupinfo'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    group_name = db.Column(db.String(20))
    note = db.Column(db.String(100))
    upload_cycle = db.Column(db.Integer)
    ten_id = db.Column(db.String(255))
    item_id = db.Column(db.String(20))

    plc_id = db.Column(db.Integer, db.ForeignKey('yjplcinfo.id'))

    variables = db.relationship('YjVariableInfo', backref='yjgroupinfo', lazy='dynamic')

    def __init__(self, group_name=None, plc_id=None, note=None,
                 upload_cycle=None, ten_id=None, item_id=None):
        self.group_name = group_name
        self.plc_id = check_int(plc_id)
        self.note = note
        self.upload_cycle = check_int(upload_cycle)
        self.ten_id = ten_id
        self.item_id = item_id

    def __repr__(self):
        return '<Group :ID(%r) Name(%r) >' % (int(self.id), self.group_name)


class YjVariableInfo(db.Model):

    __tablename__ = 'yjvariableinfo'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    tag_name = db.Column(db.String(20))
    address = db.Column(db.String(20))
    data_type = db.Column(db.String(10))
    rw_type = db.Column(db.Integer)
    upload = db.Column(db.Integer)
    acquisition_cycle = db.Column(db.Integer)
    server_record_cycle = db.Column(db.Integer)
    note = db.Column(db.String(50))
    ten_id = db.Column(db.String(200))
    item_id = db.Column(db.String(20))

    plc_id = db.Column(db.Integer, db.ForeignKey('yjplcinfo.id'))
    group_id = db.Column(db.Integer, db.ForeignKey('yjgroupinfo.id'))

    values = db.relationship('Value', backref='yjvariableinfo', lazy='dynamic')

    def __init__(self, tag_name=None, plc_id=None, group_id=None, address=None,
                 data_type=None, rw_type=None, upload=None,
                 acquisition_cycle=None, server_record_cycle=None,
                 note=None, ten_id=None, item_id=None):
        self.tag_name = tag_name
        self.plc_id = plc_id
        self.group_id = group_id
        self.address = address
        self.data_type = data_type
        self.rw_type = check_int(rw_type)
        self.upload = check_int(upload)
        self.acquisition_cycle = check_int(acquisition_cycle)
        self.server_record_cycle = check_int(server_record_cycle)
        self.note = note
        self.ten_id = ten_id
        self.item_id = item_id

    def __repr__(self):
        return '<Variable :ID(%r) Name(%r) >' % (int(self.id), self.tag_name)


class Value(db.Model):

    __tablename__ = 'values'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    variable_id = db.Column(db.Integer, db.ForeignKey('yjvariableinfo.id'))
    value = db.Column(db.String(128))
    time = db.Column(db.Integer)

    def __init__(self, variable_id, value, time=None):
        self.variable_id = variable_id
        self.value = value
        self.time = time

    def __repr__(self):
        return '<Value {} {} {} {}'.format(int(self.id), self.variable_id, self.value, self.time)


class User(UserMixin, db.Model):

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(32), nullable=False)
    email = db.Column(db.String(32))
    pw_hash = db.Column(db.String(128))
    login_count = db.Column(db.Integer, default=0)
    last_login_ip = db.Column(db.String(64), default='unknown')

    roles = db.relationship(
        'Role',
        secondary=roles,
        backref=db.backref('user', lazy='dynamic')
    )

    def __init__(self, username, password):
        self.username = username
        # self.set_password(password)
        self.pw_hash = password

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
        user = User.query.get(data['id'])
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
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(30), unique=True)
    description = db.Column(db.String(255))

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


