import socket
import time
import ip_mail
import os


#s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
#s.connect(("8.8.8.8", 80))
#print(s.getsockname()[0])

#print(socket.gethostbyname(socket.gethostname()))


time.sleep(30)
IPA0 = os.popen('hostname -I').readline(15)
print(IPA0)
f = open("/home/pi/ip.txt", "w")
f.write(str(IPA0))
f.close()
ip_mail.ip_mail()


while True:
    time.sleep(600)
    IPA1 = os.popen('hostname -I').readline(15)
    
    
    if IPA0 != IPA1:
        IPA1 = os.popen('hostname -I').readline(15)
        f = open("/home/pi/ip.txt", "w")
        f.write(str(IPA1))
        f.close()
        IPA0 = IPA1
        ip_mail.ip_mail()
        
    
        
        
    
