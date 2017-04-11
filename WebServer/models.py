#coding=utf-8
import os, datetime
from ext import db

from werkzeug.security import generate_password_hash, check_password_hash


def check_int(column):
    if column:
        return int(column)
    else:
        return column


class YjStationInfo(db.Model):
    __tablename__ = 'yjstationinfo'
    id = db.Column(db.Integer, primary_key=True, nullable=False, autoincrement=True)
    name = db.Column(db.String(30))
    mac = db.Column(db.String(20))
    ip = db.Column(db.String(20))
    note = db.Column(db.String(200))
    idnum = db.Column(db.String(200))
    plcnum = db.Column(db.Integer)
    tenid = db.Column(db.String(255))
    itemid = db.Column(db.String(20))
    con_date = db.Column(db.DateTime)
    modification = db.Column(db.Integer)
    version = db.Column(db.Integer, autoincrement=True)

    plcs = db.relationship('YjPLCInfo', backref='yjstationinfo', lazy='dynamic')

    def __init__(self, name=None, mac=None, ip=None, note=None, idnum=None,
                 plcnum=None, tenid=None, itemid=None, con_date=None, modification=0):
        self.name = name
        self.mac = mac
        self.ip = ip
        self.note = note
        self.idnum = idnum
        self.plcnum = check_int(plcnum)
        self.tenid = tenid
        self.itemid = itemid
        if con_date is None:
            con_date = datetime.datetime.utcnow()
        self.con_date = con_date
        self.modification = modification

    def __repr__(self):
        return '<Station : %r >' % self.name


class YjPLCInfo(db.Model):
    __tablename__ = 'yjplcinfo'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(30))
    note = db.Column(db.String(200))
    ip = db.Column(db.String(30))
    mpi = db.Column(db.Integer)
    type = db.Column(db.Integer)
    plctype = db.Column(db.String(20))
    tenid = db.Column(db.String(255), nullable=False)
    itemid = db.Column(db.String(20))

    station_id = db.Column(db.Integer, db.ForeignKey('yjstationinfo.id'))

    variables = db.relationship('YjVariableInfo', backref='yjplcinfo', lazy='dynamic')
    groups = db.relationship('YjGroupInfo', backref='yjplcinfo', lazy='dynamic')

    def __init__(self, name=None, station_id=None, note=None, ip=None,
                 mpi=None, type=None, plctype=None,
                 tenid=0, itemid=None):
        self.name = name
        self.station_id = station_id
        self.note = note
        self.ip = ip
        self.mpi = check_int(mpi)
        self.mpi = check_int(mpi)
        self.plctype = plctype
        self.tenid = tenid
        self.itemid = itemid

    def __repr__(self):
        return '<PLC : %r >' % self.name

    @classmethod
    def upload(cls, uploaded_data):
        rst = cls(uploaded_data["name"])
        uploaded_data.save(rst.path)
        with open(rst.path, 'rb') as f:
            dataname = f.name
            uploaded_data = cls.query.filter_by(name=dataname).first()
            if uploaded_data:
                os.remove(rst.path)
                return uploaded_data
        rst.name = dataname
        return rst


class YjGroupInfo(db.Model):
    __tablename__ = 'yjgroupinfo'
    id = db.Column(db.Integer, primary_key=True, nullable=False, autoincrement=True)
    groupname = db.Column(db.String(20))
    note = db.Column(db.String(100))
    uploadcycle = db.Column(db.Integer)
    tenid = db.Column(db.String(255), nullable=False)
    itemid = db.Column(db.String(20))

    plc_id = db.Column(db.Integer, db.ForeignKey('yjplcinfo.id'))

    variables = db.relationship('YjVariableInfo', backref='yjgroupinfo', lazy='dynamic')

    def __init__(self, groupname=None, plc_id=None, note=None,
                 uploadcycle=None, tenid=None, itemid=None):
        self.groupname = groupname
        self.plc_id = check_int(plc_id)
        self.note = note
        self.uploadcycle = check_int(plc_id)
        self.tenid = tenid
        self.itemid = itemid

    def __repr__(self):
        return '<Group : %r >' % self.groupname


class YjVariableInfo(db.Model):
    __tablename__ = 'yjvariableinfo'
    id = db.Column(db.Integer, primary_key=True, nullable=False, autoincrement=True)
    tagname = db.Column(db.String(20))
    address = db.Column(db.String(20))
    datatype = db.Column(db.String(10))
    rwtype = db.Column(db.Integer)
    upload = db.Column(db.Integer)
    acquisitioncycle = db.Column(db.Integer)
    serverrecordcycle = db.Column(db.Integer)
    writevalue = db.Column(db.String(20))
    note = db.Column(db.String(50))
    tenid = db.Column(db.String(200), nullable=False)
    itemid = db.Column(db.String(20))

    plc_id = db.Column(db.Integer, db.ForeignKey('yjplcinfo.id'))
    group_id = db.Column(db.Integer, db.ForeignKey('yjgroupinfo.id'))

    # values = db.relationship('Value', backref='yjvariableinfo', lazy='dynamic')

    def __init__(self, tagname=None, plc_id=None, group_id=None, address=None,
                 datatype=None, rwtype=None, upload=None,
                 acquisitioncycle=None, serverrecordcycle=None,
                 writevalue=None, note=None, tenid=None, itemid=None):
        self.tagname = tagname
        self.plc_id = plc_id
        self.group_id = group_id
        self.address = address
        self.datatype = datatype
        self.rwtype = check_int(rwtype)
        self.upload = check_int(upload)
        self.acquisitioncycle = check_int(acquisitioncycle)
        self.serverrecordcycle = check_int(serverrecordcycle)
        self.writevalue = writevalue
        self.note = note
        self.tenid = tenid
        self.itemid = itemid

    def __repr__(self):
        return '<Variable : %r >' % self.tagname


class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(20), nullable=False)
    pw_hash = db.Column(db.String(128), nullable=False)
    level = db.Column(db.Integer)

    def __init__(self, name, password, level=3):
        self.name = name
        self.set_password(password)
        self.level = check_int(level)

    def set_password(self, password):
        self.pw_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.pw_hash, password)


class Value(db.Model):
    __tablename__ = 'values'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    variable_name = db.Column(db.String(20))
    value = db.Column(db.String(128))
    date = db.Column(db.DateTime)

    def __init__(self, variable_name, value, date=None):
        self.variable_name = variable_name
        self.value = value
        self.get_time = date





