#!/usr/bin/env python

from __future__ import print_function
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

import rdm6300
import time
import serial
from gpiozero import OutputDevice
import RPi.GPIO as GPIO

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/drive']

# The ID and range of a sample spreadsheet.
SAMPLE_SPREADSHEET_ID = '1WYrr7KdKaIW5u76SWWCf06A_tXwfrKpkuSoyBJ_m740'
SAMPLE_RANGE_NAME = 'Data!A16'

# filenamed='pump_log_'+time.strftime("%Y%m%d")+'.csv'
# logging.basicConfig(filename=filenamed, filemode='a', format='%(asctime)s %(message)s', datefmt="%Y-%m-%d; \t %H:%M:%S;", level=logging.INFO)
# logfile = open("pump_log_"+time.strftime("%Y%m%d")+".csv", "a")
# logfile.write("Date; \tTime; \tVehicleID; \tLiters;\n")
# logfile.close()

start = 5
stop = 6
clear = 13

GPIO.setmode(GPIO.BCM)

GPIO.setup(start, GPIO.OUT)
GPIO.setup(stop, GPIO.OUT)
GPIO.setup(clear, GPIO.OUT)

GPIO.output(start, GPIO.LOW)
GPIO.output(stop, GPIO.LOW)
GPIO.output(clear, GPIO.LOW)

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

s1 = serial.Serial(
	port='/dev/ttyUSB0',    
	baudrate=9600,
	parity=serial.PARITY_NONE,
	stopbits=serial.STOPBITS_ONE,
	bytesize=serial.EIGHTBITS,
	timeout=1
)

s2 = serial.Serial(
	port='/dev/ttyUSB1',    
	baudrate=9600,
	parity=serial.PARITY_NONE,
	stopbits=serial.STOPBITS_ONE,
	bytesize=serial.EIGHTBITS,
	timeout=1
)

fuelling = False
act=[]

print("System Ready")

def update_values (creds, spreadsheet_id, range_name, value_input_option,
                      _values):
		
						  
        service = build('sheets', 'v4', credentials=creds)
        # [START sheets_update_values]
        values = [
            [
                # Cell values ...
            ],
            # Additional rows ...
        ]
        # [START_EXCLUDE silent]
        values = _values
        # [END_EXCLUDE]
        body = {
            'values': values
        }
        result = service.spreadsheets().values().append(
            spreadsheetId=spreadsheet_id, range=range_name,
            valueInputOption=value_input_option, body=body).execute()
        print('{0} cells updated.'.format(result.get('updatedCells')))
        # [END sheets_update_values]
        return result

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
			stopped = False
			s1.write(serial.to_bytes(mes1))
			s1.flush()
			tdata = s2.read()           # Wait forever for anything
			time.sleep(1)              # Sleep (or inWaiting() doesn't give the correct value)
			data_left = s2.inWaiting()  # Get the number of characters ready to be read
			tdata += s2.read(data_left)
			print((tdata))	
			
			act = bytearray(tdata)
			act=act[8:]
			value1 = int(act[4])/100
			value2 = int(act[6])/10
			value3 = int(act[8])/1
			value4 = int(act[10])/0.1
			value5 = int(act[12])/0.01
			total = value1+value2+value3+value4+value5
			print(total)
			act = []
			
			
			clear_button()
			
			update_values(creds, SAMPLE_SPREADSHEET_ID, 'Data!A1:D1', 'USER_ENTERED', [[tag_id, 'date', 'time', total]])
			
			return stopped
	

def main():
    """Shows basic usage of the Sheets API.
    Prints values from a sample spreadsheet.
    """
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = build('sheets', 'v4', credentials=creds)
    
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

    #update_values(creds, SAMPLE_SPREADSHEET_ID, 'Data!A1:D1', 'USER_ENTERED', [['vehicleID', 'date', 'time', 'liters']])

if __name__ == '__main__':
    main()

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
			
			
