import struct
import string
import snap7
from snap7 import util
client=snap7.client.Client()
client.connect("192.168.18.17",0,2)
print"ok"
####### write ########
data=(100,)
a=struct.pack('>b',data[0])
data=bytearray(a)
client.db_write(1,0,data)

data=(100.1,)
a=struct.pack('>f',data[0])
data=bytearray(a)
client.db_write(1,2,data)

data=(200,)
a=struct.pack('>h',data[0])
data=bytearray(a)
client.db_write(1,6,data)

data=(3000,)
a=struct.pack('>l',data[0])
data=bytearray(a)
client.db_write(1,8,data)

data=(8,)
a=struct.pack('>b',data[0])
data=bytearray(a)
client.db_write(1,12,data)

data=(100,)
a=struct.pack('>h',data[0])
data=bytearray(a)
client.db_write(1,14,data)
####### write ########
data=(10.1,)
a=struct.pack('>f',data[0])
data=bytearray(a)
client.db_write(1,2,data)


print"->122(1)"
date=client.db_read(1,0,1)
b=''.join(chr(i)for i in date)
print struct.unpack('>b',b)

print"->9392.13(4)"
date=client.db_read(1,2,4)
b=''.join(chr(i)for i in date)
print struct.unpack('>f',b)

print"->996(2)"
date=client.db_read(1,6,2)
b=''.join(chr(i)for i in date)
print struct.unpack('>h',b)

print"->1234567(4)"
date=client.db_read(1,8,4)
b=''.join(chr(i)for i in date)
print struct.unpack('>l',b)

date=client.db_read(1,12,1)
b=''.join(chr(i)for i in date)
print struct.unpack('>b',b)

date=client.db_read(1,14,2)
b=''.join(chr(i)for i in date)
print struct.unpack('>h',b)
