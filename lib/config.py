import network
from machine import Pin, ADC, Timer, I2C
from sh1107 import SH1107_I2C
#Offset timezone 1 in winter, 2 in summer
UTC_Offset= 1
#Config led
led = Pin("LED", Pin.OUT)
#Config relay Output 1
relay1=Pin(2, Pin.OUT)
relay2=Pin(3, Pin.OUT)
#config wlan
wlan = network.WLAN(network.STA_IF)

#Publish:
publishString = "picoFront/stat/"

#Subscribe:
subscribeString = "cmnd/apicoFront/relay"

#Temperature sensors:
IDSensorTempFrame=bytearray(b'(\xbd\x9f\x85a"\x06P')
IDSensorTempFlowVentilator=bytearray(b'(\xf0\x08Na"\x06$')


