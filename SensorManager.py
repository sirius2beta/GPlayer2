import time
import threading
import subprocess
import serial
SENSOR = b'\x50'
class SensorManager:
	def __init__(self):
		self.name = 'sensor'
		self._on_message = None
		self._sensorList = [[1,'i']]
		self.thread_terminate = False
		self.thread_sensor = threading.Thread(target=self.sensorLoop)
		self.thread_sensor.start()
		cmd = "lsusb"
		returncode = returned_value = subprocess.check_output(cmd,shell=True).decode("utf-8")
		codelist = returncode.split()
		usblist = []
		for i in codelist:
			if len(i) > 7:
				if i.split()[6] == "Arduino":
					print(i)
		cmd = "ls /dev/tty*"
		returncode = returned_value = subprocess.check_output(cmd,shell=True).decode("utf-8")
		codelist = returncode.split()
		devlist = dict()
		for i in codelist:
			if i.find("ttyS") != -1:
				devlist[i] = []
				print(i)
				ser = serial.Serial(i, 9600, timeout=2)
				if ser.read() == b"":
					print(f"---------{i} is not opened")
			elif i.find("ttyACM") != -1:
				print(i)
			elif i.find("ttyAMA") != -1:
				print(i)
		
	def __del__(self):
		self.thread_terminate = True
		self.thread_sensor.join()
	def sensorLoop(self):
		value = 0
		num_sensor = chr(1)
		while self.thread_terminate == False:
			
	
			value += 1;
			sensorMsg = SENSOR
			sensorMsg += bytes(num_sensor, 'ascii')
			sensorMsg += bytes('i', 'ascii')
			sensorMsg+=bytes(chr(1),'ascii')
			sensorMsg+=bytes(chr(1),'ascii')
			sensorMsg+=value.to_bytes(4, 'big')
			sensorMsg += bytes('i', 'ascii')
			sensorMsg+=bytes(chr(1),'ascii')
			sensorMsg+=bytes(chr(0),'ascii')
			sensorMsg+=int(value/2).to_bytes(4, 'big')
			
			if self.thread_terminate is True:
				break
			if self._on_message != None:
				try:
					on_message = self.on_message
					on_message(sensorMsg)
					time.sleep(1)
				except:
					print(f"Sensor failed")	
	def call(self, Msg):
		if self._on_message != None:
			on_message = self.on_message
			
			for sensor in self._sensorList:
				Msg = str(sensor[0])+" : "+sensor[1]
				on_message(Msg)
				
		else:
			print("not called")
	def setSensor(self, slist):
		self._sensorList = slist
		for sensor in self._sensorList:
			print(f'setsensor: sensor:{sensor[0]}, {sensor[1]}')
	@property
	def sensorList(self):
		return self.sensorList
	@sensorList.setter
	def sensorList(self, slist):
		self._sensorList = slist
	@property
	def on_message(self):
		return self._on_message
	@on_message.setter
	def on_message(self, func):
		self._on_message = func
