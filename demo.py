import GPlayer
import DeviceManager

gplayer = GPlayer.GPlayer()
sm = DeviceManager.DeviceManager()
gplayer.on_setDevice = sm.setDevice
gplayer.get_dev_info = sm.on_dev_info
sm.on_message = gplayer.sendMsg
gplayer.startLoop()


