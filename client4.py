# coding:utf-8
import socket
import struct
import threading
import Ping
import itertools

packet_list = []

#####注册报文
def pack_recog(type,function,tID,number,cID):
    #  把字节打包成二进制数据
    imcp_packet = struct.pack('>BBBBB',type,function,tID,number,cID)
    return imcp_packet
#####控制报文
def pack_cont(type,function,tID,number,cID,load=b'a'):
    #  把字节打包成二进制数据
    imcp_packet = struct.pack('>BBBB32s',type,function,tID,number,cID,load)
    return imcp_packet

def send_packet(cID,type=1,function=1,tID=1,number=1):
    ip = "127.0.0.1"  # 对方ip和端口
    port = 3000
    other_addr = (ip,port)
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    send_data = pack_recog(type,function,tID,number,cID)
    udp_socket.sendto(send_data, other_addr)#发送数据
    udp_socket.close()

def receive_packet():
    ip = "127.0.0.1"  # 自己ip和端口
    port = 20004
    byte = 1024
    own_addr = (ip, port)  # 接收方端口信息
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_socket.bind(own_addr)  # 绑定端口信息
    recv_data, other_addr = udp_socket.recvfrom(byte)
    icmpHeader = recv_data[0:5]
    #print(len(icmpHeader))
    # # 反转编码
    type, function, tID, number, cID= struct.unpack('>BBBBB', icmpHeader)
    #print("收到来自%s的消息: %s %s %s %s %s" % (other_addr,type, function, tID, number, cID))
    udp_socket.close()  # 关闭socket
    return cID

def regist():
    number = 4
    send_packet(number)
    cID = receive_packet()
    #print(cID)
    if cID == number:
        print('regist succeed,start working...')
    else:
        print('regist failed!')

def receive():
    ip = "127.0.0.1"  # 自己ip和端口
    port = 20001
    byte = 1024
    own_addr = (ip, port)  # 接收方端口信息
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_socket.bind(own_addr)
    while True:
        recv_data, other_addr = udp_socket.recvfrom(byte)
        #print('cmd receive')
        packet_list.append(recv_data)

def send(result):
    ip = "127.0.0.1"  # 对方ip和端口
    port = 3000
    other_addr = (ip,port)
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    send_data = imcp_packet = struct.pack('>BBBBB{0}s'.format(len(result)),2,2,1,1,4,result)
    udp_socket.sendto(send_data, other_addr)#发送数据
    udp_socket.close()

def get_iplist(ip):
    ip_list = []
    b = ip.split('/')
    d = b[0].split('.')
    ip_head = ''
    for i in range(int(b[1])//8):
    	ip_head+=d[i]+'.' 

    ip_next = str(bin(int(d[3],10)))[2:]
    ip_next = '0'*(8-len(ip_next))+ip_next

    #print(ip_head,ip_next[:int(b[1])%8])

    for i in itertools.product('01', repeat = 32-int(b[1])):
	    a = ip_next[:int(b[1])%8]+''.join(i)
	    a = ip_head+str(int(a,2))
	    ip_list.append(a)
    return ip_list



def deal_packet():
    while True:
        if packet_list:
            Header = packet_list[0]
            packet_list.remove(Header)
            #print(len(Header))
            type,function,tID,number,cID,load = struct.unpack('>BBBBB{0}s'.format(len(Header)-5),Header)
            #print(load)
            load = load.decode('utf-8')
            print('exec cmd:'+load)
            if '/' in load:
                ip_list = get_iplist(load)
            else:
                ip_list = []
                ip_list.append(load)
            #print(len(load))
            #if load[0:4] == 'ping':
            result = ''
            for host in ip_list:
                lost,time=Ping.ping(host,4)
                result+=host+'#'+str(time)+'#'+str(lost)+'##'
            #print(str(lost)+'%',time,'ms')
            result = bytes((str(result)).encode('utf-8'))
            send(result)
            #print('over')




threads = []
t1 = threading.Thread(target=receive)
threads.append(t1)
t2 = threading.Thread(target=deal_packet)
threads.append(t2)

if __name__ == "__main__":
    regist()
    for t in threads:
        t.setDaemon(True)
        t.start()
    threads[0].join()