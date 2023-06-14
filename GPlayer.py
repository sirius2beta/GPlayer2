import gi
import os
import subprocess
import time
import threading
import socket
import struct

HEARTBEAT = '\x10'
FORMAT = '\x20'
COMMAND = '\x30'

gi.require_version("Gst", "1.0")
from gi.repository import Gst, GLib, GObject
# update
class GPlayer:
	def __init__(self):
		self.BOAT_NAME = 'usv1'
		self.GROUND_NAME = 'ground1'

		self.PC_IP='10.10.10.205'
		self.SERVER_IP = ''
		self.P_CLIENT_IP = '127.0.0.1' #PC IP
		self.S_CLIENT_IP = '127.0.0.1'
		self.OUT_PORT = 50008
		self.IN_PORT = 50007 

		self.pipelinesexist = []
		self.pipelines = []
		self.pipelines_state = []
		self.camera_format = []
		self.get_video_format()
		
		self._on_msg = None
		
		GObject.threads_init()
		Gst.init(None)

		self.createPipelines()
		


		self.server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		self.client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		self.server.bind((self.SERVER_IP, self.IN_PORT))
		self.server.setblocking(0)

		print(f'server started at {self.IN_PORT}')
		print(f'send message to {self.P_CLIENT_IP}, Port: {self.IN_PORT}')
		
		self.thread_terminate = False
		self.lock = threading.Lock()

		self.thread_cli = threading.Thread(target=self.aliveLoop)
		self.thread_ser = threading.Thread(target=self.listenLoop)

		self.thread_cli.start()
		self.thread_ser.start()
		
	def __del__(self):
		self.thread_terminate = True
		self.thread_cli.join()
		self.thread_ser.join()

	def sendMsg(self, msg):
		# Send primary heartbeat every 0.5s
			try:
				self.client.sendto(msg.encode(),(self.P_CLIENT_IP,self.OUT_PORT))
				
				print(f"Primary send to: {self.P_CLIENT_IP}:{self.OUT_PORT}")
			except:
				print(f"Primary unreached: {self.P_CLIENT_IP}:{self.OUT_PORT}")
			# Send secondary heartbeat every 0.5s
			try:
				self.client.sendto(msg.encode(),(self.S_CLIENT_IP, self.OUT_PORT))
				print(f"Secondarysend to: {self.S_CLIENT_IP}:{self.OUT_PORT}")
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
				print(f"Primary send to: {self.P_CLIENT_IP}:{self.OUT_PORT}")
			except:
				print(f"Primary unreached: {self.P_CLIENT_IP}:{self.OUT_PORT}")
			# Send secondary heartbeat every 0.5s
			try:
				self.client.sendto(beat,(self.S_CLIENT_IP, self.OUT_PORT))
				time.sleep(0.5)
				print(f"Secondarysend to: {self.S_CLIENT_IP}:{self.OUT_PORT}")
			except:
				print(f"Secondary unreached: {self.S_CLIENT_IP}:{self.OUT_PORT}")
			

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
			
			indata = indata.decode()
			header = indata[0]
			indata = indata[1:]
			if header == HEARTBEAT:
				print("HB")
				self.BOAT_NAME = indata.split()[1]
				primary = indata.split()[2]
				if primary == 'P':
					self.P_CLIENT_IP = indata.split()[0]
				else:
					self.S_CLIENT_IP = indata.split()[0]

			elif header == FORMAT:
				print("format")
				msg = 'format '+self.BOAT_NAME+'\n'+'\n'.join(self.camera_format)

				self.client.sendto(msg.encode(),(self.P_CLIENT_IP,self.OUT_PORT))
				self.client.sendto(msg.encode(),(self.S_CLIENT_IP,self.OUT_PORT))
			elif header == COMMAND:
				print("cmd")
				print(indata)
				cformat = indata.split()[1:6]

				print(cformat)
				encoder, mid, quality, ip, port = indata.split()[6:]
				print(quality, ip, port)

				if(' '.join(cformat) not in self.camera_format):
					print('format error')
				else:
					gstring = 'v4l2src device=/dev/'+cformat[0]
					if cformat[1] == 'YUYV':
						cformat[1] = 'YUY2'
						gstring += ' num-buffers=-1 ! video/x-raw,format={},width={},height={},framerate={}/1 ! '.format(cformat[1],cformat[2].split('=')[1],cformat[3].split('=')[1],cformat[4].split('=')[1])
						if mid != 'nan':
							gstring += (mid+' ! ')
						if encoder == 'h264':
							gstring +=' videoconvert ! omxh264enc ! rtph264pay pt=96 config-interval=1 ! udpsink host={} port={}'.format(ip, port)	
						else:
							gstring +='jpegenc quality=30 ! rtpjpegpay ! udpsink host={} port={}'.format(ip, port)
					elif cformat[1] == 'MJPG':
						gstring += ' num-buffers=-1 ! image/jpeg,width={},height={},framerate={}/1 ! '.format(cformat[2].split('=')[1],cformat[3].split('=')[1],cformat[4].split('=')[1])
						if mid != 'nan':
							gstring += (mid+' ! ')
						if encoder == 'h264':
							gstring +=' jpegparse ! jpegdec ! videoconvert ! omxh264enc ! rtph264pay pt=96 config-interval=1 ! udpsink host={} port={}'.format(ip, port)	
						else:
							gstring +='jpegparse ! jpegdec ! jpegenc quality=30 ! rtpjpegpay ! udpsink host={} port={}'.format(ip, port)

					elif cformat[1] == 'GREY':
						gstring += ' num-buffers=-1 ! video/x-raw,format=GRAY8 ! videoscale ! videoconvert ! video/x-raw, format=YUY2, width=640,height=480 ! '
						if mid != 'nan':
							gstring += (mid+' ! ')
						if encoder == 'h264':
							gstring +='videoconvert ! omxh264enc ! rtph264pay pt=96 config-interval=1 ! udpsink host={} port={}'.format(ip, port)

						else:
							gstring +='jpegenc quality=30 ! rtpjpegpay ! udpsink host={} port={}'.format(ip, port)
					else:
						if cformat[1] == 'RGBP':
							cformat[1] = 'RGB16'
						elif cformat[1] == 'BGR8':
							cformat[1] = 'BGR'
						elif cformat[1] == 'Y1':
							cformat[1] = 'UYVY'
						gstring += ' num-buffers=-1 ! video/x-raw,format={}! videoscale ! videoconvert ! video/x-raw, format=YUY2, width=640,height=480 ! '.format(cformat[1])
						if mid != 'nan':
							gstring += (mid+' ! ')
						if encoder == 'h264':
							gstring +='videoconvert ! omxh264enc ! rtph264pay pt=96 config-interval=1 ! udpsink host={} port={}'.format(ip, port)

						else:
							gstring +='jpegenc quality=30 ! rtpjpegpay ! udpsink host={} port={}'.format(ip, port)


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
			elif header == 'quit':
				video = int(indata.split()[1][5:])
				if video in self.pipelinesexist:
					videoindex = self.pipelinesexist.index(video)
					self.pipelines[videoindex].set_state(Gst.State.NULL)
					self.pipelines_state[videoindex] = False
					print("quit : video"+str(video))
			elif self.on_msg:
				try:
					#on_msg(header, message)
					indata = indata.split()
					indata.pop(0)
					indata = " ".join(indata)
					self.on_msg(header, indata)
					print('on msg')
				except Exception as err:
					print(f'error on_msg callback function: {err}')


	@property
	def on_msg(self):
		return self._on_msg
	
	@on_msg.setter
	def on_msg(self, func):
		self._on_msg = func
	
	def on_msg_callback(self):
		def decorator(func):
			self.on_msg = func
			return func
		return decorator
			

# The callback for when a PUBLISH message is received from the server.





