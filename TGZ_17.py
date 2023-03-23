import sys
import os
import time 
import datetime 
import matplotlib.pyplot as plt
import RPi.GPIO as GPIO
import psutil
import numpy as np
import koji_mail


#Kernelmodule laden
os.system('modprobe w1-gpio')
os.system('modprobe w1-therm')

#1wire-Tempsensoren auslesen:
sensorcount = 2                                            #Festlegen, wieviele Sensoren vorhanden sind
sensors = ['28-00000016d974', '28-00000b1fd876']          #Array mit den Sensor-IDs
sensorpath = '/sys/bus/w1/devices/'                        #Pfad zum Sensorverzeichnis
sensorfile = '/w1_slave'





pin = 17  
count = 0
gas_volume = 0
r = 0
start = datetime.datetime.now()
x = [start]
y = [0]
y2 = [0]
V_diff = 0
V1 = 0
V2 = 0
T1 = 0
T2 = 0
SENT = True


GPIO.setmode(GPIO.BCM)  
GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)


timestr = time.strftime("%Y%m%d_%H%M%S")
data = "/home/pi/stta/data/" + "TGZ_17_" + timestr+ ".txt"
f = open(data,  "w")
f.write("Datum/Zeit,      Gasvolumen[L],  CO2-Volumenstrom [ml/h],    Koji-Temp.[°C],   cpu[%]" + '\n')
f.close()




def callsensor(sensor):

    f = open(sensorpath + sensor + sensorfile, 'r')       #Pfad, Sensor-ID und Geraetedatei zusammensetzen, Datei im Lesemodus oeffnen
    lines = f.readlines()                     #Inhalt der Datei in lines schreiben
    f.close()                         #Datei schliessen
    temp_line = lines[1].find('t=')               #Den Index (Position) von t= in temp_line schreiben
    temp_output = lines[1].strip() [temp_line+2:]       #Index 1 (Zeile 2) strippen und die Zeichen nach t= in temp_output schreiben
    temp_celsius = float(temp_output) / 1000            #Tausendstelgrad durch 1000 teilen und so in Grad Celsius wandeln, in temp_celsius
    return temp_celsius

def DS1820(T1, T2):
    s1 = sensors[0]
    s2 = sensors[1]
    T1 = round(((callsensor(s1)) + 0.22), 2)
    if (T1 > 125):
        T1 = round((T1 - 4096), 2)
    T2 = round(((callsensor(s2)) - 0.4), 2)
    if (T2 > 125):
        T2 = round((T2 -4096), 2)
    return(T1,T2)
T1 = (DS1820(T1,T2)[0])



### Prepare the plot
# Clean up and exit on matplotlib window close
def on_close(event):
    f.close()  # Save file one last time
    print("Cleaning up...")
    GPIO.cleanup()
    print("Bye :)")
    sys.exit(0)





def on_trigger(triggered_pin):
    global count
    count = count + 1
    
GPIO.add_event_detect(pin, GPIO.RISING, callback=on_trigger,bouncetime = 179)#1/(50L*1000ml/2,5/60/60)=178,6ms Maximum
t_start = time.time()

plt.ion() # Interactive mode otherwise plot won't update in real time
fig = plt.figure(figsize=(8, 11))
fig.canvas.manager.set_window_title("TGZ 17")
#fig.canvas.manager.full_screen_toggle()
fig.canvas.mpl_connect("close_event", on_close) # Connect the plot window close event to function on_close
ax = fig.add_subplot(111)
ax2 = ax.twinx() # Get a second y axis
(vol_line,) = ax.plot(x, y, label="TGZ 17 Gasvolumen", color="#00549F", marker=".") #00549F is the RWTH blue color
ax.set_ylabel("TGZ 17 Gasvolumen in L", color="#00549F")
(rate_line,) = ax2.plot(x, y2, label="TGZ CO2-Volumenstrom", color="#CC071E", linestyle="dotted", marker=".") #CC071E is the RWTH red (both colors as defined in the official RWTH guide)
ax2.set_ylabel("TGZ 17 CO2-Volumenstrom [ml/h]", color="#CC071E")
#plt.ylim(22, 35)#commented out because it overrides dynamic axes scaling
plt.title("TGZ 17: " + "\n" + str(gas_volume) + "L  " + str(T1) + " °C", fontsize=25) # To display 0ml initially. Will be updated in an event-driven manner (see on_trigger)
plt.xlabel("Zeit [h]", fontsize=15)

try:
    while True:
        T1 = (DS1820(T1,T2)[0])
        t_end = time.time() 
        z = datetime.datetime.now()
        delta = z - x[-1]  # Last element in x is the timestamp of the last measurement!
        # Put new values into their respective lists..        
        x.append(z)
        gas_volume = count*2.5/1000
        y.append(gas_volume)
        V2 = gas_volume
        V_diff = (V2 - V1)*1000
        
        if V_diff > 15:
            r = round((V_diff / (t_end - t_start)*60*60),2)
            t_start = time.time()
            V1 = V2
            

        else:
            r = np.nan
            print(r)
        y2.append(r)
        timestr = time.strftime("%d.%m.%y   %H:%M:%S")
        plt.title(timestr + "    TGZ 17: " + "\n" + str(gas_volume) + "L  " + str(r) + " ml/h   "+ str(T1) + " °C", fontsize=25)#Diagrammtitel
        vol_line.set_xdata(x)
        vol_line.set_ydata(y)
        rate_line.set_xdata(x)
        rate_line.set_ydata(y2)
        
        ax.relim()  # Rescale data limit for first line
        ax.autoscale_view()  # Rescale view limit for first line
        ax2.relim()  # Rescale data limit for second line
        ax2.autoscale_view()  # Rescale view limit for second line

        fig.canvas.draw()
        fig.canvas.flush_events()
        
        cpu = psutil.cpu_percent(2)
        Zeit = time.strftime("%Y-%m-%d %H:%M:%S")
        f = open(data, "a")
        f.write(Zeit + ",       " + str(gas_volume) + ",         " + str(r) +  ",                   "  +  str(T1) + ",         " + str(cpu) + "\n")
        f.close()
        
        try:
            if T1 > 30 and SENT == True:
                koji_mail.koji_mail(T1)
                SENT = False
            else:
                print(T1)
        except:
            print()
        time.sleep(600)
        


except KeyboardInterrupt:
    print("keyboardInterrupt")
    timestr = time.strftime("%Y%m%d_%H%M%S")
    f = open(data, "a")
    f.write("KeyboardInterrupt at: " + timestr + "\n")
    f.close()
    GPIO.cleanup()
    print("\nBye")
    sys.exit()



