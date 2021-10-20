import copy
import cv2
import threading
import queue
import numpy as np
import os
import time 

from typing import Optional
from vimba import *


def try_put_frame(q: queue.Queue, cam: Camera, frame: Optional[Frame]):
    try:
        q.put_nowait((cam.get_id(), frame))

    except queue.Full:
        pass

class FrameProducer(threading.Thread):
    def __init__(self, cam: Camera, frame_queue: queue.Queue):
        threading.Thread.__init__(self)

        # swith off logging
        self.vimba = Vimba.get_instance ()
        self.log = Log.get_instance ()
        '''
        self.vimba.enable_log(LOG_CONFIG_WARNING_CONSOLE_ONLY)
        self.log.critical('Critical , invisible ')
        self.log.error('Error , invisible ')
        self.log.warning('Warning , invisible ')
        self.log.info('Info , invisible ')
        self.log.trace('Trace , invisible ')
        '''
        self.vimba.disable_log()

        #self.log = Log.get_instance()
        self.cam = cam
        self.frame_queue = frame_queue
        self.killswitch = threading.Event()
        self.IntensityControllerTarget = 50 # percent
        self.Gain = 1
        self.Blacklevel = 0
        self.ExposureTime = 10e3
        # TODO: Make this adaptive/initiliazed properly 
        # TODO: Make the names conincde with other vicamera classes
        
    def __call__(self, cam: Camera, frame: Frame):
        # This method is executed within VimbaC context. All incoming frames
        # are reused for later frame acquisition. If a frame shall be queued, the
        # frame must be copied and the copy must be sent, otherwise the acquired
        # frame will be overridden as soon as the frame is reused.
        if frame.get_status() == FrameStatus.Complete:

            if not self.frame_queue.full():
                frame_cpy = copy.deepcopy(frame)
                try_put_frame(self.frame_queue, cam, frame_cpy)

        cam.queue_frame(frame)

    def stop(self):
        self.killswitch.set()

    def getFramesize(self):
        try:
            print("getting pixel numbers")
            PIX_HEIGHT = self.cam.HeightMax.get()
            PIX_WIDTH = self.cam.WidthMax.get()            
            return PIX_HEIGHT, PIX_WIDTH
        except:
            print("Error getting N pixels - frame producer already running?")

    def setIntensityCorrection(self, IntensityControllerTarget):
        self.IntensityControllerTarget = IntensityControllerTarget

    def setExposureTime(self, ExposureTime):
        self.ExposureTime = ExposureTime
        try:
            self.cam.ExposureTime.set(self.ExposureTime)
        except:
            print("Error setting ExposureTime1 - frame producer already running?")


    def setROI(self, vpos, hpos, vsize, hsize):        
        try:
            print("setting ROI")
            self.cam.OffsetX.set(vpos)
            self.cam.OffsetY.set(hpos)
            self.cam.Width.set(vsize)
            self.cam.Height.set(hsize)
        except:
            print("Error setting roi - frame producer already running?")


    def setGain(self, Gain):
        self.Gain = Gain
        try:
            print("setting Gain: "+str(self.Gain))
            self.cam.Gain.set(self.Gain)
        except:
            print("Error setting Gain - frame producer already running?")

    def setExposureAuto(self, ExposureAuto=False):
        self.ExposureAuto = False
        try:
            print("setting ExposureAuto: "+str(self.ExposureAuto))
            self.cam.ExposureAuto.set(self.ExposureAuto)
        except (AttributeError, VimbaFeatureError):
            self.log.info('Camera {}: Failed to set Feature \'ExposureAuto\'.'.format(
                          self.cam.get_id()))

    def setBlacklevel(self, Blacklevel=0):
        self.Blacklevel = Blacklevel
        try:
            self.cam.BlackLevel.set(self.Blacklevel)
        except (AttributeError, VimbaFeatureError):
            self.log.info('Camera {}: Failed to set Feature \'Blacklevel\'.'.format(
                          self.cam.get_id()))

    def setPixelformat(self, pixelformat=8):
        self.pixelformat = pixelformat
        try:
            if pixelformat == 12:
                self.cam.get_feature_by_name("PixelFormat").set("Mono12")
            else:
                self.cam.set_pixel_format(PixelFormat.Mono8)
        except (AttributeError, VimbaFeatureError):
            self.log.info('Camera {}: Failed to set Feature \'PixelFormat\'.'.format(
                          self.cam.get_id()))
        
    def setFramerate(self, framerate=None):
        # Try to set exposure time to something reasonable 
        self.framerate = framerate
        try:
            self.cam.AcquisitionFrameRateEnable.set(False)
            self.cam.AcquisitionFrameRate.set(self.framerate)
        except (AttributeError, VimbaFeatureError):
            self.log.info('Camera {}: Failed to set Feature \'AcquisitionFrameRate\'.'.format(
                          self.cam.get_id()))

    def setup_camera(self):
        #set_nearest_value(self.cam, 'Height', FRAME_HEIGHT)
        #set_nearest_value(self.cam, 'Width', FRAME_WIDTH)

        # try to set IntensityControllerTarget
        '''
        try:
            self.cam.ExposureAutoMax.set(T_EXPOSURE_MAX)

        except (AttributeError, VimbaFeatureError):
            self.log.info('Camera {}: Failed to set Feature \'ExposureAutoMax\'.'.format(
                        self.cam.get_id()))
        '''

        # try to set IntensityControllerTarget
        '''
        try:
            self.cam.IntensityControllerTarget.set(self.IntensityControllerTarget)

        except (AttributeError, VimbaFeatureError):
            self.log.info('Camera {}: Failed to set Feature \'IntensityControllerTarget\'.'.format(
                        self.cam.get_id()))
        '''

        self.setExposureTime(self.ExposureTime)
        self.setGain(self.Gain)
        self.setBlacklevel(self.Blacklevel)
        self.setPixelformat(pixelformat=8)


    def run(self):
        self.log.info('Thread \'FrameProducer({})\' started.'.format(self.cam.get_id()))

        try:
            with self.cam:
                self.setup_camera()

                try:
                    self.cam.start_streaming(self)
                    self.killswitch.wait()

                finally:
                    self.cam.stop_streaming()

        except VimbaCameraError:
            pass

        finally:
            try_put_frame(self.frame_queue, self.cam, None)

        self.log.info('Thread \'FrameProducer({})\' terminated.'.format(self.cam.get_id()))
