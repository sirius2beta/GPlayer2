import subprocess
def get_video_format():	
		#Check camera device
		camera_format = list()
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
						camera_format.append('video{} {} width={} height={} framerate={}'.format(i,form, width, height , j.split()[3][1:].split('.')[0]))
						print('video{} {} width={} height={} framerate={}'.format(i,form, width, height , j.split()[3][1:].split('.')[0]))
		return camera_format
  
get_video_format()
