import GPlayer
import SensorManager

gplayer = GPlayer.GPlayer()
sm = SensorManager.SensorManager()
gplayer.on_setsensor = sm.setSensor
sm.on_message = gplayer.sendMsg
sm.call("hello")
