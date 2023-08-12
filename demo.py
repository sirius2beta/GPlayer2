import GPlayer
import SensorManager

gplayer = GPlayer.GPlayer()
sm = SensorManager.SensorManager()
gplayer.on_setsensor = sm.setSensor
gplayer.get_dev_info = sm.on_dev_info
sm.on_message = gplayer.sendMsg
gplayer.startLoop()


