import gi
import os
import subprocess
import time
import threading
import socket
import struct

HEARTBEAT = b'\x10'
FORMAT = b'\x20'
COMMAND = b'\x30'
QUIT = b'\x40'
SENSOR = b'\x50'

gi.require_version("Gst", "1.0")
from gi.repository import Gst, GLib, GObject
# update
def getFormatCMD(sys, cam, format, width, height, framerate, encoder, IP, port):
		gstring = 'v4l2src device=/dev/'+cam
		mid = 'nan'
		if format == 'YUYV':
			format = 'YUY2'
			gstring += ' num-buffers=-1 ! video/x-raw,format={},width={},height={},framerate={}/1 ! '.format(format, width, height, framerate)
			if mid != 'nan':
				gstring += (mid+' ! ')
			if encoder == 'h264':
				if sys == 'buster':
					gstring +=' videoconvert ! omxh264enc ! rtph264pay pt=96 config-interval=1 ! udpsink host={} port={}'.format(IP, port)
				else:
					gstring +='nvvideoconvert ! nvv4l2h264enc ! rtph264pay pt=96 config-interval=1 ! udpsink host={} port={}'.format(IP, port)	
			else:
				gstring +='jpegenc quality=30 ! rtpjpegpay ! udpsink host={} port={}'.format(IP, port)
		elif format == 'MJPG':
			gstring += ' num-buffers=-1 ! image/jpeg,width={},height={},framerate={}/1 ! '.format(width, height, framerate)
			if mid != 'nan':
				gstring += (mid+' ! ')
			if encoder == 'h264':
				if sys == 'buster':
					gstring +=' jpegparse ! jpegdec ! videoconvert ! omxh264enc ! rtph264pay pt=96 config-interval=1 ! udpsink host={} port={}'.format(IP, port)
				else:
					gstring +='jpegparse ! jpegdec ! videoconvert ! videoconvert   ! nvvideoconvert ! nvv4l2h264enc ! rtph264pay pt=96 config-interval=1 ! udpsink host={} port={}'.format(IP, port)	
			else:
				gstring +='jpegparse ! jpegdec ! jpegenc quality=30 ! rtpjpegpay ! udpsink host={} port={}'.format(IP, port)

		elif format == 'GREY':
			gstring += ' num-buffers=-1 ! video/x-raw,format=GRAY8 ! videoscale ! videoconvert ! video/x-raw, format=YUY2, width=640,height=480 ! '
			if mid != 'nan':
				gstring += (mid+' ! ')
			if encoder == 'h264':
				if sys == 'buster':
					gstring +='videoconvert ! omxh264enc ! rtph264pay pt=96 config-interval=1 ! udpsink host={} port={}'.format(IP, port)
				else:
					gstring +='videoconvert !  nvvideoconvert ! nvv4l2h264enc ! rtph264pay pt=96 config-interval=1 ! udpsink host={} port={}'.format(IP, port)

			else:
				gstring +='jpegenc quality=30 ! rtpjpegpay ! udpsink host={} port={}'.format(IP, port)
		else:
			if format == 'RGBP':
				format = 'RGB16'
			elif format == 'BGR8':
				format = 'BGR'
			elif format == 'Y1':
				format = 'UYVY'
			gstring += ' num-buffers=-1 ! video/x-raw,format={}! videoscale ! videoconvert ! video/x-raw, format=YUY2, width=640,height=480 ! '.format(format)
			if mid != 'nan':
				gstring += (mid+' ! ')
			if encoder == 'h264':
				gstring +='videoconvert ! omxh264enc ! rtph264pay pt=96 config-interval=1 ! udpsink host={} port={}'.format(IP, port)

			else:
				gstring +='jpegenc quality=30 ! rtpjpegpay ! udpsink host={} port={}'.format(IP, port)
		return gstring


class GPlayer:
	def __init__(self):
		self.BOAT_ID = 0
		self.GROUND_NAME = 'ground1'

		self.PC_IP='10.10.10.205'
		self.SERVER_IP = ''
		self.P_CLIENT_IP = '127.0.0.1' #PC IP
		self.S_CLIENT_IP = '127.0.0.1'
		self.OUT_PORT = 50008
		self.IN_PORT = 50007 
		self.newConnection = True

		self.pipelinesexist = []
		self.pipelines = []
		self.pipelines_state = []
		self.camera_format = []
		self.get_video_format()
		
		self._on_setsensor = None
		self._get_dev_info = None
		
		GObject.threads_init()
		Gst.init(None)

		self.createPipelines()
		


		self.server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		self.client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		self.server.bind((self.SERVER_IP, self.IN_PORT))
		self.server.setblocking(0)
		
		self.thread_terminate = False
		self.lock = threading.Lock()
		
		
		
	def __del__(self):
		self.thread_terminate = True
		self.thread_cli.join()
		self.thread_ser.join()
	def startLoop(self):
		self.thread_cli = threading.Thread(target=self.aliveLoop)
		self.thread_ser = threading.Thread(target=self.listenLoop)

		self.thread_cli.start()
		self.thread_ser.start()
	def test(self, msg):
		print(f"called outside: {msg}")
	def sendMsg(self, topic, msg):
		# Send primary heartbeat every 0.5s
		#print(f"msg: {msg}")
		msg = topic + self.BOAT_ID.to_bytes(4, 'big') + msg
		try:
			self.client.sendto(msg,(self.P_CLIENT_IP,self.OUT_PORT))

		except:
			print(f"Primary unreached: {self.P_CLIENT_IP}:{self.OUT_PORT}")
		# Send secondary heartbeat every 0.5s
		try:
			self.client.sendto(msg,(self.S_CLIENT_IP, self.OUT_PORT))
		except:
			print(f"Secondary unreached: {self.S_CLIENT_IP}:{self.OUT_PORT}")
	
	def aliveLoop(self):
		print('client started...')
		run = True
		checkAlive = False
		while run:
			if self.thread_terminate is True:
				break
			#beat = b'\x10' + self.BOAT_NAME.encode()
			beat = b'\x10'
			# Send primary heartbeat every 0.5s
			try:
				self.client.sendto(beat,(self.P_CLIENT_IP,self.OUT_PORT))
				time.sleep(0.5)
				if self.newConnection:
					print(f"Primary send to: {self.P_CLIENT_IP}:{self.OUT_PORT}")
			except:
				if self.newConnection:
					print(f"Primary unreached: {self.P_CLIENT_IP}:{self.OUT_PORT}")
			# Send secondary heartbeat every 0.5s
			try:
				self.client.sendto(beat,(self.S_CLIENT_IP, self.OUT_PORT))
				time.sleep(0.5)
				if self.newConnection:
					print(f"Secondarysend to: {self.S_CLIENT_IP}:{self.OUT_PORT}")
			except:
				if self.newConnection:
					print(f"Secondary unreached: {self.S_CLIENT_IP}:{self.OUT_PORT}")
			self.newConnection = False

	def createPipelines(self):
		for i in self.camera_format:
			j = int(i.split()[0][5]);
			if(j not in self.pipelinesexist):
				pipeline = Gst.Pipeline()
				self.pipelines.append(pipeline)
				self.pipelinesexist.append(j)
		for i in self.pipelines:
			self.pipelines_state.append(False)
		print(self.pipelinesexist)
	

#get video format from existing camera devices
	def get_video_format(self):
		try:
			cmd = " grep '^VERSION_CODENAME=' /etc/os-release"
			returned_value = subprocess.check_output(cmd,shell=True).replace(b'\t',b'').decode("utf-8") 
		except:
			returned_value = '0'
		sys = returned_value.split('=')[1]
		if sys == 'buster':
			print('system: buster')
		else:
			print(f'system: {sys}')
		#Check camera device
		for i in range(0,10):
				try:
					cmd = "v4l2-ctl -d /dev/video{} --list-formats-ext".format(i)
					returned_value = subprocess.check_output(cmd,shell=True).replace(b'\t',b'').decode("utf-8")  # returns the exit code in unix
				except:
					continue
				line_list = returned_value.splitlines()
				new_line_list = list()
				for j in line_list:
					if len(j.split()) == 0:
						continue
					elif j.split()[0][0] =='[':
						form = j.split()[1][1:-1]
					elif j.split()[0] =='Size:':
						size = j.split()[2]
						width, height = size.split('x')
					elif j.split()[0] == 'Interval:':
						self.camera_format.append('video{} {} width={} height={} framerate={}'.format(i,form, width, height , j.split()[3][1:].split('.')[0]))
						print('video{} {} width={} height={} framerate={}'.format(i,form, width, height , j.split()[3][1:].split('.')[0]))
	
	def get_video_format_for_diffNx(self):	
		#Check camera device
		for i in range(0,10):
				try:
					cmd = "v4l2-ctl -d /dev/video{} --list-formats-ext".format(i)
					returned_value = subprocess.check_output(cmd,shell=True).replace(b'\t',b'').decode("utf-8")  # returns the exit code in unix
				except:
					continue
				line_list = returned_value.splitlines()
				new_line_list = list()
				for j in line_list:
					if len(j.split()) == 0:
						continue
					elif j.split()[0] =='Pixel':
						form = j.split()[2][1:-1]
					elif j.split()[0] =='Size:':
						size = j.split()[2]
						width, height = size.split('x')
					elif j.split()[0] == 'Interval:':
						self.camera_format.append('video{} {} width={} height={} framerate={}'.format(i,form, width, height , j.split()[3][1:].split('.')[0]))
						print('video{} {} width={} height={} framerate={}'.format(i,form, width, height , j.split()[3][1:].split('.')[0]))
	

	
	def listenLoop(self):
		print('server started...')
		run = True
		while run:
			if self.thread_terminate is True:
				break
			try:
				indata, addr = self.server.recvfrom(1024)
				
			except:
				continue

			print(f'message from: {str(addr)}, data: {indata}')
			
			indata = indata
			header = indata[0]

			if header == HEARTBEAT[0]:
				indata = indata[1:]
				ip = f"{indata[3]}.{indata[2]}.{indata[1]}.{indata[0]}"
				self.BOAT_ID = indata[4]
				primary = indata[5:].decode()
				#print(f"id:{id}, primary:{primary}")
				if primary == 'P':
					self.P_CLIENT_IP = indata.split()[0]
					self.P_CLIENT_IP = ip
				else:
					self.S_CLIENT_IP = indata.split()[0]
					self.S_CLIENT_IP = ip
				self.newConnection = True
				if self.get_dev_info != None:
					get_dev_info = self.get_dev_info
					get_dev_info()
				else:
					print("get dev info failed")

			elif header == FORMAT[0]:
				indata = indata[1:].decode()
				print("FORMAT---")
				msg = chr(self.BOAT_ID)+"\n".join(self.camera_format)
				msg = FORMAT + msg.encode()

				self.client.sendto(msg,(self.P_CLIENT_IP,self.OUT_PORT))
				self.client.sendto(msg,(self.S_CLIENT_IP,self.OUT_PORT))
			elif header == COMMAND[0]:
				indata = indata[1:].decode()
				print("COMMAND---")
				print(indata)
				cformat = indata.split()[:5]

				print(cformat)
				encoder, mid, quality, ip, port = indata.split()[5:]
				#print(quality, ip, port)

				if(' '.join(cformat) not in self.camera_format):
					print('format error')
				else:
					gstring = getFormatCMD('buster', cformat[0], cformat[1], cformat[2].split('=')[1], cformat[3].split('=')[1],cformat[4].split('=')[1], encoder, ip, port)
					print(gstring)
					print(cformat[1])
					print(cformat[1][5:])
					videoindex = self.pipelinesexist.index(int(cformat[0][5:]))


					if self.pipelines_state[videoindex] == True:
						self.pipelines[videoindex].set_state(Gst.State.NULL)
						self.pipelines[videoindex] = Gst.parse_launch(gstring)
						self.pipelines[videoindex].set_state(Gst.State.PLAYING)

					else:
						self.pipelines[videoindex] = Gst.parse_launch(gstring)
						self.pipelines[videoindex].set_state(Gst.State.PLAYING)
						self.pipelines_state[videoindex] = True
			elif header == SENSOR[0]:
				print("SENSOR---")
				sensorList = [[1,'i']]
				if self.on_setsensor != None:
					on_setsensor = self.on_setsensor
					on_setsensor(sensorList)
				else:
					print("no setsensor callback")
			elif header == QUIT[0]:
				print("QUIT---")
				indata = indata[1:].decode()
				#video = int(indata.split()[1][5:])
				#if video in self.pipelinesexist:
				#	videoindex = self.pipelinesexist.index(video)
				#	self.pipelines[videoindex].set_state(Gst.State.NULL)
				#	self.pipelines_state[videoindex] = False
				#	print("quit : video"+str(video))

	@property
	def on_setsensor(self):
		return self._on_setsensor
	
	@on_setsensor.setter
	def on_setsensor(self, func):
		self._on_setsensor = func

	@property
	def get_dev_info(self):
		return self._get_dev_info

	@get_dev_info.setter
	def get_dev_info(self, func):
		self._get_dev_info = func
	
	#def on_msg_callback(self):
	#	def decorator(func):
	#		self._on_setsensor = func
	#		return func
	#	return decorator
			

# The callback for when a PUBLISH message is received from the server.
