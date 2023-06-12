import os
import cv2
import warnings
from collections import namedtuple
from pathlib import Path
from typing import List, Optional, Tuple, Union

import numpy as np
import pycuda.autoinit  # noqa F401
import pycuda.driver as cuda
import tensorrt as trt
from numpy import ndarray
import threading

os.environ['CUDA_MODULE_LOADING'] = 'LAZY'
warnings.filterwarnings(action='ignore', category=DeprecationWarning)
class TRTEngine:

    def __init__(self, weight: Union[str, Path]) -> None:
        self.weight = Path(weight) if isinstance(weight, str) else weight
        self.stream = cuda.Stream(0)
        self.__init_engine()
        self.__init_bindings()
        self.__warm_up()
    def __init_engine(self) -> None:
        logger = trt.Logger(trt.Logger.WARNING)
        trt.init_libnvinfer_plugins(logger, namespace='')
        with trt.Runtime(logger) as runtime:
            model = runtime.deserialize_cuda_engine(self.weight.read_bytes())

        context = model.create_execution_context()

        names = [model.get_binding_name(i) for i in range(model.num_bindings)]
        self.num_bindings = model.num_bindings
        self.bindings: List[int] = [0] * self.num_bindings
        num_inputs, num_outputs = 0, 0

        for i in range(model.num_bindings):
            if model.binding_is_input(i):
                num_inputs += 1
            else:
                num_outputs += 1

        self.num_inputs = num_inputs
        self.num_outputs = num_outputs
        self.model = model
        self.context = context
        self.input_names = names[:num_inputs]
        self.output_names = names[num_inputs:]

    def __init_bindings(self) -> None:
        dynamic = False
        Tensor = namedtuple('Tensor', ('name', 'dtype', 'shape', 'cpu', 'gpu'))
        inp_info = []
        out_info = []
        out_ptrs = []
        for i, name in enumerate(self.input_names):
            assert self.model.get_binding_name(i) == name
            dtype = trt.nptype(self.model.get_binding_dtype(i))
            shape = tuple(self.model.get_binding_shape(i))
            if -1 in shape:
                dynamic |= True
            if not dynamic:
                cpu = np.empty(shape, dtype)
                gpu = cuda.mem_alloc(cpu.nbytes)
                cuda.memcpy_htod_async(gpu, cpu, self.stream)
            else:
                cpu, gpu = np.empty(0), 0
            inp_info.append(Tensor(name, dtype, shape, cpu, gpu))
        for i, name in enumerate(self.output_names):
            i += self.num_inputs
            assert self.model.get_binding_name(i) == name
            dtype = trt.nptype(self.model.get_binding_dtype(i))
            shape = tuple(self.model.get_binding_shape(i))
            if not dynamic:
                cpu = np.empty(shape, dtype=dtype)
                gpu = cuda.mem_alloc(cpu.nbytes)
                cuda.memcpy_htod_async(gpu, cpu, self.stream)
                out_ptrs.append(gpu)
            else:
                cpu, gpu = np.empty(0), 0
            out_info.append(Tensor(name, dtype, shape, cpu, gpu))

        self.is_dynamic = dynamic
        self.inp_info = inp_info
        self.out_info = out_info
        self.out_ptrs = out_ptrs

    def __warm_up(self) -> None:
        if self.is_dynamic:
            print('You engine has dynamic axes, please warm up by yourself !')
            return
        for _ in range(10):
            inputs = []
            for i in self.inp_info:
                inputs.append(i.cpu)
            self.__call__(inputs)

    def set_profiler(self, profiler: Optional[trt.IProfiler]) -> None:
        self.context.profiler = profiler \
            if profiler is not None else trt.Profiler()

    def __call__(self, *inputs) -> Tuple[ndarray, ndarray, ndarray, ndarray]:

        assert len(inputs) == self.num_inputs
        contiguous_inputs: List[ndarray] = [
            np.ascontiguousarray(i) for i in inputs
        ]

        for i in range(self.num_inputs):

            if self.is_dynamic:
                self.context.set_binding_shape(
                    i, tuple(contiguous_inputs[i].shape))
                self.inp_info[i].gpu = cuda.mem_alloc(
                    contiguous_inputs[i].nbytes)

            cuda.memcpy_htod_async(self.inp_info[i].gpu, contiguous_inputs[i],
                                   self.stream)
            self.bindings[i] = int(self.inp_info[i].gpu)

        output_gpu_ptrs: List[int] = []
        outputs: List[ndarray] = []

        for i in range(self.num_outputs):
            j = i + self.num_inputs
            if self.is_dynamic:
                shape = tuple(self.context.get_binding_shape(j))
                dtype = self.out_info[i].dtype
                cpu = np.empty(shape, dtype=dtype)
                gpu = cuda.mem_alloc(contiguous_inputs[i].nbytes)
                cuda.memcpy_htod_async(gpu, cpu, self.stream)
            else:
                cpu = self.out_info[i].cpu
                gpu = self.out_info[i].gpu
            outputs.append(cpu)
            output_gpu_ptrs.append(gpu)
            self.bindings[j] = int(gpu)

        self.context.execute_async_v2(self.bindings, self.stream.handle)
        self.stream.synchronize()

        for i, o in enumerate(output_gpu_ptrs):
            cuda.memcpy_dtoh_async(outputs[i], o, self.stream)
        
        data_output = tuple(outputs) if len(outputs) > 1 else outputs[0]
        num_dets, bboxes, scores, labels = (i[0] for i in data_output)
        nums = num_dets.item()
        bboxes = bboxes[:nums]
        scores = scores[:nums]
        labels = labels[:nums]
        
        return bboxes, scores, labels

def letterbox(im: ndarray,
              new_shape: Union[Tuple, List] = (640, 640),
              color: Union[Tuple, List] = (0, 0, 0)) \
        -> Tuple[ndarray, float, Tuple[float, float]]:
    # Resize and pad image while meeting stride-multiple constraints
    shape = im.shape[:2]  # current shape [height, width]
    if isinstance(new_shape, int):
        new_shape = (new_shape, new_shape)

    # Scale ratio (new / old)
    r = min(new_shape[0] / shape[0], new_shape[1] / shape[1])

    # Compute padding
    new_unpad = int(round(shape[1] * r)), int(round(shape[0] * r))
    dw, dh = new_shape[1] - new_unpad[0], new_shape[0] - new_unpad[
        1]  # wh padding

    dw /= 2  # divide padding into 2 sides
    dh /= 2

    if shape[::-1] != new_unpad:  # resize
        im = cv2.resize(im, new_unpad, interpolation=cv2.INTER_LINEAR)
    top, bottom = int(round(dh - 0.1)), int(round(dh + 0.1))
    left, right = int(round(dw - 0.1)), int(round(dw + 0.1))
    im = cv2.copyMakeBorder(im,
                            top,
                            bottom,
                            left,
                            right,
                            cv2.BORDER_CONSTANT,
                            value=color)  # add border
    return im, r, (dw, dh)
def blob(im: ndarray, return_seg: bool = False) -> Union[ndarray, Tuple]:
    if return_seg:
        seg = im.astype(np.float32) / 255
    im = im.transpose([2, 0, 1])
    im = im[np.newaxis, ...]
    im = np.ascontiguousarray(im).astype(np.float32) / 255
    if return_seg:
        return im, seg
    else:
        return im
      
CLASSES = ('person', 'bicycle', 'car', 'motorcycle', 'airplane', 'bus',
           'train', 'truck', 'boat', 'traffic light', 'fire hydrant',
           'stop sign', 'parking meter', 'bench', 'bird', 'cat', 'dog',
           'horse', 'sheep', 'cow', 'elephant', 'bear', 'zebra', 'giraffe',
           'backpack', 'umbrella', 'handbag', 'tie', 'suitcase', 'frisbee',
           'skis', 'snowboard', 'sports ball', 'kite', 'baseball bat',
           'baseball glove', 'skateboard', 'surfboard', 'tennis racket',
           'bottle', 'wine glass', 'cup', 'fork', 'knife', 'spoon', 'bowl',
           'banana', 'apple', 'sandwich', 'orange', 'broccoli', 'carrot',
           'hot dog', 'pizza', 'donut', 'cake', 'chair', 'couch',
           'potted plant', 'bed', 'dining table', 'toilet', 'tv', 'laptop',
           'mouse', 'remote', 'keyboard', 'cell phone', 'microwave', 'oven',
           'toaster', 'sink', 'refrigerator', 'book', 'clock', 'vase',
           'scissors', 'teddy bear', 'hair drier', 'toothbrush')      
class engineA:
	def __init__(self):
		self.enggine = TRTEngine('yolov8s.engine')
		self.H, self.W = self.enggine.inp_info[0].shape[-2:]
	def detect(self, tensor):
		return self.enggine(tensor)
	def W(self):
		return self.W
	def H(self):
		return self.H
		
def vr():
    global write
    global frame
    out_send = cv2.VideoWriter('appsrc ! videoconvert ! video/x-raw,format=I420 ! nvvideoconvert ! video/x-raw(memory:NVMM) ! nvv4l2h264enc ! rtph264pay pt=96 config-interval=1 ! udpsink host=100.117.209.85 port=5201'\
         ,cv2.CAP_GSTREAMER\
         ,0\
         , 30\
         , (640, 480)\
         , True)
    if not out_send.isOpened():
        print('VideoWriter not opened')
        exit(0)
    while True:
        event.wait()
        event.clear()
        if out_send.isOpened():
            out_send.write(frame)
        if cv2.waitKey(1)&0xFF == ord('q'):
            break
    out_send.release()
            

thread_cli = threading.Thread(target=vr)
event = threading.Event()

engine = engineA()

video_pipeline = f'v4l2src device=/dev/video0 ! video/x-raw, format=YUY2, width=640, height=480, framerate=30/1 ! videoconvert ! appsink'
cap_send = cv2.VideoCapture(video_pipeline, cv2.CAP_GSTREAMER)
w = cap_send.get(cv2.CAP_PROP_FRAME_WIDTH)
h = cap_send.get(cv2.CAP_PROP_FRAME_HEIGHT)
fps = cap_send.get(cv2.CAP_PROP_FPS)
out_send = cv2.VideoWriter('appsrc ! videoconvert ! video/x-raw,format=I420 ! nvvideoconvert ! video/x-raw(memory:NVMM) ! nvv4l2h264enc ! rtph264pay pt=96 config-interval=1 ! udpsink host=100.117.209.85 port=5201'\
         ,cv2.CAP_GSTREAMER\
         ,0\
         , 30\
         , (640, 480)\
         , True)


if not cap_send.isOpened():
  print('VideoCapture not opened')
  exit(0)

print('Src opened, %dx%d @ %d fps' % (w, h, fps))


play = False

thread_cli.start()
while True:
  #play = False
  ret,frame = cap_send.read()
  if not ret:
    print('empty frame')
    break

  
  bgr, ratio, dwdh = letterbox(frame, (engine.W, engine.H))
  rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
  tensor = blob(rgb, return_seg=False)
  dwdh = np.array(dwdh * 2, dtype=np.float32)
  tensor = np.ascontiguousarray(tensor)
  results = engine.detect(tensor)


  bboxes, scores, labels = results
  bboxes -= dwdh
  bboxes /= ratio
  for (bbox, score, label) in zip(bboxes, scores, labels):
      bbox = bbox.round().astype(np.int32).tolist()
      cls_id = int(label)
      cls = CLASSES[cls_id]
      color = (0,255,0)
      cv2.rectangle(frame, tuple(bbox[:2]), tuple(bbox[2:]), color, 2)
      cv2.putText(frame,
                  f'{cls}:{score:.3f}', (bbox[0], bbox[1] - 2),
                  cv2.FONT_HERSHEY_SIMPLEX,
                  0.75, [225, 255, 255],
                  thickness=2)
    
  #play = True
  event.set()
  if cv2.waitKey(1)&0xFF == ord('q'):
    break
cap_send.release()
