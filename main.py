# Author: WimShu
# Date: Feb 25th, 2024
# Version: HeaterPico
# 
import network
import socket
import time
from phew import connect_to_wifi, logging, server, is_connected_to_wifi
from phew.template import render_template
from machine import Pin, ADC, Timer
from secret import ssid, password , mqttBrokerIP, mqttclient_id, mqttuser, mqttpassword, deviceID
from config import relay1, relay2, IDSensorTempFrame, IDSensorTempFlowVentilator, led, UTC_Offset, publishString, subscribeString
import random
from umqtt.simple import MQTTClient
import onewire, ds18x20



#Variables:
heating1 = False #Back accumulator heating up
heating2 = False #Water boiler heating up

textHeating1 = "Heating off" #Back accumulator heating up
textHeating2 = "Heating off" #Water boiler heating up
textTempUnit = "55" #Front accumulator heating up
textTempFan = "56" #Spare
ip = "0.0.0.0"

statusPico = 1000



def readTemp():
    global textTempUnit
    global textTempFan
    #Temperature config ds18x20
    ds_pin = machine.Pin(22)
    ds_sensor = ds18x20.DS18X20(onewire.OneWire(ds_pin))
    
    roms = ds_sensor.scan()
    logging.info('Scan result %s' %(roms))
    try:
        ds_sensor.convert_temp()
        
        #time.sleep(1)
        nrRom=1
        for rom in roms:
            temp =str(ds_sensor.read_temp(rom))
            
            logging.info('temp DS18D20:%s, %s'%(rom, temp))
            if rom == IDSensorTempFrame :
                textTempUnit = temp
                logging.info('Temperature Frame:%s, %s, %s'%(rom, temp, textTempUnit))
            elif rom == IDSensorTempFlowVentilator:
                textTempFan = temp
                logging.info('Temperature Airflow:%s, %s, %s'%(rom, temp, textTempFan))
            #time.sleep(1)
            nrRom=nrRom+1
        
    except:
          logging.info('No sensors detected!')


def message():
    global MSG_mqtt_Stat
    MSG_mqtt_Stat ='{"time" : "' + local_Time_Display() +'", "date" : "' + local_Date_Display() + '", "Relay_1" : "' + textHeating1 + '", "Relay_2" : "' + textHeating2 + '", "Temp_Unit" : "' + textTempUnit + '", "Temp_Fan" : "' + textTempFan + '", "IP" : "' + ip + '"}'

def connectMQTT():
    '''Connects to Broker'''
    # Client ID can be anything
    #logging.info( str(mqttclient_id) + " / " + str(mqttBrokerIP) + " / " + str(mqttuser)  + " / " + str(mqttpassword))
    client = MQTTClient(
        client_id=mqttclient_id,
        server=mqttBrokerIP,
        port=0,
        user=mqttuser,
        password=mqttpassword,
        keepalive=7200,
        ssl=False,
        #ssl_params={'server_hostname': mqttBrokerIP}
    )
    logging.info('connection to mqtt broker')
    
    
    
    return client

#For the webserver and oled
def getNow():
    return time.gmtime(time.time() + UTC_Offset *3600)

def local_TimeAndDate_Display():
    ldatetime = time.gmtime()
    #logging.info("Start conversion " + str(ldatetime))
    timetext="%s:%s:%s" %(str(ldatetime[3]), str(ldatetime[4]), str(ldatetime[5]))
    #logging.info(timetext)
    datetext="%s/%s/%s" %(str(ldatetime[2]), str(ldatetime[1]), str(ldatetime[0]))
    #logging.info(datetext)
    dateTimeText = " %s  /  %s " %(datetext, timetext)
    #logging.info(dateTimeText)
    return dateTimeText
def local_Time_Display():
    ldatetime = time.gmtime()
    #logging.info("Start conversion " + str(ldatetime))
    timeText="%s:%s:%s" %(str(ldatetime[3]), str(ldatetime[4]), str(ldatetime[5]))
    #logging.info(timeText)
    return timeText
def local_Date_Display():
    ldatetime = time.gmtime()
    #logging.info("Start conversion " + str(ldatetime))
    dateText="%s/%s/%s" %(str(ldatetime[2]), str(ldatetime[1]), str(ldatetime[0]))
    #logging.info(dateText)
    return dateText

def connect_to_internet(_ssid, _password):
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    time.sleep(5)
    print('Wifi network :' + _ssid + '. Password : ' + _password)
    
    wlan.connect(_ssid, _password)
    
    max_wait = 10
    while (wlan.isconnected() == False) and (max_wait > 0):
        print('Waiting for connection ...')
        time.sleep(2)
        max_wait -= 1
    print(wlan.ifconfig())      
    
    max_wait = 10
    while max_wait > 0:
        if wlan.status() < 0 or wlan.status() >= 3:
            break
        max_wait -= 1
        print('waiting on connection ...')
        time.sleep(1)
    if wlan.status() != 3:
        print(wlan.status())
        raise RuntimeError('Network connection Failed')
    else:
        print('Connected')
        print(wlan.status())
        status = wlan.ifconfig()

def publish(topic, value, client):
    '''Sends data to the broker'''
    print(topic)
    print(value)
    client.publish(topic, value)
    print("Publish Done")

def sub_cb(topic, msg):
    print((topic, msg))
    
    
class Temperature:
    def __init__(self):
        adcpin = 4
        self.sensor = ADC(adcpin)
        
        
    def ReadTemperature(self):
        adc_value = self.sensor.read_u16()
        volt = (3.3/65535)*adc_value
        temperature = 27 - (volt - 0.706)/0.001721
        return round(temperature, 1)
    

import uasyncio

def mainTempPico():
    logging.info("Start the main task for temperature read")
    
    
    readTemp()
    
    #mqttclient.check_msg()
    
    
    
async def startupTask():
    logging.info("Startup pico")
    global statusPico
    relay1.value(1)
    relay2.value(1)    
    logging.info("Startup pico")
    checkingWifi = False
    while not checkingWifi:
        led.toggle()
        checkingWifi = is_connected_to_wifi()
        logging.info("Wifi connection is " + str(checkingWifi))
        statusPico = 2000
        await uasyncio.sleep(1)
        
    import ntptime, machine
    #Read and set RTC with UTC clock from internet connection
    ntptime.settime()
    #Change time to local time with UTC_offset
    timestamp = getNow()
    #Write to the pico
    machine.RTC().datetime((
      timestamp[0], timestamp[1], timestamp[2], timestamp[6], 
      timestamp[3], timestamp[4], timestamp[5], 0))
        
    
    logging.info("Startup pico done")
    
    await uasyncio.sleep(1)
    
async def ConnectToWifi():
    global ip
    while True:
        try:        
            ip = connect_to_wifi(ssid, password)
            logging.info("Pico is connected to " + ip)
            while is_connected_to_wifi():
                logging.info("Pico Wifi is alive")
                await uasyncio.sleep(30)
                
        except:
            logging.error("Wifi is not connected")
        await uasyncio.sleep(60)
        
    
async def mqtt_Task():
    global mqttclient_Pico
    mqttclient_Pico = connectMQTT()
    while True:
        try:
            
            mqttclient_Pico.connect()
            logging.info("MQTT connected")
            mqttclient_Pico.set_callback(sub_cb)
            mqttclient_Pico.subscribe(subscribeString)
            statusPico = 2500
            while True:
                try:
                    message()
                    topic = publishString
                    value = MSG_mqtt_Stat
                    publish(topic, value, mqttclient_Pico)
                    await uasyncio.sleep(15)
                    
                except:
                    logging.info("MQTT publish error")
                    break
                     
        except:
            logging.info("MQTT error logon to broker")
        await uasyncio.sleep(60)
        
async def main():
        
        
        logging.info("Pico is Powered on ")
        
        
        task1 = startupTask()
        uasyncio.create_task(task1)
        logging.info("Task 1 is started")
        await uasyncio.sleep(1)
        
        
        task2 = ConnectToWifi()
        uasyncio.create_task(task2)
        logging.info("Task 2 is started")
        await uasyncio.sleep(2)
        
        if is_connected_to_wifi():
            task3 = mqtt_Task()
            uasyncio.create_task(task3)
            logging.info("Task 3 is started")
        await uasyncio.sleep(5)
#         #Main loop to read temp      
#         task4 = mainTempPico()
#         uasyncio.create_task(task4)
#         logging.info("Task 4 is started")
        
        counter = 0
        while True:
            counter +=1
            logging.info("Counter loop troughs " + str(counter))
            mainTempPico()
            await uasyncio.sleep(10)
              
          
            

try:
    uasyncio.run(main())
finally:
    
    uasyncio.new_event_loop()    

    