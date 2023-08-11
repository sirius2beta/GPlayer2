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
		
		# get all tty* device (ACM, USB..)
		cmd = "ls /dev/tty*"
		returncode = subprocess.check_output(cmd,shell=True).decode("utf-8")
		codelist = returncode.split()
		devlist = []
		for i in codelist:
			
			#if i.find("ttyS") != -1:
			#	devlist.append(i)
			#	print(i)
			if i.find("ttyACM") != -1:
				devlist.append(i)
			elif i.find("ttyUSB") != -1:
				devlist.append(i)
			elif i.find("ttyAMA") != -1:
				devlist.append(i)
		# find device detail
		current_dev_list = []
		idProduct = ''
		for i in devlist:
			cmd = f"udevadm info -a -p  $(udevadm info -q path -n {i})"
			returncode = subprocess.check_output(cmd,shell=True).decode("utf-8")
			dlist = returncode.split('\n')
			count = 0
			for j in dlist:
				word = j.split("==")
				#print(f"------: {word[0]}")
				if word[0].find("KERNELS") != -1: # not used
					kernals = word[1]
				elif word[0].find("idProduct") != -1:
					idProduct = word[1]
					count += 1
				elif word[0].find("idVendor") != -1:
					idVendor = word[1]
					count += 1
				elif word[0].find("manufacturer") != -1:
					manufacturer = word[1][1:-1].split()[0] # only take first word for identification
					count += 1
				if count == 3:
					current_dev_list.append([idProduct, idVendor, manufacturer, i])
					break

		udev_file = open('/etc/udev/rules.d/79-sir.rules','r+')
		lines = udev_file.readlines()
		registered_dev_list = []
		
		# generate exist dev list
		num_exist = []
		for line in lines:
			wa = line.split(', ')
			for wb in wa:
				wc = wb.split("=")
				if wc[0] == "KERNELS": # Not used
					kernals = wc[2]
				elif wc[0] == "ATTRS{idProduct}":
					idProduct = wc[2]
				elif wc[0] == "ATTRS{idVendor}":
					idVendor = wc[2]
				elif wc[0] == "SYMLINK+":
					SYMLINK = wc[1][1:-1]
					num = int(SYMLINK[2,-1])
					print(f"num: {num}")
					num_exist.append(num)
					registered_dev_list.append([idProduct, idVendor, SYMLINK])
			
		print(f"Registered device:")
		for i in registered_dev_list:
			print(f"K:{i[0]}, P:{i[1]}, V:{i[2]}, M:{i[3]}")
		
					
		
		# compare exist and added device
		for i in current_dev_list:
			for j in registered_dev_list:
				if (i[1] == j[1]) and (i[2] == j[2]):
					i[4] = "/dev/"+j[3][1:-1]
					print("device exist")
				else:
					n = 0
					while True:
						if n in num_exist:
							n+=1
						else:
							break
					udev_file.write(f"ATTRS{{idProduct}}=={i[1]}, ATTRS{{idVendor}}=={i[2]}, SYMLINK+=\"PD{n}\", MODE=\"0777\"")
		udev_file.close()
		print(f"Current device:")
		for i in current_dev_list:
			print(f"K:{i[0]}, P:{i[1]}, V:{i[2]}, M:{i[3]}, D:{i[4]}")
					
		
		
		
		
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
