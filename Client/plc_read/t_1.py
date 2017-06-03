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

#写DB位地址,例如DB4.DB1.6为1
client.write_area(area = ID.S7AreaDB , dbnumber = 4 , start = 1 , data = chr(64))
#读M位地址,例如M6.7为1: B:7,W:15,D:31
buffer = client.read_area(area = ID.S7AreaDB , dbnumber = 4 , start = 1 , size = 1)
print struct.unpack('!?', buffer)
temp = 7
buffer1 = []
for x in buffer:
    buffer1.extend(bin(x).replace('0b','').rjust(8 , '0'))
print buffer1[abs(temp - 6)]
#print buffer1


#写DB字地址,H无符号，h有符号
client.write_area(area = ID.S7AreaDB , dbnumber = 1 , start = 200 , data = struct.pack('!h',-12))
client.write_area(area = ID.S7AreaDB , dbnumber = 1 , start = 202 , data = struct.pack('!H',12))
#读DB字地址,
DW0 = client.read_area(area = ID.S7AreaDB , dbnumber = 1 , start = 200 , size = 2)
DW1 = client.read_area(area = ID.S7AreaDB , dbnumber = 1 , start = 202 , size = 2)
print struct.unpack('!h' , DW0)
print struct.unpack('!H' , DW1)



#写DB双字地址，L:unsigned int,f:real
client.write_area(area = ID.S7AreaDB , dbnumber = 1 , start = 196 , data = struct.pack('!L',12))
client.write_area(area = ID.S7AreaDB , dbnumber = 1 , start = 204 , data = struct.pack('!f',12.9))
#读M双字地址,
DD0 = client.read_area(area = ID.S7AreaDB , dbnumber = 1 , start = 196 , size = 4)
DD1 = client.read_area(area = ID.S7AreaDB , dbnumber = 1 , start = 204 , size = 4)
print struct.unpack('!L' , DD0)
print struct.unpack('!f' , DD1)
#有精度问题？


# 结束连接
client.disconnect()
print client.get_connected()
client.destroy()
