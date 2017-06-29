# coding=utf-8
import os, datetime
from sqlalchemy import Column, String, Integer, DateTime, Boolean, ForeignKey, create_engine
from sqlalchemy.orm import sessionmaker, relationship, backref
from sqlalchemy.ext.declarative import declarative_base

from consts import DB_URI

# 创建连接
eng = create_engine(DB_URI)
# 创建基类
Base = declarative_base()

Session = sessionmaker(bind=eng)
session = Session()


def check_int(column):
    if column is not unicode("None"):
        return int(column)
    else:
        return column


class YjStationInfo(Base):
    __tablename__ = 'yjstationinfo'
    id = Column(Integer, primary_key=True, nullable=False)
    station_name = Column(String(30))
    mac = Column(String(20))
    ip = Column(String(20))
    note = Column(String(200))
    id_num = Column(String(200))
    plc_num = Column(Integer)
    ten_id = Column(String(255))
    item_id = Column(String(20))
    con_date = Column(Integer)
    modification = Column(Integer)
    version = Column(Integer)

    def __init__(self, id, name=None, mac=None, ip=None, note=None, id_num=None,
                 plc_num=0, ten_id=None, item_id=None, con_date=None, modification=0, version=0):
        self.id = id
        self.name = name
        self.mac = mac
        self.ip = ip
        self.note = note
        self.id_num = id_num
        self.plc_num = check_int(plc_num)
        self.ten_id = ten_id
        self.item_id = item_id
        if con_date is None:
            con_date = datetime.datetime.utcnow()
        self.con_date = con_date
        self.modification = check_int(modification)
        self.version = version

    def __repr__(self):
        return '<Station : %r >' % self.station_name


class YjPLCInfo(Base):
    __tablename__ = 'yjplcinfo'
    id = Column(Integer, primary_key=True, nullable=False)
    plc_name = Column(String(30))
    note = Column(String(200))
    ip = Column(String(30))
    mpi = Column(Integer)
    type = Column(Integer)
    plc_type = Column(String(20))
    ten_id = Column(String(255), nullable=False)
    item_id = Column(String(20))

    station_id = Column("station_id", Integer, ForeignKey("yjstationinfo.id"))
    station = relationship("YjStationInfo", foreign_keys="YjPLCInfo.station_id",
                           backref=backref("plcs", cascade="all, delete-orphan"),
                           primaryjoin="YjStationInfo.id==YjPLCInfo.station_id")

    # station_id = Column(Integer, ForeignKey('yjstationinfo.id'))
    # station = relationship('YjStationInfo', back_populates='plcs')

    def __init__(self, id, name=None, station_id=None, note=None, ip=None,
                 mpi=None, type=None, plc_type=None,
                 ten_id=0, item_id=None):
        self.id = id
        self.name = name
        self.station_id = station_id
        self.note = note
        self.ip = ip
        self.mpi = check_int(mpi)
        self.type = check_int(type)
        self.plc_type = plc_type
        self.ten_id = ten_id
        self.item_id = item_id

    def __repr__(self):
        return '<PLC : %r >' % self.plc_name


class YjGroupInfo(Base):
    __tablename__ = 'yjgroupinfo'
    id = Column(Integer, primary_key=True, nullable=False)
    group_name = Column(String(20))
    note = Column(String(100))
    upload_cycle = Column(Integer)
    ten_id = Column(String(255), nullable=False)
    item_id = Column(String(20))

    plc_id = Column("plc_id", Integer, ForeignKey("yjplcinfo.id"))
    plc = relationship("YjPLCInfo", foreign_keys="YjGroupInfo.plc_id",
                       backref=backref("groups", cascade="all, delete-orphan"),
                       primaryjoin="YjPLCInfo.id==YjGroupInfo.plc_id")

    # plc_id = Column(Integer, ForeignKey('yjplcinfo.id'))
    # plc = relationship('YjPLCInfo', back_populates='groups')

    def __init__(self, id, group_name=None, plc_id=None, note=None,
                 upload_cycle=None, ten_id=None, item_id=None):
        self.id = id
        self.group_name = group_name
        self.plc_id = check_int(plc_id)
        self.note = note
        self.upload_cycle = check_int(upload_cycle)
        self.ten_id = ten_id
        self.item_id = item_id

    def __repr__(self):
        return '<Group : %r >' % self.group_name


class YjVariableInfo(Base):
    __tablename__ = 'yjvariableinfo'
    id = Column(Integer, primary_key=True, nullable=False)
    variable_name = Column(String(20))
    db_num = Column(Integer)
    address = Column(String(20))
    data_type = Column(String(10))
    rw_type = Column(Integer)
    upload = Column(Integer)
    acquisition_cycle = Column(Integer)
    server_record_cycle = Column(Integer)
    note = Column(String(50))
    ten_id = Column(String(200), nullable=False)
    item_id = Column(String(20))

    plc_id = Column("plc_id", Integer, ForeignKey("yjplcinfo.id"))
    plc = relationship("YjPLCInfo", foreign_keys="YjVariableInfo.plc_id",
                       backref=backref("variables", cascade="all, delete-orphan"),
                       primaryjoin="YjPLCInfo.id==YjVariableInfo.plc_id")

    group_id = Column("group_id", Integer, ForeignKey("yjgroupinfo.id"))
    group = relationship("YjGroupInfo", foreign_keys="YjVariableInfo.group_id",
                         backref=backref("variables", cascade="all, delete-orphan"),
                         primaryjoin="YjGroupInfo.id==YjVariableInfo.group_id")

    # plc_id = Column(Integer)
    # plc_id = Column(Integer, ForeignKey('yjplcinfo.id'))
    # plc = relationship('YjPLCInfo', back_populates='variables')
    # group_id = Column(Integer)
    # group_id = Column(Integer, ForeignKey('yjgroupinfo.id'))
    # group = relationship('YjGroupInfo', back_populates='variables')

    def __init__(self, id, variable_name=None, plc_id=None, group_id=None, db_num=None, address=None,
                 data_type=None, rw_type=None, upload=None,
                 acquisition_cycle=None, server_record_cycle=None,
                 note=None, ten_id=None, item_id=None):
        self.id = id
        self.variable_name = variable_name
        self.plc_id = plc_id
        self.group_id = group_id
        self.db_num = db_num
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
        return '<Variable : %r >' % self.variable_name


class Value(Base):
    __tablename__ = 'values'
    id = Column(Integer, primary_key=True, autoincrement=True)
    value = Column(String(128))
    time = Column(Integer)

    variable_id = Column("variable_id", Integer, ForeignKey("yjvariableinfo.id"))
    variable = relationship("YjVariableInfo", foreign_keys="Value.variable_id",
                            backref=backref("values", cascade="all, delete-orphan"),
                            primaryjoin="YjVariableInfo.id==Value.variable_id")

    # variable_name = Column("variable_name", String(20), ForeignKey("yjvariableinfo.tagname"))
    # variable = relationship("YjVariableInfo", foreign_keys="Value.variable_name", backref=backref("values"),
    #                        primaryjoin="YjVariableInfo.id==Value.variable_name")
    # variable_id = Column(Integer)
    # variable_id = Column(Integer, ForeignKey('yjvariableinfo.id'))
    # variable = relationship('YjVariableInfo', back_populates='values')

    def __init__(self, variable_id, value, get_time):
        self.variable_id = variable_id
        self.value = value
        self.get_time = get_time


class TransferLog(Base):
    __tablename__ = 'transfer_logs'
    id = Column(Integer, primary_key=True, autoincrement=True)
    type = Column(String(20))
    time = Column(Integer)
    status = Column(String(20))
    note = Column(String(200))

    def __init__(self, type, time, status=None, note=None):
        self.type = type
        self.time = time
        self.status = status
        self.note = note


class ConfigUpdateLog(Base):
    __tablename__ = 'config_update_log'
    id = Column(Integer, primary_key=True, autoincrement=True)
    time = Column(Integer)
    version = Column(Integer)


class GroupUploadTime(Base):
    __tablename__ = 'group_upload_times'
    id = Column(Integer, primary_key=True, autoincrement=True)
    time = Column(Integer)

    group_id = Column("group_id", Integer, ForeignKey("yjgroupinfo.id"))
    group = relationship("YjGroupInfo", foreign_keys="GroupUploadTime.group_id",
                         backref=backref("upload_times", cascade="all, delete-orphan"),
                         primaryjoin="YjGroupInfo.id==GroupUploadTime.group_id")

    def __init__(self, group_id, next_time):
        self.group_id = group_id
        self.next_time = next_time


class VariableGetTime(Base):
    __tablename__ = 'value_get_times'
    id = Column(Integer, primary_key=True, autoincrement=True)
    time = Column(Integer)

    variable_id = Column("variable_id", Integer, ForeignKey("yjvariableinfo.id"))
    variable = relationship("YjVariableInfo", foreign_keys="VariableGetTime.variable_id",
                            backref=backref("get_times", cascade="all, delete-orphan"),
                            primaryjoin="YjVariableInfo.id==VariableGetTime.variable_id")

    def __init__(self, variable_id, time):
        self.variable_id = variable_id
        self.time = time
