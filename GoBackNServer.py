import threading
import time
import socket
import argparse
import datetime

Receiver_Name=""
DEBUG=False
PORT_NO=501  #Receiver's Port Number it is set to default:501
PACKET_LENGTH=25
PACKET_GEN_RATE=1
MAX_PACKETS=25
WINDOW_SIZE=5
MAX_BUFFER_SIZE=50
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
flag=False
def Generate_Packets():
    global ret
    global acked_packets
    if acked_packets>=MAX_PACKETS or (ret>=5 and base<next_seq_num):
        if timer.is_alive():
            timer.cancel()
        #print("Done")
        exit()
    global SEQ_NO
    global PACKET_LENGTH
    global PACKET_GEN_RATE
    global MAX_BUFFER_SIZE
    global Buffer
    info=str(SEQ_NO)
    #print("Generating"+str(info))
    while(len(info)<PACKET_LENGTH):
        info=info+"?"
    if(len(Buffer)-base<MAX_BUFFER_SIZE):
        Lck.acquire()
        Buffer.append(info)
        Send_times.append(st_time)
        Lck.release()
       # print(Buffer)
        SEQ_NO=SEQ_NO+1
    #Lck.release()
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
    while True and acked_packets<MAX_PACKETS and (ret<5 or base==next_seq_num):
        if(len(Buffer)>base and next_seq_num<base+WINDOW_SIZE and next_seq_num<len(Buffer) and not flag):
            #Send Packet to Receiver
            Lck.acquire()
            s1.sendto(Buffer[next_seq_num].encode(),(Receiver_Name,PORT_NO))
            Send_times[next_seq_num]=datetime.datetime.now()
            tot_transmissions=tot_transmissions+1
            #print("Added "+str(next_seq_num))
            Lck.release()
            #print("I sent Something")
            if base==next_seq_num:
                ret=0
                timer.cancel()
                if acked_packets<10:
                    timer=threading.Timer(0.1,timeout);
                else:
                    timer=threading.Timer(2*RTT,timeout);
                timer.start()
            next_seq_num=next_seq_num+1
    #rdt_send()
    if timer.is_alive():
        timer.cancel()
    #print("Done")
    exit()
        
def timeout():
   # Lck.acquire()
    global timer
    global s
    global ret
    global acked_packets
    global Send_times
    global tot_transmissions
    flag=True
    timer.cancel()
    if acked_packets<10:
        timer=threading.Timer(0.1,timeout);
    else:
        timer=threading.Timer(2*RTT,timeout);
    timer.start()
    #print("timeout")
    if base<next_seq_num:
        ret=ret+1
        
    for j in range(base,next_seq_num):
        #Send packet to receiver
        Lck.acquire()
        s1.sendto(Buffer[j].encode(),(Receiver_Name,PORT_NO))
        Send_times[j]=datetime.datetime.now()
        tot_transmissions=tot_transmissions+1
        #print("Added "+str(j))
        Lck.release()
    flag=False
   # Lck.release()
  
timer=threading.Timer(0.1,timeout);

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
    while True and acked_packets<MAX_PACKETS and (ret<5 or base==next_seq_num):
        ack_seq_no,addr=s1.recvfrom(1024)
        prev_base=base
        base=max(base,int(ack_seq_no)+1)
        acked_packets=base
        #print(Send_times)
        cur=(datetime.datetime.now()-Send_times[int(ack_seq_no)])
        RTT=RTT*received_acks+cur.seconds+cur.microseconds/1000000.0
        received_acks=received_acks+1
        RTT=RTT/received_acks
        if DEBUG:
            gen_time= Send_times[int(ack_seq_no)]-st_time
            print("Seq "+str(int(ack_seq_no))+": Time Generated : " + str(gen_time.seconds*1000+gen_time.microseconds//1000)+" : "+str(gen_time.microseconds%1000)+" RTT : "+str(RTT)+" Number of attempts : "+str(ret+1))
        if base==next_seq_num:
            ret=0
            timer.cancel()
        else:
            timer.cancel()
            if acked_packets<10:
                timer=threading.Timer(0.1,timeout);
            else:
                timer=threading.Timer(2*RTT,timeout);
            timer.start()
    if timer.is_alive():
        timer.cancel()
    #print("Done")
    exit()
    

parser = argparse.ArgumentParser()
parser.add_argument("-d","--debug", help="Switch on Debug mode",action="store_true")
parser.add_argument("-s",help="Name/Ip address of receiver",type=str)
parser.add_argument("-p",help="Port Number of Receiver",type=int)
parser.add_argument("-l",help="Length of Packet",type=int)
parser.add_argument("-r",help="Packet Generation Rate",type=float)
parser.add_argument("-n",help="Maximum number of packets to be sent and acknowledged",type=int);
parser.add_argument("-w",help="Size of window",type=int)
parser.add_argument("-b",help="Maximum size of buffer",type=int)
args=parser.parse_args()
DEBUG=args.debug
Receiver_Name=args.s
PORT_NO=args.p
PACKET_LENGTH=args.l
PACKET_GEN_RATE=args.r
MAX_PACKETS=args.n
WINDOW_SIZE=args.w
MAX_BUFFER_SIZE=args.b
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
udp_host="127.0.0.1"
udp_port=500
s1 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s1.bind((udp_host,udp_port))
#print ("Hi")
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
print("")
print("PACKET GENERATION RATE: "+str(PACKET_GEN_RATE))
print("PACKET LENGTH: "+str(PACKET_LENGTH))
print("RETRANSMISSION RATIO: "+str(tot_transmissions/received_acks))
print("RTT: "+str(RTT*1000))
print("")
exit()
