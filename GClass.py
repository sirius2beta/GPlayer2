import serial

HEARTBEAT = b'\x10'
FORMAT = b'\x20'
COMMAND = b'\x30'
QUIT = b'\x40'
SENSOR = b'\x50'

class Peripheral:
	def __init__(self, idProduct = "", idVendor="", manufacturer="", dev="", ID = 0):
		self.idProduct = idProduct
		self.idVendor = idVendor
		# 未來加入bcdDevice 作為識別
		self.manufacturer = manufacturer
		self.dev = dev
		self.ID = ID
		self.IO = None
		
	def getList(self):
		return [self.idProduct, self.idVendor, self.manufacturer, self.dev, self.ID]
	def connect(self):
		if self.manufacturer == "Arduino LLC":
			print("    -connected to arduino...")
			self.IO = serial.Serial(self.dev,9600)

	def read(self):
		if self.IO != None:
			return self.IO.readline()
		else:
			return 0

	def __del__(self):
		if self.IO != None:
			self.IO.close()

	

class Device:
	ID = ""
	#deviceName = ""
	type = ""
	settings = ""
	pinIDList = []

