
class Sensor:
	def __init__(self):
		self.name = 'sensor'
		self.__callback = 0
	def call(self, Msg):
		if _callback != 0:
			print("called")
