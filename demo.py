import GPlayer
import SensorManager

gplayer = GPlayer.GPlayer()
sm = SensorManager.Sensor()
sm.on_message = gplayer.sendMsg
sm.call("hello")
