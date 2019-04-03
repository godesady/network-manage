# coding:utf-8
import socket
import struct
import threading
import time
from flask import *
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.DEBUG, filename='server.log', filemode='w',
                    format='%(asctime)s %(filename)s [line:%(lineno)d] %(levelname)s %(message)s')

packet_list = []
cmd_count = 0

cID_list = {
    1:20001,
    2:20002,
    3:20003,
    4:20004
    }

active_cID = []
#####注册报文
def pack_recog(type,function,tID,number,cID):
    #  把字节打包成二进制数据
    imcp_packet = struct.pack('>BBBBB',type,function,tID,number,cID)
    return imcp_packet

def send_packet(cID,type=1,function=2,tID=1,number=1):
    ip = "127.0.0.1"  # 对方ip和端口
    port = cID_list[cID]
    other_addr = (ip, port)
    byte = 1024
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    send_data = pack_recog(type,function,tID,number,cID)
    udp_socket.sendto(send_data, other_addr)
    udp_socket.close()

    
def receive():
    ip = "127.0.0.1"  # 自己ip和端口
    port = 3000
    byte = 1024
    own_addr = (ip, port)  # 接收方端口信息
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_socket.bind(own_addr)
    print('bind on 3000')
    while True:
        recv_data, other_addr = udp_socket.recvfrom(byte)
        packet_list.append(recv_data)

#@app.route("result.html")
def send_cmd(send_data,cID):
    ip = "127.0.0.1"  # 对方ip和端口
    port = cID_list[cID]
    other_addr = (ip,port)
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    send_data = struct.pack('>BBBBB{0}s'.format(len(send_data)),2,1,1,1,cID,send_data)
    udp_socket.sendto(send_data, other_addr)#发送数据
    udp_socket.close()

def deal_regist():
    while True:
        for packet in packet_list:
            if len(packet) == 5:
                Header = packet
                packet_list.remove(Header)
                type,function,tID,number,cID = struct.unpack('>BBBBB',Header)
                if cID in cID_list.keys():
                    #print(cID,'号客户端上线')
                    active_cID.append(cID)
                    send_packet(cID)
                else:
                    send_packet(0)
            else:
                continue

@app.route('/result.html')
def receive_cmd():
    global cmd_count
    result = []
    while True:
        if len(packet_list) == cmd_count:
            break
    if len(packet_list) == cmd_count:
        for packet in packet_list:
            if len(packet) != 5:
                Header = packet
                #packet_list.remove(Header)
                type,function,tID,number,cID,load = struct.unpack('>BBBBB{0}s'.format(len(Header)-5),Header)
                load = load.decode('utf-8')
                load = load.split('##')
                for i in range(len(load)-1):
                    a = load[i].split('#')
                    a.append(str(cID))
                    result.append(a)
            else:
                continue
        packet_list.clear()
        #print(result)
        for res in result:
            if res[2] == '100.0':
                res[1] = '-1'
        cmd_count = 0
        return render_template('result.html',results = result)
    else:
        return render_template('result.html',results = [])


@app.route('/')
def index():
    return redirect('/index.html')

#login
@app.route('/login.html', methods=['GET', 'POST'])
def login():
    pass

@app.route('/index.html', methods=['GET', 'POST'])
def deal_cmd():
    global cmd_count
    if request.method == 'POST':
        cmd = request.form.get('cmd')
        cID = request.form.get('cID')
        send_cmd(bytes(cmd.encode('utf-8')),int(cID))
        cmd_count+=1
    return render_template('index.html')

@app.route('/client.html')
def client_active():
    res = {
        1:'NO',
        2:'No',
        3:'No',
        4:'No'
    }
    for i in range(4):
        if i in active_cID:
            res[i] = 'active'
    return render_template('client.html',result = res)

#def webapp():
#    app.run(debug=True)

threads = []
t1 = threading.Thread(target=receive)
threads.append(t1)
t2 = threading.Thread(target=deal_regist)
threads.append(t2)
#t3 = threading.Thread(target=webapp)
#threads.append(t3)

if __name__ == '__main__':
    for t in threads:
        t.setDaemon(True)
        t.start()
    app.run(host='0.0.0.0',debug=False)
    threads[0].join()