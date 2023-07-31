import GPlayer
import Sensor

gplayer = GPlayer.GPlayer()
sensorMaster = Sensor.Sensor()
sensorMaster.setCallBack(gplayer.sendMsg)
sensorMaster.sendMsg("hello")
