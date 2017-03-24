#coding=utf-8
import os, datetime
from ext import db

from werkzeug.security import generate_password_hash, check_password_hash

class YjGroupInfo(db.Model):
    __tablename__ = 'yjgroupinfo'
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    groupname = db.Column(db.String(20))

    plcid = db.Column(db.Integer, db.ForeignKey('yjplcinfo.id'))

    note = db.Column(db.String(100))
    uploadcycle = db.Column(db.Integer)
    tenid = db.Column(db.String(255), nullable=False)
    itemid = db.Column(db.String(20))
    # utf8
    variables = db.relationship('YjVariableInfo',
                            backref='yjgroupinfo', lazy='dynamic')

    def __init__(self, id=None, groupname=None , plcid=None, note=None,
                 uploadcycle=None, tenid=None, itemid=None):
        self.id = id
        self.groupname = groupname
        if plcid:
            self.plcid = int(plcid)
        else:
            self.plcid = plcid
        self.note = note
        if uploadcycle:
            self.uploadcycle = int(uploadcycle)
        else:
            self.uploadcycle = uploadcycle
        self.tenid = tenid
        self.itemid = itemid

    def __repr__(self):
        return '<Group : %r >' % self.groupname


class YjPLCInfo(db.Model):
    __tablename__ = 'yjplcinfo'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30))
    # todo db.Integer 原sql文件中用的string类型,和李总确认下
    stationid = db.Column(db.Integer, db.ForeignKey('yjstationinfo.id'))



    note = db.Column(db.String(200))
    ip = db.Column(db.String(30))
    mpi = db.Column(db.Integer)
    type = db.Column(db.Integer)
    plctype = db.Column(db.String(20))
    tenid = db.Column(db.String(255), nullable=False)
    itemid = db.Column(db.String(20))
    #utf8
    variables = db.relationship('YjVariableInfo', backref='yjplcinfo', lazy='dynamic')
    groups = db.relationship('YjGroupInfo', backref='yjplcinfo', lazy='dynamic')

    def __init__(self, id, name=None, stationid=None, note=None, ip=None,
                 mpi=None, type=None, plctype=None,
                 tenid=0, itemid=None):
        self.id = id
        self.name = name
        # self.stationid = stationid
        self.stationid = stationid
        self.note = note
        self.ip = ip
        if mpi:
            self.mpi = int(mpi)
        else:
            self.mpi = mpi
        if type:
            self.type = int(type)
        else:
            self.type = type
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


class YjStationInfo(db.Model):
    __tablename__ = 'yjstationinfo'
    id = db.Column(db.Integer, primary_key=True, nullable=False, autoincrement=7)
    name = db.Column(db.String(30))
    mac = db.Column(db.String(20))
    ip = db.Column(db.String(20))
    note = db.Column(db.String(200))
    idnum = db.Column(db.String(200))
    plcnum = db.Column(db.Integer)
    tenid = db.Column(db.String(255))
    itemid = db.Column(db.String(20))
    con_date = db.Column(db.DateTime)
    modification = db.Column(db.Boolean)

    # AUTO_INCREMENT=7 DEFAULT CHARSET=utf8;

    plcs = db.relationship('YjPLCInfo', backref='yjstationinfo', lazy='dynamic')

    def __init__(self, name=None, mac=None, ip=None, note=None, idnum=None,
                 plcnum=None, tenid=None, itemid=None, con_date = None, modification=None):
        self.name = name
        self.mac = mac
        self.ip = ip
        self.note = note
        self.idnum = idnum
        self.plcnum = int(plcnum)
        self.tenid = tenid
        self.itemid = itemid
        if con_date is None:
            con_date = datetime.datetime.utcnow()
        self.con_date = con_date
        self.modification = modification

    #def __repr__(self):
    #    return '<Station : %r >' % self.name


class YjVariableInfo(db.Model):
    __tablename__ = 'yjvariableinfo'
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    tagname = db.Column(db.String(20))

    plcid = db.Column(db.Integer, db.ForeignKey('yjplcinfo.id'))


    groupid = db.Column(db.Integer, db.ForeignKey('yjgroupinfo.id'))


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
    # utf8

    def __init__(self, id, tagname=None, plc=None, group=None, address=None,
                 datatype=None, rwtype=None, upload=None,
                 acquisitioncycle=None, serverrecordcycle=None,
                 writevalue=None, note=None, tenid=None, itemid=None):
        self.id = id
        self.tagname = tagname
        # self.plcid = int(plcid)
        # self.groupid = int(groupid)

        self.plc = plc
        self.group = group

        self.addrress = address
        self.datatype = datatype
        self.rwtype = int(rwtype)
        self.upload = int(upload)
        self.acquisitioncycle = int(acquisitioncycle)
        self.serverrecordcycle = int(serverrecordcycle)
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
    pw_hash = db.Column(db.String, nullable=False)
    level = db.Column(db.Integer)

    def __init__(self, name, password, level=3):
        self.name = name
        self.set_password(password)
        self.level = level

    def set_password(self, password):
        self.pw_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.pw_hash, password)


