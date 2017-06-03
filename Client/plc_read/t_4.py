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



#写Q位地址,例如Q6.0为1
client.write_area(area = ID.S7AreaPA , dbnumber = 0 , start = 6 , data = chr(1))
#读M位地址,例如i0.0为1,temp取值： B:7,W:15,D:31
QB = client.read_area(area = ID.S7AreaPA , dbnumber = 0 , start = 6 , size = 1)
temp = 7
buffer = []
for x in QB:
    buffer.extend(bin(x).replace('0b','').rjust(8 , '0'))
print buffer[abs(temp - 0)]
#print buffer


#写Q字地址,例如QB9
client.write_area(area = ID.S7AreaPA , dbnumber = 0 , start = 9 , data = chr(2))
#读Q字地址,
QW = client.read_area(area = ID.S7AreaPA , dbnumber = 0 , start = 9 , size = 2)
sumW = 0
for x in QW:
    sumW = sumW*256 + x
print '{0:016b}'.format(sumW)



#写Q双字地址QD2
client.write_area(area = ID.S7AreaPA , dbnumber = 0 , start = 2 , data = chr(1))
#读Q双字地址,
QD = client.read_area(area = ID.S7AreaPA , dbnumber = 0 , start = 2 , size = 4)
sumD = 0
for x in QD:
    sumD = sumD*256 + x
print '{0:032b}'.format(sumD)



# 结束连接
client.disconnect()
print client.get_connected()
client.destroy()