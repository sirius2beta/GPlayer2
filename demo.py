import GPlayer
import Sensor

gplayer = GPlayer.GPlayer()
sensorMaster = Sensor.Sensor()
sensorMaster.setCallBack(gplayer.test)
sensorMaster.sendMsg("hello")
