import copy
import cv2
import threading
import queue
import numpy as np
import os
import time 

from PIL import Image

from typing import Optional
from vimba import *

from imswitch.imcontrol.model.interfaces.vimbapy.vicamera_frameproducer import *
from imswitch.imcontrol.model.interfaces.vimbapy.vicamera_frameconsumer import *


# Camera Settings
#CAM_GAIN = 20 # dB
T_EXPOSURE_MAX = 1e6 # µs => 1s
ExposureTime = 50e3

###########################################################################################


class VimbaCameraThread(threading.Thread):
    def __init__(self, is_record=False, filename='',
    resolution=(640,),
    framerate=20,
    exposure_time=10e6,
    gain=0,
    blacklevel=255):
        threading.Thread.__init__(self)

        self.is_connected = False
        self.frame_queue = queue.Queue(maxsize=FRAME_QUEUE_SIZE)
        self.producers = {}
        self.producers_lock = threading.Lock()
        self.is_record = is_record
        self.filename = filename
        self.is_active = False
        self.IntensityCorrection = 50
        self.ExposureTime = ExposureTime
        self.Gain = 10
        self.blacklevel = 0
        self.PIX_HEIGHT = -1
        self.PIX_WIDTH = -1

        # TODO: Cleanup class variables!
        # Displaying parameters
        self.preview = False                # state of the camera's preview
        self.window = None                  # coordinates for the preview window

        # Camera Acquisition Parameters
        self.resolution = resolution
        self.framerate = framerate
        self.exposure_time = exposure_time
        self.gain = gain
        self.blacklevel = blacklevel

        self.image_sink = None  # can be 'window', 'stream', 'record', or NONE
        self.filename = '' # TODO: Adapt it!

        self.preview_resolution = (FRAME_WIDTH,FRAME_HEIGHT)

        # recording
        self.i_frame = 0 # iterator for the recorded frames

    def __call__(self, cam: Camera, event: CameraEvent):
        # New camera was detected. Create FrameProducer, add it to active FrameProducers
        if event == CameraEvent.Detected:
            with self.producers_lock:
                self.producer = FrameProducer(cam, self.frame_queue)
                self.producer.start()

        # An existing camera was disconnected, stop associated FrameProducer.
        elif event == CameraEvent.Missing:
            with self.producers_lock:
                self.producer.stop()
                self.producer.join()

    def run(self):
        log = Log.get_instance()
        self.consumer = FrameConsumer(self.frame_queue, image_sink=self.image_sink, filename=self.filename)
        self.consumer.setPreviewResolution(size=self.preview_resolution)

        vimba = Vimba.get_instance()
        #vimba.enable_log()
        vimba.disable_log ()

        log.info('Thread \'VimbaCameraThread\' started.')
        try:
            with vimba:
                # Construct FrameProducer threads for the detected camera
                cams = vimba.get_all_cameras()
                cam = cams[0]
                self.producer = FrameProducer(cam, self.frame_queue)

                # get camera parameters
                self.getFramesize()

                # Start FrameProducer threads
                with self.producers_lock:
                    self.is_active = True
                    self.producer.start()
                
                # Start and wait for consumer to terminate
                vimba.register_camera_change_handler(self)
                self.consumer.start()
                self.consumer.join()
                vimba.unregister_camera_change_handler(self)

                # Stop all FrameProducer threads
                with self.producers_lock:
                    # Initiate concurrent shutdown
                    self.producer.stop()

                    # Wait for shutdown to complete
                    self.producer.join()
        except Exception as e:
            print(str(e))    
        self.is_active = False
        log.info('Thread \'VimbaCameraThread\' terminated.')

    def stop(self):
        # Stop all FrameProducer threads
        print("Stopping main CameraThread ")
        self.consumer.is_stop = True
        while True:
            if not self.consumer.alive:
                del self.consumer
                del self.producer
                break
            
    def close(self):
        '''
        [Set Camera Parameters]
        '''
        self.camerathread.stop()
        del self.camerathread            

    def getFramesize(self):
        self.PIX_HEIGHT, self.PIX_WIDTH = self.producer.getFramesize()

    def setROI(self, vpos, hpos, vsize, hsize):
        self.producer.setRoi(vpos, hpos, vsize, hsize)

    def setIntensityCorrection(self, IntensityCorrection=50):
        self.IntensityCorrection = IntensityCorrection

    def setExposureTime(self, ExposureTime):
        self.ExposureTime = ExposureTime
        try:
            self.producer.setExposureTime(self.ExposureTime)
        except:
            print("Error setting exposure time - frame producer already running?")

    def setGain(self, Gain):
        self.Gain = Gain
        try:
            self.producer.setGain(self.Gain)
        except:
            print("Error setting gain - frame producer already running?")

    def setBlacklevel(self, blacklevel=0):
        self.blacklevel = blacklevel
        try:
            self.producer.setBlacklevel(self.blacklevel)
        except:
            print("Error setting blacklevel - frame producer already running?")

    def setPixelFormat(self, pixelformat=12):
        # 8 or 12
        self.pixelformat = pixelformat 
        try:
            self.producer.setPixelformat(self.pixelformat)
        except:
            print("Error setting pixelformat - frame producer already running?")

    def getLatestFrame(self, is_raw=True):
        try:
            return self.consumer.getLatestFrame(is_raw=is_raw)
        except:
            return None

    def setup_camera(self, cam: Camera):
        with cam:
            # Try to adjust GeV packet size. This Feature is only available for GigE - Cameras.
            try:
                cam.GVSPAdjustPacketSize.run()

                while not cam.GVSPAdjustPacketSize.is_done():
                    pass

            except (AttributeError, VimbaFeatureError):
                pass

    def getCameraConnected(self):
        return self.consumer.getCameraConnected()