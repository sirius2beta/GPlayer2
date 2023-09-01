class Peripheral:
	def __init__(self, idProduct = "", idVendor="", manufacturer="", index="", ID = 0):
		self.idProduct = idProduct
		self.idVendor = idVendor
		self.manufacturer = manufacturer
		self.index = index
		self.ID = ID
	
	
	

class Device:
	ID = ""
	#deviceName = ""
	type = ""
	settings = ""
	pinIDList = []
