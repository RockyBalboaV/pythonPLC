import snap7
import snap7.snap7types as ID
import struct

I = 1
Q = 2
M = 3
DB = 4

Real = 'f'
Int = 'h'
Bool = 'h'
Word = 'H'
Dword = 'L'


def write(IP, area, start, Bytes, Types, data, dbnumber):
    if area == 1:
        writeI(IP, start, Bytes)
    if area == 2:
        writeQ(IP, start, Bytes)
    if area == 3:
        writeM(IP, start, Bytes, Types, data)
    if area == 4:
        writeDB(IP, start, data, dbnumber)


def read(IP, area, start, Bytes, dbnumber):
    if area == 1:
        return readI(IP, area, start, Bytes)
    if area == 2:
        return readQ(IP, area, start, Bytes)
    if area == 3:
        return readM(IP, area, start, Bytes)
    if area == 4:
        return readDB(IP, area, start, Bytes, dbnumber)


def writeI(IP, start, data):
    client = snap7.client.Client()
    client.create()
    client.connect(address=IP, rack=0, slot=2, tcpport=102)
    return client.write_area(area=ID.S7AreaPE, dbnumber=0, start=start, data=data)
    client.disconnect()
    client.destroy()


def writeQ(IP, start, data):
    client = snap7.client.Client()
    client.create()
    client.connect(address='192.168.18.17', rack=0, slot=2, tcpport=102)
    if len(data) > 210:
        return client.write_area(area=ID.S7AreaPA, dbnumber=0, start=start, data=data)
    else:
        return client.as_ab_write(start=start, data=data)
    client.disconnect()
    client.destroy()


def writeM(IP, start, data):
    client = snap7.client.Client()
    client.create()
    client.connect(address=IP, rack=0, slot=2, tcpport=102)
    return client.write_area(area=ID.S7AreaMK, dbnumber=0, start=start, data=data)
    client.disconnect()
    client.destroy()


def writeDB(IP, start, data, dbnumber):
    client = snap7.client.Client()
    client.create()
    client.connect(address=IP, rack=0, slot=2, tcpport=102)
    if len(data) < 200:
        return client.as_db_write(db_number=dbnumber, start=start, data=data)
    else:
        return client.write_area(area=ID.S7AreaDB, dbnumber=dbnumber, start=start, data=data)
    client.disconnect()
    client.destroy()


def readI(IP, area, start, Bytes):
    client = snap7.client.Client()
    client.create()
    client.connect(address=IP, rack=0, slot=2, tcpport=102)
    return client.read_area(area=area, dbnumber=0, start=start, size=Bytes)
    client.disconnect()
    client.destroy()


def readQ(IP, area, start, Bytes):
    client = snap7.client.Client()
    client.create()
    client.connect(address=IP, rack=0, slot=2, tcpport=102)
    return client.read_area(area=area, dbnumber=0, start=start, size=Bytes)
    client.disconnect()
    client.destroy()


def readM(IP, area, start, Bytes):
    client = snap7.client.Client()
    client.create()
    client.connect(address=IP, rack=0, slot=2, tcpport=102)
    return client.read_area(area=area, dbnumber=0, start=start, size=Bytes)
    client.disconnect()
    client.destroy()


def readDB(IP, area, start, Bytes, dbnumber):
    client = snap7.client.Client()
    client.create()
    client.connect(address=IP, rack=0, slot=2, tcpport=102)
    if Bytes > 1000:
        return client.db_get(db_number=dbnumber)
    else:
        return client.db_read(db_number=dbnumber, start=start, size=Bytes)
    client.disconnect()
    client.destroy()


def creatarray(sum, formate, size):
    array = '!'
    while sum >= 0:
        sum = sum - size
        array = array + formate
    return array


def packarray(sum, formate, value):
    size = 0
    array = ''
    if formate == Real:
        size = 4
    if formate == Int:
        size = 2
    if formate == Bool:
        size = 1
    if formate == Word:
        size = 2
    if formate == Dword:
        size = 4
    while sum >= 0 and formate != Bool:
        sum = sum - size
        array = array + struct.pack('!f', value)
    while sum >= 0 and formate == Bool:
        sum = sum - size
        array = array + chr(int('11111111', 2))
    return array


def unpackarray(array, type, bite):
    if type == Real:
        arraylist = []
        sum = 0
        while sum < len(array):
            arraylist.append(struct.unpack_from('!f', array, sum))
            sum = sum + 4
        return arraylist
    if type == Int:
        arraylist = []
        sum = 0
        while sum < len(array):
            arraylist.append(struct.unpack_from('!h', array, sum))
            sum = sum + 2
        return arraylist
    if type == Bool:
        buffer = []
        for x in array:
            buffer.extend(bin(x).replace('0b', '').rjust(8, '0'))
        return buffer[len(array) * 8 - 1 - bite]
    if type == Word:
        arraylist = []
        sum = 0
        while sum < len(array):
            arraylist.append(struct.unpack_from('!H', array, sum))
            sum = sum + 2
        return arraylist
    if type == Dword:
        arraylist = []
        sum = 0
        while sum < len(array):
            arraylist.append(struct.unpack_from('!I', array, sum))
            sum = sum + 4
        return arraylist


def structarray(number, data, bytes):
    array = ''
    while number >= 0:
        array = array + struct.pack('!' + bytes, data)
        number = number - bytes
    return array


client = snap7.client.Client()
client.create()
client.connect(address='192.168.18.17', rack=0, slot=2, tcpport=102)
# client.write_area(area = ID.S7AreaDB,dbnumber=6,start =0,data =structarray(6552,9.9,4))
write(IP='192.168.18.17', area=DB, start=0, Bytes=4, Types=Real, data=packarray(6548, Real, 8.9), dbnumber=6)
read(IP='192.168.18.17', area=DB, start=0, Bytes=6552, dbnumber=6)
print(unpackarray(readDB('192.168.18.17', DB, 0, 6552, 6), 'f', bite=0))
