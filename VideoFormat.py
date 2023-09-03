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