
class Sensor:
	def __init__(self):
		self.name = 'sensor'
		self.__callback = self.callback
	def sendMsg(self, Msg):
		if self.__callback != 0:
			
			self.__callback(Msg)
		else:
			print("called")
	def callback():
		self.a = 1
