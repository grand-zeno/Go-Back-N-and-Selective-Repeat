import threading
import time
import socket
import argparse
import datetime
import numpy

Receiver_Name=""
DEBUG=False
PORT_NO=501  #Receiver's Port Number it is set to default:501
PACKET_LENGTH=25
PACKET_GEN_RATE=1
MAX_PACKETS=25
WINDOW_SIZE=5
MAX_BUFFER_SIZE=50
SEQ_LEN=0
Buffer=[]
SEQ_NO=0
base=0
udp_host=0
udp_port=0;
next_seq_num=0
acked_packets=0;
ret=0
RTT=0.0
Send_times=[]
st_time=datetime.datetime.now()
received_acks=0
tot_transmissions=0
packet_timers=[]
no_of_transmissions=[]
is_acked=[]
flag=False
def Generate_Packets():
    global ret
    global acked_packets
    if acked_packets>=MAX_PACKETS or (ret>=10):
        #if timer.is_alive():
        #    timer.cancel()
        exit()
    global SEQ_NO
    global PACKET_LENGTH
    global PACKET_GEN_RATE
    global MAX_BUFFER_SIZE
    global Buffer
    info=str(SEQ_NO%(2**(SEQ_LEN)))
    while(len(info)<numpy.random.choice(PACKET_LENGTH-40)+41):
        info=info+"?"
    if(len(Buffer)-base<MAX_BUFFER_SIZE):
        Lck.acquire()
        Buffer.append(info)
        packet_timers.append(None)
        Send_times.append(0)
        is_acked.append(False)
        no_of_transmissions.append(0)
        Lck.release()
        SEQ_NO=SEQ_NO+1
    threading.Timer(1.0/PACKET_GEN_RATE , Generate_Packets).start()
    
    
def rdt_send():
    global timer
    global s
    global next_seq_num
    global Buffer
    global ret
    global acked_packets
    global Send_times
    global tot_transmissions
    while True and acked_packets<MAX_PACKETS and ret<10:
        if(len(Buffer)>base and next_seq_num<base+WINDOW_SIZE and next_seq_num<len(Buffer) and not flag):
            #Send Packet to Receiver
            Lck.acquire()
            s1.sendto(Buffer[next_seq_num].encode(),(Receiver_Name,PORT_NO))
            Send_times[next_seq_num]=datetime.datetime.now()
            no_of_transmissions[next_seq_num]=no_of_transmissions[next_seq_num]+1
            tot_transmissions=tot_transmissions+1
            if acked_packets<10:
                packet_timers[next_seq_num]=threading.Timer(0.3,timeout,[next_seq_num]);
                packet_timers[next_seq_num].start()
            else:
                packet_timers[next_seq_num]=threading.Timer(2*RTT,timeout,[next_seq_num]);
                packet_timers[next_seq_num].start()
            next_seq_num=next_seq_num+1
            Lck.release()
    exit()
        
def timeout(seq_num):
    Lck.acquire()
    #print("Timeout: "+str(seq_num))
    packet_timers[seq_num].cancel()
    global timer
    global s
    global ret
    global acked_packets
    global Send_times
    global tot_transmissions
    no_of_transmissions[seq_num]=no_of_transmissions[seq_num]+1
    ret=max(ret , no_of_transmissions[seq_num])
    if acked_packets<10:
        packet_timers[seq_num]=threading.Timer(0.1,timeout,[seq_num]);
    else:
        packet_timers[seq_num]=threading.Timer(2*RTT,timeout,[seq_num]);
    packet_timers[seq_num].start()
    s1.sendto(Buffer[seq_num].encode(),(Receiver_Name,PORT_NO))
    Send_times[seq_num]=datetime.datetime.now()
    tot_transmissions=tot_transmissions+1
    Lck.release()
   

def start_timer():
    global timer
    timer.start()

def receive_acks():
    global timer
    global s
    global ret
    global acked_packets
    global base
    global RTT
    global received_acks
    global tot_transmissions
    while True and acked_packets<MAX_PACKETS and ret<10:
        ack_seq_no,addr=s1.recvfrom(1024)
        Lck.acquire()
        prev_base=base
        
        cur=(datetime.datetime.now()-Send_times[int(ack_seq_no)])
        RTT=RTT*received_acks+cur.seconds+cur.microseconds/1000000.0
        received_acks=received_acks+1
        RTT=RTT/received_acks
        actual_seq_num=(int(ack_seq_no))%(2**SEQ_LEN)+base-(base%(2**SEQ_LEN))
        if DEBUG:
            gen_time= Send_times[int(ack_seq_no)]-st_time
            print("Seq "+str(int(ack_seq_no))+": Time Generated : " + str(gen_time.seconds*1000+gen_time.microseconds//1000)+" : "+str(gen_time.microseconds%1000)+" RTT : "+str(RTT)+" Number of attempts : "+str(no_of_transmissions[actual_seq_num]))
        packet_timers[actual_seq_num].cancel()
        is_acked[actual_seq_num]=True
        while base<len(Buffer) and is_acked[base] and base<next_seq_num:
            base=base+1
        acked_packets=base
        Lck.release()
    exit()
    

parser = argparse.ArgumentParser()
parser.add_argument("-d","--debug", help="Switch on Debug mode",action="store_true")
parser.add_argument("-s",help="Name/Ip address of receiver",type=str)
parser.add_argument("-p",help="Port Number of Receiver",type=int)
parser.add_argument("-n",help="Length of the Sequence NUmber Field",type=int)
parser.add_argument("-L",help="Length of Packet",type=int)
parser.add_argument("-R",help="Packet Generation Rate",type=float)
parser.add_argument("-N",help="Maximum number of packets to be sent and acknowledged",type=int);
parser.add_argument("-W",help="Size of window",type=int)
parser.add_argument("-B",help="Maximum size of buffer",type=int)
args=parser.parse_args()
DEBUG=args.debug
Receiver_Name=args.s
PORT_NO=args.p
SEQ_LEN=args.n
PACKET_LENGTH=args.L
PACKET_GEN_RATE=args.R
MAX_PACKETS=args.N
WINDOW_SIZE=args.W
MAX_BUFFER_SIZE=args.B
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
udp_host="127.0.0.1"
udp_port=500
s1 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s1.bind((udp_host,udp_port))
Lck=threading.Lock()
t1 = threading.Thread(target=Generate_Packets)
t2 = threading.Thread(target=rdt_send)
t3 = threading.Thread(target=receive_acks)
t1.setDaemon(True)
t3.setDaemon(True)
t1.start()
t2.start()
t3.start()
t2.join()
for i in range(0,len(packet_timers)):
    if not (packet_timers[i]==None) and packet_timers[i].is_alive():
        packet_timers[i].cancel()
print("")
print("PACKET GENERATION RATE: "+str(PACKET_GEN_RATE))
print("PACKET LENGTH: "+str(PACKET_LENGTH))
print("RETRANSMISSION RATIO: "+str(tot_transmissions/received_acks))
print("RTT: "+str(RTT*1000))
print("")
exit()

