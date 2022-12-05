import socket
import time
import ip_mail
import os

time.sleep(30)
IPA0 = os.popen('hostname -I').readline(15)
print(IPA0)
f = open("/home/pi/ip.txt", "w")
f.write(str(IPA0))
f.close()
ip_mail.ip_mail()


while True:
    IPA0 = os.popen('hostname -I').readline(15)
    time.sleep(10)
    IPA1 = os.popen('hostname -I').readline(15)
    
    if IPA0 != IPA1:
        f = open("/home/pi/ip.txt", "w")
        f.write(str(IPA1))
        f.close()
        ip_mail.ip_mail()
        
    