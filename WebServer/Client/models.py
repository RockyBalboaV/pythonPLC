# coding=utf-8
import os, datetime
from sqlalchemy import Column, String, Integer, DateTime, Boolean, ForeignKey, create_engine
from sqlalchemy.orm import sessionmaker, relationship, backref
from sqlalchemy.ext.declarative import declarative_base

from consts import DB_URI

eng = create_engine(DB_URI)
# 创建基类
Base = declarative_base()


def check_int(column):
    if column is not unicode("None"):
        return int(column)
    else:
        return column


class YjStationInfo(Base):
    __tablename__ = 'yjstationinfo'
    id = Column(Integer, primary_key=True, nullable=False)
    name = Column(String(30))
    mac = Column(String(20))
    ip = Column(String(20))
    note = Column(String(200))
    idnum = Column(String(200))
    plcnum = Column(Integer)
    tenid = Column(String(255))
    itemid = Column(String(20))
    con_date = Column(DateTime)
    modification = Column(Integer)
    version = Column(Integer)

    def __init__(self, id, name=None, mac=None, ip=None, note=None, idnum=None,
                 plcnum=0, tenid=None, itemid=None, con_date=None, modification=0, version=0):
        self.id = id
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
        self.modification = check_int(modification)
        self.version = version

    def __repr__(self):
        return '<Station : %r >' % self.name


class YjPLCInfo(Base):
    __tablename__ = 'yjplcinfo'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(30))
    note = Column(String(200))
    ip = Column(String(30))
    mpi = Column(Integer)
    type = Column(Integer)
    plctype = Column(String(20))
    tenid = Column(String(255), nullable=False)
    itemid = Column(String(20))

    #station_id = Column(Integer)
    station_id = Column("station_id", Integer, ForeignKey("yjstationinfo.id"))
    station = relationship("YjStationInfo", foreign_keys="YjPLCInfo.station_id",
                           backref=backref("plcs", cascade="all, delete-orphan"),
                            primaryjoin="YjStationInfo.id==YjPLCInfo.station_id")
    #station_id = Column(Integer, ForeignKey('yjstationinfo.id'))
    #station = relationship('YjStationInfo', back_populates='plcs')

    def __init__(self, id, name=None, station_id=None, note=None, ip=None,
                 mpi=None, type=None, plctype=None,
                 tenid=0, itemid=None):
        self.id = id
        self.name = name
        self.station_id = station_id
        self.note = note
        self.ip = ip
        self.mpi = check_int(mpi)
        self.type = check_int(type)
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


class YjGroupInfo(Base):
    __tablename__ = 'yjgroupinfo'
    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    groupname = Column(String(20))
    note = Column(String(100))
    uploadcycle = Column(Integer)
    tenid = Column(String(255), nullable=False)
    itemid = Column(String(20))

    plc_id = Column("plc_id", Integer, ForeignKey("yjplcinfo.id"))
    plc = relationship("YjPLCInfo", foreign_keys="YjGroupInfo.plc_id", backref=backref("groups", cascade="all, delete-orphan"),
                           primaryjoin="YjPLCInfo.id==YjGroupInfo.plc_id")
    #plc_id = Column(Integer)
    #plc_id = Column(Integer, ForeignKey('yjplcinfo.id'))
    #plc = relationship('YjPLCInfo', back_populates='groups')

    def __init__(self, id, groupname=None, plc_id=None, note=None,
                 uploadcycle=None, tenid=None, itemid=None):
        self.id = id
        self.groupname = groupname
        self.plc_id = check_int(plc_id)
        self.note = note
        self.uploadcycle = check_int(uploadcycle)
        self.tenid = tenid
        self.itemid = itemid

    def __repr__(self):
        return '<Group : %r >' % self.groupname


class YjVariableInfo(Base):
    __tablename__ = 'yjvariableinfo'
    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    tagname = Column(String(20), unique=True)
    address = Column(String(20))
    datatype = Column(String(10))
    rwtype = Column(Integer)
    upload = Column(Integer)
    acquisitioncycle = Column(Integer)
    serverrecordcycle = Column(Integer)
    writevalue = Column(String(20))
    note = Column(String(50))
    tenid = Column(String(200), nullable=False)
    itemid = Column(String(20))


    plc_id = Column("plc_id", Integer, ForeignKey("yjplcinfo.id"))
    plc = relationship("YjPLCInfo", foreign_keys="YjVariableInfo.plc_id", backref=backref("variables", cascade="all, delete-orphan"),
                           primaryjoin="YjPLCInfo.id==YjVariableInfo.plc_id")

    group_id = Column("group_id", Integer, ForeignKey("yjgroupinfo.id"))
    group = relationship("YjGroupInfo", foreign_keys="YjVariableInfo.group_id", backref=backref("variables", cascade="all, delete-orphan"),
                           primaryjoin="YjGroupInfo.id==YjVariableInfo.group_id")
    #plc_id = Column(Integer)
    #plc_id = Column(Integer, ForeignKey('yjplcinfo.id'))
    #plc = relationship('YjPLCInfo', back_populates='variables')
    #group_id = Column(Integer)
    #group_id = Column(Integer, ForeignKey('yjgroupinfo.id'))
    #group = relationship('YjGroupInfo', back_populates='variables')


    def __init__(self, id, tagname=None, plc_id=None, group_id=None, address=None,
                 datatype=None, rwtype=None, upload=None,
                 acquisitioncycle=None, serverrecordcycle=None,
                 writevalue=None, note=None, tenid=None, itemid=None):
        self.id = id
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


class Value(Base):
    __tablename__ = 'values'
    id = Column(Integer, primary_key=True, autoincrement=True)
    value = Column(String(128))
    date = Column(DateTime)
    variable_name = Column(String(20))
    #variable_name = Column("variable_name", String(20), ForeignKey("yjvariableinfo.tagname"))
    #variable = relationship("YjVariableInfo", foreign_keys="Value.variable_name", backref=backref("values"),
    #                        primaryjoin="YjVariableInfo.id==Value.variable_name")
    #variable_id = Column(Integer)
    #variable_id = Column(Integer, ForeignKey('yjvariableinfo.id'))
    #variable = relationship('YjVariableInfo', back_populates='values')

    def __init__(self, variable_name, value, date=None):
        #self.variable_id = check_int(variable_id)
        self.variable_name = variable_name
        self.value = value
        self.get_time = get_time


class TransferLog(Base):
    __tablename__ = 'transferlogs'
    id = Column(Integer, primary_key=True, autoincrement=True)
    type = Column(String(20))
    date = Column(DateTime)
    status = Column(String(20))

    def __init__(self, type, date, status):
        self.type = type
        self.date = date
        self.status = status


Session = sessionmaker(bind=eng)
