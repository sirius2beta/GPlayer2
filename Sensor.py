
class Sensor:
	def __init__(self):
		self.name = 'sensor'
		self.__callback = 0
	def sendMsg(self, Msg):
		if __callback != 0:
			print("called")
