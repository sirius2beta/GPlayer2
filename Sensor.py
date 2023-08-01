
class SensorManager:
	def __init__(self):
		self.name = 'sensor'
		self._on_message = None
	def call(self, Msg):
		if self._on_message != None:
			
			on_message(Msg)
		else:
			print("not called")
	@property
	def on_message(self):
		return self._on_message
	@on_message.setter
	def on_message(self, func):
		self._on_message = func
