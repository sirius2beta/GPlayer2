import time
import cv2

video_pipeline = f'v4l2src device=/dev/video0 ! image/jpeg, width=1920, height=1080, framerate=30/1! jpegparse ! jpegdec ! videoconvert ! appsink'
cap_send = cv2.VideoCapture(video_pipeline, cv2.CAP_GSTREAMER)
w = int(cap_send.get(cv2.CAP_PROP_FRAME_WIDTH))
h = int(cap_send.get(cv2.CAP_PROP_FRAME_HEIGHT))
fps = cap_send.get(cv2.CAP_PROP_FPS)
out_send = cv2.VideoWriter('appsrc ! videoconvert ! video/x-raw,format=I420 ! nvvideoconvert ! video/x-raw(memory:NVMM) ! nvv4l2h264enc ! rtph264pay pt=96 config-interval=1 ! udpsink host=100.73.190.7 port=5201'\
         ,cv2.CAP_GSTREAMER\
         ,0\
         , fps\
         , (w, h)\
         , True)
fourcc = cv2.VideoWriter_fourcc(*'mp4v')
save_video = cv2.VideoWriter('../output.mp4', fourcc, 15, (int(w), int(h)))
if not cap_send.isOpened() or not out_send.isOpened():
  print('VideoCapture or VideoWriter not opened')
  
  exit(0)
print('Src opened, %dx%d @ %d fps' % (w, h, fps))

def draw(img):
  
  dot1 = (int(w/2-20),int(h/2))
  dot2 = (int(w/2-5),int(h/2))
  dot3 = (int(w/2+5),int(h/2))
  dot4 = (int(w/2+20),int(h/2))
  dot5 = (int(w/2),int(h/2+10))
  dot6 = (int(w/2),int(h/2+20))
  dot7 = (int(w/2),int(h/2-10))
  dot8 = (int(w/2),int(h/2-20))
  color = (255,255,255)
  ine = cv2.line(img, dot1, dot2, color, 2)
  cv2.line(img, dot3, dot4, color, 2)
  cv2.line(img, dot5, dot6, color, 2)
  cv2.line(img, dot7, dot8, color, 2)


while True:
  ret,frame = cap_send.read()
  if not ret:
    print('empty frame')
    break
  if out_send.isOpened():
    draw(frame)
    out_send.write(frame)
    save_video.write(frame)


save_video.release()

