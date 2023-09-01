class Peripheral:
	def __init__(self, idProduct = "", idVendor="", manufacturer="", dev="", ID = 0):
		self.idProduct = idProduct
		self.idVendor = idVendor
		# 未來加入bcdDevice 作為識別
		self.manufacturer = manufacturer
		self.dev = dev
		self.ID = ID
	
	
	

class Device:
	ID = ""
	#deviceName = ""
	type = ""
	settings = ""
	pinIDList = []
