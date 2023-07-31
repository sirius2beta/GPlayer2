
class Sensor:
	def __init__(self):
		self.name = 'sensor'
		self.__callback = self.callback
	def sendMsg(self, Msg):
		if self.__callback != 0:
			print("called")
		else:
			self.__callback(Msg)
	def callback():
		self.a = 1
