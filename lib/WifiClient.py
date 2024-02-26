# Program to read RGB values from a local Pico Web Server
# Tony Goodhew 5th July 2022
# Connect to network
import network
import time
from secret import ssid, password
import socket

wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(ssid, password)
while not wlan.isconnected() and wlan.status() >= 0:
    print("Waiting to connect:")
    time.sleep(1)
 
# Should be connected and have an IP address
wlan.status() # 3 == success
wlan.ifconfig()
print(wlan.ifconfig())

while True:
    ai = socket.getaddrinfo("192.168.15.142", 80) # Address of Web Server
    addr = ai[0][-1]

    # Create a socket and make a HTTP request
    s = socket.socket() # Open socket
    s.connect(addr)
    s.send(b"GET Data") # Send request
    ss=str(s.recv(512)) # Store reply
    # Print what we received
    print(ss)
    # Split into RGB components
    l = len(ss)
    ss = ss[2:l-1]     # Strip to essentials  
    p = ss.find(",")   # Find first comma
    r = int(ss[0:p])   # Extract RED value
    ss = ss[p+1:]      # Remove red part
    p = ss.find(",")   # Find comma separator
    g = int(ss[0:p])   # Extract GREEN value
    b = int(ss[p+1:])  # Extract BLUE value
    print(r,g,b)       # Print RGB values
    print()
    # Set RGB LED here
    s.close()          # Close socket
    time.sleep(0.2)    # wait