# image processing libraries
import numpy as np
import cv2, queue, threading, time


# https://stackoverflow.com/questions/33432426/importerror-no-module-named-queue
# bufferless VideoCapture
class VideoCapture:
    def __init__(self, name):
        self.cap = cv2.VideoCapture(name, cv2.CAP_GSTREAMER)
        #self.cap.set(cv2.CAP_PROP_CONVERT_RGB, False);
        self.q = queue.Queue()
        t = threading.Thread(target=self._reader)
        t.daemon = True
        t.start()
        self._isopen = True
        
    # read frames as soon as they are available, keeping only most recent one
    def _reader(self):
        self._isopen = True
        while True:
            ret, frame = self.cap.read()
            if not ret:
                self._isopen = False
                break
            if not self.q.empty():
                try:
                    self.q.get_nowait()   # discard previous (unprocessed) frame
                except Queue.Empty:
                    pass
            self.q.put(frame)
    
    def isOpened(self):
        return self._isopen

    def release(self):
        self.cap.release()

    def read(self):
        return None, self.q.get()


# Camera parameters 
height = 240
width = 320 
exposuretime = 1 # minimum is 1 (int values only!)


# for debugging
is_display = False
if is_display: import matplotlib.pyplot as plt 

# gstreamer pipeline for the jetson IMX219 camera
def gstreamer_pipeline(
    capture_width=640,
    capture_height=480,
    display_width=640,
    display_height=480,
    exposuretime=1,
    framerate=120,
    flip_method=0,
    exposure_comp = 2,
    exposure_time = 10
):
    #gst-launch-1.0 
    # nvarguscamerasrc awblock=true aelock=false  exposuretimerange="100000 100000"  gainrange="1 1" ispdigitalgainrange="1 1"  ! 'video/x-raw(memory:NVMM),width=1920,height=1080,format=NV12' ! nvoverlaysink
    # nvarguscamerasrc awblock=true aelock=false width=(int)640, height=(int)480, exposuretimerange="(int)100000 (int)100000" gainrange="1 1" ispdigitalgainrange="1 1" format=(string)NV12, framerate=(fraction)120/1 ! nvvidconv flip-method=0 ! video/x-raw, width=(int)640, height=(int)480, format=(string)BGRx ! videoconvert ! video/x-raw, format=(string)BGR ! appsinkvideo/x-raw(memory:NVMM), 

    exposuretime = int(exposuretime*100000)
    return (
        'nvarguscamerasrc '
        'exposuretimerange="%d %d" gainrange="1 1" ispdigitalgainrange="1 1" '
        'awblock=true aelock=true '
        '! video/x-raw(memory:NVMM), '
        #"width=(int)%d, height=(int)%d, "
        'width=(int)%d, height=(int)%d, ' #" ##exposurecompensation=-2, aelock=true, "  #exposuretimerange=34000 35873300, 
        "format=(string)NV12, framerate=(fraction)%d/1 ! "
        "nvvidconv flip-method=%d ! "
        "video/x-raw, width=(int)%d, height=(int)%d, format=(string)BGRx ! "
        "videoconvert ! "
        "video/x-raw, format=(string)BGR ! appsink"
        % (
            exposuretime,
            exposuretime,
            capture_width,
            capture_height, 
            framerate,
            flip_method,
            display_width,
            display_height,
        )
    )


# open camera
cap = VideoCapture(gstreamer_pipeline(exposuretime=exposuretime,capture_width=width, capture_height = height, display_width=width, display_height=height, flip_method=0))#, cv2.CAP_GSTREAMER)
print("Camera is open")

# let the camera warm up
for i in range(20):
    _, img = cap.read() 
    print(np.mean(img))