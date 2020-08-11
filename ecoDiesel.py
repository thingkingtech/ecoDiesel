#!/usr/bin/env python

import rdm6300
import time
import serial
from gpiozero import OutputDevice
import RPi.GPIO as GPIO

start = 13
stop = 5
clear = 6
req = 26

GPIO.setmode(GPIO.BCM)

GPIO.setup(start, GPIO.OUT)
GPIO.setup(stop, GPIO.OUT)
GPIO.setup(clear, GPIO.OUT)
GPIO.setup(req, GPIO.OUT)

GPIO.output(start, GPIO.LOW)
GPIO.output(stop, GPIO.LOW)
GPIO.output(clear, GPIO.LOW)
GPIO.output(req, GPIO.LOW)

class Reader(rdm6300.BaseReader):
	def card_inserted(self, card): 
		print("card inserted") 
		if (card.value == tag_id): 
			print('Tag ID: ' + str(card.value)) 
			start_fuel()
		else:
			print('wrong tag inserted')
			

	def card_removed(self, card):
		if (card.value == tag_id):
			print("card removed")
			stop_fuel()
		else:
			print('wrong tag removed')

	def invalid_card(self, card):
		print("invalid card")

reader = rdm6300.Reader('/dev/ttyS0') ##### THIS NEEDS TO CHANGE

# RO  <-> GPIO15/RXD
# RE  <-> GPIO17
# DE  <-> GPIO27
# DI  <-> GPIO14/TXD

# VCC <-> 3.3V
# B   <-> RS-485 B
# A   <-> RS-485 A
# GND <-> GND

re = OutputDevice(17)
de = OutputDevice(27)

global stopped
global started

stopped = True
started = False

mes1 = [0x01, 0x03, 0x00, 0x01, 0x00, 0x00, 0x14, 0x0A]

tag_id = 5028137

timeout = 5

s = serial.Serial(
	port='/dev/ttyS0',    ####### THIS NEEDS TO CHANGE
	baudrate=9600,
	parity=serial.PARITY_NONE,
	stopbits=serial.STOPBITS_ONE,
	bytesize=serial.EIGHTBITS,
	timeout=1
)

fuelling = False

print("System Ready")

def start_button():
	print('start button pushed')
	GPIO.output(start, GPIO.HIGH)
	time.sleep(0.1)
	GPIO.output(start, GPIO.LOW)

def stop_button():
	print('stop button pushed')
	GPIO.output(stop, GPIO.HIGH)
	time.sleep(0.1)
	GPIO.output(stop, GPIO.LOW)
	
def clear_button():
	print('clear button pushed')
	GPIO.output(clear, GPIO.HIGH)
	time.sleep(0.1)
	GPIO.output(clear, GPIO.LOW)

def request():
	print('request high')
	GPIO.output(req, GPIO.HIGH)
	time.sleep(1.5)
	GPIO.output(req, GPIO.LOW)
	print('request low')
	

def start_fuel():
	print('Fuelling')
	started = True
	start_button()
	card = reader.read(timeout=0.5)
	while card:
		card = reader.read(timeout=0.5) 

def stop_fuel():
	print('Fuelling stopped')
	stop_button()
	stopped = True
	start_time = time.time()
	card = reader.read(timeout=0.5)
	while stopped and not card:
		card = reader.read(timeout=0.5)
		if ((time.time()-start_time)>timeout):
			print("Timeout, requesting liters dispensed from pump")
			request()
			stopped = False
			clear_button()
	return stopped
	

while True:
	card = reader.read(timeout=0.5)
	#print(card)
	if card:
		print('Tag Found')
		if card.value == tag_id:
			start_fuel()
		else:
			print('Invalid Tag')
	else:
		print('No Tag')
		stop_fuel()
		card = reader.read(timeout=0.5)
		print('Looking for tags...')
		while not card:
			card = reader.read(timeout=0.5)
			
			
