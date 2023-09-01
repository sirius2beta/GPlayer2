class Peripheral:
	def __init__(self, idProduct = "", idVendor="", manufacturer="", dev="", ID = 0):
		self.idProduct = idProduct
		self.idVendor = idVendor
		# 未來加入bcdDevice 作為識別
		self.manufacturer = manufacturer
		self.dev = dev
		self.ID = ID
	def getList(self):
		return [self.idProduct, self.idVendor, self.manufacturer, self.dev, self.ID]
	
	
	

class Device:
	ID = ""
	#deviceName = ""
	type = ""
	settings = ""
	pinIDList = []
