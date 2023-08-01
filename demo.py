import GPlayer
import SensorManager

gplayer = GPlayer.GPlayer()
sm = SensorManager.SensorManager()
sm.on_message = gplayer.sendMsg
sm.call("hello")
