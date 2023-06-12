import cv2






f = 3 # 3 mm
LCD_w = 5.27 
LCD_h = 3.96 #LCD 5.27mm x 3.96mm
camera_height = 3


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
if not cap_send.isOpened() or not out_send.isOpened():
  print('VideoCapture or VideoWriter not opened')
  
  exit(0)
print('Src opened, %dx%d @ %d fps' % (w, h, fps))

from ultralytics import YOLO
from ultralytics.yolo.utils.plotting import Annotator
model = YOLO('../models/yolov8n.pt')


if not cap_send.isOpened() or not out_send.isOpened():
  print('VideoCapture or VideoWriter not opened')
  
  exit(0)
print('Src opened, %dx%d @ %d fps' % (w, h, fps))

while True:
    ret, frame = cap_send.read()
    if ret:
        img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = model.predict(img, conf=0.5, classes=0)
        annotator = Annotator(img)

        for r in results:
            for box in r.boxes:
                b = box.xyxy[0]
                c = box.cls
                annotator.box_label(b, f"{r.names[int(c)]} {float(box.conf):.2}")

        img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
        
        if not ret:
            print('empty frame')
            break
        if out_send.isOpened():
            out_send.write(frame)
        else:
            break
cap_send.release()
out_send.release()

