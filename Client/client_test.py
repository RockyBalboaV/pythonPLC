# coding=utf-8
import unittest
import mock
import time

from subprocess import Popen
from os import path, kill
import snap7

import app
from models import *

ip = '192.168.18.17'
tcpport = 102
db_number = 10
rack = 0
slot = 2


class TestClient(unittest.TestCase):

    def setUp(self):
        eng = create_engine(DB_URI)
        Session = sessionmaker(bind=eng)
        self.session = Session()


        print 'setUp starting...'

    def tearDown(self):

        self.session.close()
        print 'tearDowning starting...'

    def test_encryption_decryption(self):
        # 加密解密的数据中包括引号会报错
        raw_data = {"description": "Its test"}
        data = app.decryption(app.encryption(raw_data))
        self.assertEqual(raw_data, data)

    def test_get_station_info(self):
        station = YjStationInfo(id=999, name='test', mac='test', ip='test', note='test', idnum='1', plcnum=1, tenid=0,
                                itemid=0, version=1)
        self.session.add(station)
        self.session.commit()

        station_info = {"idnum": "1", "version": 1}
        self.assertEqual(station_info, app.get_station_info(name='test'))

        self.session.delete(self.session.query(YjStationInfo).filter(YjStationInfo.name == 'test').first())
        self.session.commit()

    def test_get_data_from_query(self):

        station = YjStationInfo(id=999, name='test', mac='test', ip='test', note='test', idnum='1', plcnum=1, tenid=0,
                                itemid=0, version=1)
        self.session.add(station)
        self.session.commit()

        station = self.session.query(YjStationInfo).filter(YjStationInfo.name == 'test').all()
        obj = app.get_data_from_query(station)
        self.assertIs(type(obj), type(list()))
        self.assertEqual(obj[0]["name"], "test")

        self.session.delete(self.session.query(YjStationInfo).filter(YjStationInfo.name == 'test').first())
        self.session.commit()

    def test_get_data_from_model(self):
        station = YjStationInfo(id=999, name='test', mac='test', ip='test', note='test', idnum='1', plcnum=1, tenid=0,
                                itemid=0, version=1)
        self.session.add(station)
        self.session.commit()

        station = self.session.query(YjStationInfo).filter(YjStationInfo.name == 'test').first()
        obj = app.get_data_from_model(station)
        self.assertIs(type(obj), type(dict()))
        self.assertEqual(obj["name"], "test")

        self.session.delete(self.session.query(YjStationInfo).filter(YjStationInfo.name == 'test').first())
        self.session.commit()

    def test_variable_size(self):
        variable = YjVariableInfo(id=9999, tagname='test', address='0', rwtype=1, upload=1, acquisitioncycle=1, serverrecordcycle=5, datatype='FLOAT', tenid=0)
        self.session.add(variable)
        self.session.commit()

        variable = self.session.query(YjVariableInfo).filter(YjVariableInfo.tagname == 'test').first()
        self.assertEqual(app.variable_size(variable), ('f', 4))
        variable.datatype = 'INT'
        self.assertEqual(app.variable_size(variable), ('i', 4))
        variable.datatype = 'DINT'
        self.assertEqual(app.variable_size(variable), ('i', 4))
        variable.datatype = 'WORD'
        self.assertEqual(app.variable_size(variable), ('h', 2))
        variable.datatype = 'BYTE'
        self.assertEqual(app.variable_size(variable), ('s', 1))
        variable.datatype = 'BOOL'
        self.assertEqual(app.variable_size(variable), ('?', 1))

        self.session.delete(variable)
        self.session.commit()


@unittest.skip("its uncomplete")
class TestPLC(unittest.TestCase):

    def setUp(self):
        self.client = snap7.client.Client()
        self.client.connect(ip, rack, slot, tcpport)
        print 'setUp starting...'

    def tearDown(self):
        self.client.disconnect()
        self.client.destroy()
        print 'tearDowning starting...'

    def test_db_read(self):
        size = 10
        start = 0
        db = 10
        data = bytearray(10)
        self.client.db_write(db_number=db, start=start, data=data)
        result = self.client.db_read(db_number=db, start=start, size=size)
        self.assertEqual(data, result)

if __name__ == '__main__':
    unittest.main()
