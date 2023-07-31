import GPlayer
import Sensor

gplayer = GPlayer.GPlayer()
sensorMaster = Sensor.Sensor()
sensorMaster.__callback = gplayer.sendMsg
sensorMaster.sendMsg()
