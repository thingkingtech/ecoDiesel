#!/usr/bin/env python3

#' IMPORTANT: remember to add "enable_uart=1" line to /boot/config.txt

from __future__ import print_function
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

from gpiozero import OutputDevice
from time import sleep
import serial
import RPi.GPIO as GPIO
import os

import time
import logging



# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/drive']

# The ID and range of a sample spreadsheet.
SAMPLE_SPREADSHEET_ID = '1WYrr7KdKaIW5u76SWWCf06A_tXwfrKpkuSoyBJ_m740'
SAMPLE_RANGE_NAME = 'Data!A16'

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

    update_values(creds, SAMPLE_SPREADSHEET_ID, 'Data!A1:D1', 'USER_ENTERED', [['vehicleID', 'date', 'time', 'liters']])

if __name__ == '__main__':
    main()


# while True:
	# if len(act)<2:
		# tdata = s.read()           # Wait forever for anything
		# sleep(1)              # Sleep (or inWaiting() doesn't give the correct value)
		# data_left = s.inWaiting()  # Get the number of characters ready to be read
		# tdata += s.read(data_left)
		# print((tdata))	
		# act = bytearray(tdata)

	# if len(act) > 12:
		# act = act[8:]
		# go=False
		# value1 = int(act[4])/100
		# value2 = int(act[6])/10
		# value3 = int(act[8])/1
		# value4 = int(act[10])/0.1
		# value5 = int(act[12])/0.01
		# total = value1+value2+value3+value4+value5
		# print(total)
		# act = []
		# if (float(total))>0:
			# logging.info('\t123; \t'+str(total)+';')
			# os.system('mpack -s "pump_logs" '+filenamed+' ecodiesel.capetown@gmail.com')
		

