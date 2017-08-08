# coding=utf-8
import os, datetime
try:
    import configparser as ConfigParser
except:
    import ConfigParser

from sqlalchemy import Column, String, Integer, Boolean, ForeignKey, create_engine, MetaData
from sqlalchemy.orm import sessionmaker, relationship, backref, class_mapper
from sqlalchemy.ext.declarative import declarative_base

here = os.path.abspath(os.path.dirname(__name__))
cf = ConfigParser.ConfigParser()
cf.read_file(open(os.path.join(here, 'config.ini')))

db_uri = cf.get(os.environ.get('env'), 'db_uri')

# 创建连接
eng = create_engine(db_uri + '?charset=utf8')
# 创建基类
Base = declarative_base()

Session = sessionmaker(bind=eng)
session = Session()


def serialize(model):
    """Transforms a model into a dictionary which can be dumped to JSON."""
    # first we get the names of all the columns on your model
    columns = [c.key for c in class_mapper(model.__class__).columns]
    # then we return their values in a dict
    return dict((c, getattr(model, c)) for c in columns)


class YjStationInfo(Base):
    __tablename__ = 'yjstationinfo'
    id = Column(Integer, primary_key=True, nullable=False)
    station_name = Column(String(30))
    mac = Column(String(20))
    ip = Column(String(20))
    note = Column(String(200))
    id_num = Column(String(200))
    plc_count = Column(Integer)
    ten_id = Column(String(255))
    item_id = Column(String(20))
    con_date = Column(Integer)
    version = Column(Integer)

    def __init__(self, model_id, station_name=None, mac=None, ip=None, note=None, id_num=None,
                 plc_count=0, ten_id=None, item_id=None, con_date=None, version=0):
        self.id = model_id
        self.station_name = station_name
        self.mac = mac
        self.ip = ip
        self.note = note
        self.id_num = id_num
        self.plc_count = plc_count
        self.ten_id = ten_id
        self.item_id = item_id
        self.con_date = con_date
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
    ten_id = Column(String(255))
    item_id = Column(String(20))
    rack = Column(Integer)
    slot = Column(Integer)
    tcp_port = Column(Integer)

    station_id = Column("station_id", Integer, ForeignKey("yjstationinfo.id"))
    station = relationship("YjStationInfo", foreign_keys="YjPLCInfo.station_id",
                           backref=backref("plcs", cascade="all, delete-orphan"),
                           primaryjoin="YjStationInfo.id==YjPLCInfo.station_id")

    def __init__(self, model_id, plc_name=None, station_id=None, note=None, ip=None,
                 mpi=None, type=None, plc_type=None,
                 ten_id=0, item_id=None, rack=0, slot=0, tcp_port=102):
        self.id = model_id
        self.plc_name = plc_name
        self.station_id = station_id
        self.note = note
        self.ip = ip
        self.mpi = mpi
        self.type = type
        self.plc_type = plc_type
        self.ten_id = ten_id
        self.item_id = item_id
        self.rack = rack
        self.slot = slot
        self.tcp_port = tcp_port

    def __repr__(self):
        return '<PLC : %r >' % self.plc_name


class YjGroupInfo(Base):
    __tablename__ = 'yjgroupinfo'
    id = Column(Integer, primary_key=True, nullable=False)
    group_name = Column(String(20))
    note = Column(String(100))
    upload_cycle = Column(Integer)
    ten_id = Column(String(255))
    item_id = Column(String(20))

    upload = Column(Boolean)
    upload_time = Column(Integer)
    uploading = Column(Boolean)

    plc_id = Column("plc_id", Integer, ForeignKey("yjplcinfo.id"))
    plc = relationship("YjPLCInfo", foreign_keys="YjGroupInfo.plc_id",
                       backref=backref("groups", cascade="all, delete-orphan"),
                       primaryjoin="YjPLCInfo.id==YjGroupInfo.plc_id")

    def __init__(self, model_id, group_name=None, plc_id=None, note=None,
                 upload_cycle=None, ten_id=None, item_id=None, upload=True):
        self.id = model_id
        self.group_name = group_name
        self.plc_id = plc_id
        self.note = note
        self.upload_cycle = upload_cycle
        self.ten_id = ten_id
        self.item_id = item_id
        self.upload = upload

    def __repr__(self):
        return '<Group : %r >' % self.group_name


class YjVariableInfo(Base):
    __tablename__ = 'yjvariableinfo'
    id = Column(Integer, primary_key=True, nullable=False)
    variable_name = Column(String(20))
    db_num = Column(Integer)
    address = Column(Integer)
    data_type = Column(String(10))
    rw_type = Column(Integer)
    upload = Column(Integer)
    acquisition_cycle = Column(Integer)
    server_record_cycle = Column(Integer)
    note = Column(String(50))
    ten_id = Column(String(200))
    item_id = Column(String(20))
    write_value = Column(Integer)
    area = Column(Integer)

    acquisition_time = Column(Integer)

    group_id = Column("group_id", Integer, ForeignKey("yjgroupinfo.id"))
    group = relationship("YjGroupInfo", foreign_keys="YjVariableInfo.group_id",
                         backref=backref("variables", cascade="all, delete-orphan"),
                         primaryjoin="YjGroupInfo.id==YjVariableInfo.group_id")

    def __init__(self, model_id, variable_name=None, group_id=None, db_num=None, address=None,
                 data_type=None, rw_type=None, upload=None,
                 acquisition_cycle=None, server_record_cycle=None,
                 note=None, ten_id=None, item_id=None, write_value=None, area=None):
        self.id = model_id
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

    def __init__(self, variable_id, value, time):
        self.variable_id = variable_id
        self.value = value
        self.time = time


class TransferLog(Base):
    __tablename__ = 'transfer_logs'
    id = Column(Integer, primary_key=True, autoincrement=True)
    trans_type = Column(String(20))
    time = Column(Integer)
    status = Column(String(20))
    note = Column(String(200))
    status_code = Column(Integer)

    def __init__(self, trans_type, time, status, note):
        self.trans_type = trans_type
        self.time = time
        self.status = status
        self.note = note


# class ConfigUpdateLog(Base):
#     __tablename__ = 'config_update_log'
#     id = Column(Integer, primary_key=True, autoincrement=True)
#     time = Column(Integer)
#     version = Column(Integer)


class VarAlarmLog(Base):
    __tablename__ = 'var_alarm_log'
    id = Column(Integer, primary_key=True, autoincrement=True)
    alarm_id = Column(Integer, ForeignKey('var_alarm_info.id'))
    time = Column(Integer)
    confirm = Column(Boolean)


class VarAlarmInfo(Base):
    __tablename__ = 'var_alarm_info'
    id = Column(Integer, primary_key=True, autoincrement=True)
    variable_id = Column(Integer, ForeignKey('yjvariableinfo.id'))
    alarm_type = Column(Integer)
    note = Column(String(128))

    logs = relationship('VarAlarmLog', backref='var_alarm_info', lazy='dynamic', cascade='all')
