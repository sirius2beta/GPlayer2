
class Sensor:
	def __init__(self):
		self.name = 'sensor'
		self.__callback = 0
	def sendMsg(self, Msg):
		if self.__callback != 0:
			print("called")
		else:
			self.__callback(Msg)
