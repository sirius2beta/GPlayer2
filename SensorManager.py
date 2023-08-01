
class SensorManager:
	def __init__(self):
		self.name = 'sensor'
		self._on_message = None
		self._sensorList = [[1,'i']]
	def call(self, Msg):
		if self._on_message != None:
			on_message = self.on_message
			
			for sensor in self._sensorList:
				Msg = str(sensor[0])+" : "+sensor[1]
				on_message(Msg)
				
		else:
			print("not called")
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
