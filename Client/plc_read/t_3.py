# /*/ coding: utf-8/*/
import struct
import snap7
import snap7.snap7types as ID

client = snap7.client.Client()

# 建立连接
client.create()

# cpu连接 ip，机架，槽
client.connect(address='192.168.18.17', rack=0, slot=2, tcpport=102)
#检测是否连接成功（True/False）
print client.get_connected()

#写M位地址,例如M6.7为1
client.write_area(area = ID.S7AreaMK , dbnumber = 0 , start = 6 , data = chr(8))
#读M位地址,例如M6.7为1: B:7,W:15,D:31
buffer = client.read_area(area = ID.S7AreaMK , dbnumber = 0 , start = 6 , size = 1)
temp = 7
buffer1 = []
for x in buffer:
    buffer1.extend(bin(x).replace('0b','').rjust(8 , '0'))
print buffer1[abs(temp - 6)]
#print buffer1


#写M字地址,例如M8为1,H无符号，h有符号
client.write_area(area = ID.S7AreaMK , dbnumber = 0 , start = 8 , data = struct.pack('!h',-12))
client.write_area(area = ID.S7AreaMK , dbnumber = 0 , start = 8 , data = struct.pack('!H',12))
#读M字地址,
MW0 = client.read_area(area = ID.S7AreaMK , dbnumber = 0 , start = 8 , size = 2)
MW1 = client.read_area(area = ID.S7AreaMK , dbnumber = 0 , start = 8 , size = 2)
print struct.unpack('!h' , MW0)
print struct.unpack('!H' , MW1)



#写M双字地址,例如M10,i:int，L:unsigned int,f:real
client.write_area(area = ID.S7AreaMK , dbnumber = 0 , start = 10 , data = struct.pack('!i',-12))
client.write_area(area = ID.S7AreaMK , dbnumber = 0 , start = 10 , data = struct.pack('!L',12))
client.write_area(area = ID.S7AreaMK , dbnumber = 0 , start = 10 , data = struct.pack('!f',12.9))
#读M双字地址,
MD0 = client.read_area(area = ID.S7AreaMK , dbnumber = 0 , start = 10 , size = 4)
MD1 = client.read_area(area = ID.S7AreaMK , dbnumber = 0 , start = 10 , size = 4)
MD2 = client.read_area(area = ID.S7AreaMK , dbnumber = 0 , start = 10 , size = 4)
print struct.unpack('!i' , MD0)
print struct.unpack('!L' , MD1)
print struct.unpack('!f' , MD2)
#有精度问题？


# 结束连接
client.disconnect()
print client.get_connected()
client.destroy()