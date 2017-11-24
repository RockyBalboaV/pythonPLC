# coding=utf-8
import os

from sqlalchemy import Column, String, Integer, Float, Boolean, ForeignKey, create_engine, MetaData, Table, JSON, \
    BigInteger
from sqlalchemy.orm import sessionmaker, relationship, backref, class_mapper
from sqlalchemy.ext.declarative import declarative_base

from param import DB_URI

# 创建连接
eng = create_engine(DB_URI + '?charset=utf8', pool_recycle=1, pool_size=20, max_overflow=0)
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


class VarGroups(Base):
    __tablename__ = 'variables_groups'
    id = Column(Integer, primary_key=True, autoincrement=True)
    variable_id = Column(Integer, ForeignKey('yjvariableinfo.id'), primary_key=True)
    group_id = Column(Integer, ForeignKey('yjgroupinfo.id'), primary_key=True)
    variable = relationship('YjVariableInfo', back_populates='groups')
    group = relationship('YjGroupInfo', back_populates='variables')


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
    uptime = Column(Integer)
    off_time = Column(Integer)
    check_time = Column(Integer)
    power_err = Column(Boolean)

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
    con_time = Column(Integer)

    station_id = Column("station_id", Integer, ForeignKey("yjstationinfo.id", ondelete='CASCADE', onupdate='CASCADE'))
    station = relationship(
        "YjStationInfo",
        foreign_keys="YjPLCInfo.station_id",
        backref=backref("plcs", cascade="all, delete-orphan"),
        primaryjoin="YjStationInfo.id==YjPLCInfo.station_id"
    )

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
    acquisition_cycle = Column(Integer)
    server_record_cycle = Column(Integer)
    acquisition_time = Column(Integer)

    is_upload = Column(Boolean)
    upload_time = Column(Integer)
    uploading = Column(Boolean)

    plc_id = Column("plc_id", Integer, ForeignKey("yjplcinfo.id", ondelete='CASCADE', onupdate='CASCADE'))
    plc = relationship(
        "YjPLCInfo",
        foreign_keys="YjGroupInfo.plc_id",
        backref=backref("groups", cascade="all, delete-orphan"),
        primaryjoin="YjPLCInfo.id==YjGroupInfo.plc_id"
    )

    # variables = relationship('YjVariableInfo', secondary=var_groups)
    variables = relationship('VarGroups', back_populates='group')

    def __repr__(self):
        return '<Group : %r >' % self.group_name


class YjVariableInfo(Base):
    __tablename__ = 'yjvariableinfo'
    id = Column(Integer, primary_key=True, nullable=False)
    variable_name = Column(String(20))
    db_num = Column(Integer)
    address = Column(Float)
    data_type = Column(Integer)
    rw_type = Column(Integer)
    is_upload = Column(Boolean)
    note = Column(String(50))
    ten_id = Column(String(200))
    item_id = Column(String(20))
    write_value = Column(Integer)
    area = Column(Integer)
    is_analog = Column(Boolean)
    analog_low_range = Column(Float)
    analog_high_range = Column(Float)
    digital_low_range = Column(Float)
    digital_high_range = Column(Float)
    offset = Column(Float)

    # groups = relationship('YjGroupInfo', secondary=var_groups)
    groups = relationship('VarGroups', back_populates='variable')

    def __repr__(self):
        return '<Variable : %r >' % self.variable_name


class Value(Base):
    __tablename__ = 'values'
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    value = Column(Float)
    time = Column(Integer)

    variable_id = Column("variable_id", Integer,
                         ForeignKey("yjvariableinfo.id", ondelete='SET NULL', onupdate='CASCADE'))
    variable = relationship(
        "YjVariableInfo",
        foreign_keys="Value.variable_id",
        backref=backref("values", cascade="all, delete-orphan"),
        primaryjoin="YjVariableInfo.id==Value.variable_id"
    )


class TransferLog(Base):
    __tablename__ = 'transfer_logs'
    id = Column(Integer, primary_key=True, autoincrement=True)
    trans_type = Column(String(20))
    time = Column(Integer)
    status = Column(String(20))
    note = Column(String(200))
    status_code = Column(Integer)


class StationAlarm(Base):
    __tablename__ = 'station_alarm'

    id = Column(Integer, primary_key=True, autoincrement=True)
    id_num = Column(String(200))
    code = Column(Integer)
    note = Column(String(200))
    time = Column(Integer)


class PLCAlarm(Base):
    __tablename__ = 'plc_alarm'

    id = Column(Integer, primary_key=True, autoincrement=True)
    id_num = Column(String(200))
    plc_id = Column(Integer)
    level = Column(Integer)
    note = Column(String(200))
    time = Column(Integer)
