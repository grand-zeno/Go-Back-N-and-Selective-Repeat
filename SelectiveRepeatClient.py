import threading
import time
import datetime
import socket
import numpy
import argparse
expected=0
RANDOM_DROP_PROB=0.0
PORT_NO=0
SENDER_PORT=0
SENDER_IP=""
MAX_PACKETS=0
Completed=0
SEQ_LEN=0
WINDOW_SIZE=0
base=0
Buffer=[]
st_time=datetime.datetime.now()
actual_nums=[]
def receive_and_ack():
        global RANDOM_PROB
        global expected
        global Completed
        global base
        while Completed<MAX_PACKETS:
                dat,addr=s.recvfrom(1024)
                #print(addr)
                #Lck.acquire()
                SENDER_IP,SENDER_PORT=addr
                dat=dat.decode()
                current_pack=int(((dat).split('?'))[0])
                population=[0,1]
                weights=[RANDOM_DROP_PROB,1-RANDOM_DROP_PROB]
                chosen=numpy.random.choice(population,p=weights)
                is_dropped=True
                if chosen==1:
                    is_dropped=False
                if DEBUG:
                    cur=datetime.datetime.now()-st_time
                    print("Seq "+str(current_pack)+": "+"Time Received: "+str(cur.seconds*1000+cur.microseconds//1000)+":"+str(cur.microseconds%1000)+" Packet Dropped: "+str(is_dropped))
                actual_pack=actual_nums[current_pack]
                if actual_pack<len(Buffer):
                    Buffer[actual_pack]=True
                if actual_pack<base and not is_dropped:
                    s1.sendto(str(current_pack).encode(),addr)
                else:
                    if not is_dropped:
                        s1.sendto(str(current_pack).encode(),addr)
                        while Buffer[base]:
                            base=base+1
                            actual_nums[(base+WINDOW_SIZE)%(2**SEQ_LEN)]=base+WINDOW_SIZE
                            Completed=Completed+1
                            Buffer.append(False)
                #Lck.release()
                        #s1.sendto(str(expected-1).encode(),("127.0.0.1",500))


parser = argparse.ArgumentParser()
parser.add_argument("-d","--debug", help="Switch on Debug mode",action="store_true")
parser.add_argument("-p",help="Port Number of Receiver",type=int)
parser.add_argument("-N",help="Maximum number of packets to be acknowledged",type=int);
parser.add_argument("-n",help="Length of the sequence number field",type=int);
parser.add_argument("-W",help="Size of Window",type=int);
parser.add_argument("-B",help="Buffer Size",type=int);
parser.add_argument("-e",help="Packet Error Rate",type=float)
args=parser.parse_args()
DEBUG=args.debug
PORT_NO=args.p
MAX_PACKETS=args.N
SEQ_LEN=args.n
RANDOM_DROP_PROB=args.e
WINDOW_SIZE=args.W
for i in range(0,WINDOW_SIZE):
    Buffer.append(False)
for i in range(0,2**SEQ_LEN):
    actual_nums.append(i)
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s1= socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
udp_host="127.0.0.1"
udp_port=PORT_NO
s.bind((udp_host,udp_port))
#Lck=threading.lock()
receive_and_ack()
