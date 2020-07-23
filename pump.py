#!/usr/bin/env python3

#' IMPORTANT: remember to add "enable_uart=1" line to /boot/config.txt

from gpiozero import OutputDevice
from time import sleep
import serial
import RPi.GPIO as GPIO
import os

import time
import logging

filenamed='pump_log_'+time.strftime("%Y%m%d")+'.csv'
logging.basicConfig(filename=filenamed, filemode='a', format='%(asctime)s %(message)s', datefmt="%Y-%m-%d; \t %H:%M:%S;", level=logging.INFO)
logfile = open("pump_log_"+time.strftime("%Y%m%d")+".csv", "a")
logfile.write("Date; \tTime; \tVehicleID; \tLiters;\n")
logfile.close()


# RO  <-> GPIO15/RXD
# RE  <-> GPIO17
# DE  <-> GPIO27
# DI  <-> GPIO14/TXD

# VCC <-> 3.3V
# B   <-> RS-485 B
# A   <-> RS-485 A
# GND <-> GND

req = 26

GPIO.setmode(GPIO.BCM)

GPIO.setup(req, GPIO.OUT)
GPIO.output(req, GPIO.LOW)

re = OutputDevice(17)
de = OutputDevice(27)

# enable transmission mode
de.off()
re.off()

s = serial.Serial(
	port='/dev/ttyS0',
	baudrate=9600,
	parity=serial.PARITY_NONE,
	stopbits=serial.STOPBITS_ONE,
	bytesize=serial.EIGHTBITS,
	timeout=1
)

#received = b'\x01\x03\x00\x02\x00\x00\xe4\n\x01\x03\x10\x00\x02\x00\x02\x00\x00\x00\x04\x00\x01\x00\x00\x00\x00\x00\x00C\x1a'
stringed = []
go = True
act=[]
while True:
	if len(act)<2:
		tdata = s.read()           # Wait forever for anything
		sleep(1)              # Sleep (or inWaiting() doesn't give the correct value)
		data_left = s.inWaiting()  # Get the number of characters ready to be read
		tdata += s.read(data_left)
		print((tdata))	
		act = bytearray(tdata)

	if len(act) > 12:
		act = act[8:]
		go=False
		value1 = int(act[4])/100
		value2 = int(act[6])/10
		value3 = int(act[8])/1
		value4 = int(act[10])/0.1
		value5 = int(act[12])/0.01
		total = value1+value2+value3+value4+value5
		print(total)
		act = []
		if (float(total))>0:
			logging.info('\t123; \t'+str(total)+';')
			os.system('mpack -s "pump_logs" '+filenamed+' ecodiesel.capetown@gmail.com')
		

