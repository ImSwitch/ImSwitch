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

FRAME_HEIGHT = 1088
FRAME_WIDTH = 1456

# Camera Settings
#CAM_GAIN = 20 # dB
T_EXPOSURE_MAX = 1e6 # µs => 1s
ExposureTime = 50e3


def set_nearest_value(cam: Camera, feat_name: str, feat_value: int):
    # Helper function that tries to set a given value. If setting of the initial value failed
    # it calculates the nearest valid value and sets the result. This function is intended to
    # be used with Height and Width Features because not all Cameras allow the same values
    # for height and width.
    feat = cam.get_feature_by_name(feat_name)

    try:
        feat.set(feat_value)

    except VimbaFeatureError:
        min_, max_ = feat.get_range()
        inc = feat.get_increment()

        if feat_value <= min_:
            val = min_

        elif feat_value >= max_:
            val = max_

        else:
            val = (((feat_value - min_) // inc) * inc) + min_

        feat.set(val)

        msg = ('Camera {}: Failed to set value of Feature \'{}\' to \'{}\': '
               'Using nearest valid value \'{}\'. Note that, this causes resizing '
               'during processing, reducing the frame rate.')
        Log.get_instance().info(msg.format(cam.get_id(), feat_name, feat_value, val))




###########################################################################################
''' VimbaCameraThread 

This class keeps the camera alive and manages the following:
1. Opens a image producer
2. Opens an image consumer, could be 
    a.) window
    b.) file
    c.) stream
3. Manages camera parameters

Future:
- We sould handle trigger events:
        cam.TriggerSelector.set('FrameStart')
        cam.TriggerActivation.set('RisingEdge')
        cam.TriggerSource.set('Line0')
        cam.TriggerMode.set('On')


'''

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

    def setROI(self, vpos, hpos, vsize, hsize):
        print(vpos, hpos, vsize, hsize)
        # Todo: Implement

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



    def setWindow(self, window=0):
        self.window = window
        try:
            self.consumer.setWindow(self.window)
        except:
            print("Error setting window - frame producer already running?")
    
    def setFullscreen(self, fullscreen=False):
        self.fullscreen = fullscreen
        # TODO: Implement

    def getLatestFrame(self, is_raw=True):
        try:
            return self.consumer.getLatestFrame(is_raw=is_raw)
        except:
            return None

    def register_capture_callback(self, callback):
        while True:
            # wait until consumer is created
            if hasattr(self, 'consumer'):
                self.consumer.register_capture_callback(callback)
                break

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

    
               



###########################################################################################
# Actual vicamera Class for vimbas 
###########################################################################################

class vicamera():
    """[summary]
    """

    def __init__(self, resolution=None, framerate=10, exposure_time=10e6, gain=0, blacklevel=0):
        """[summary]
        Picamera:
         picamera.camera.PiCamera(camera_num=0, stereo_mode='none', stereo_decimate=False, 
         resolution=None, framerate=None, sensor_mode=0, led_pin=None)
        
        Args:
            is_record (bool, optional): [description]. Defaults to False.
            filename (str, optional): [description]. Defaults to ''.
        """

        
        # Displaying parameters
        self.preview = False                # state of the camera's preview
        self.window = None                  # coordinates for the preview window
        self.recording = False              # state of the camera's recording

        # Camera Acquisition Parameters
        self.resolution = resolution
        self.framerate = framerate
        self.exposure_time = exposure_time
        self.gain = gain
        self.blacklevel = blacklevel

        self.MAX_RESOLUTION = ((FRAME_WIDTH, FRAME_HEIGHT))
        self.revision = 'ALVIUM'

        # recording 
        self.i_frame = 0



    def start_camera(self):
        if not hasattr(self, 'camerathread'):
            # no camera thread open, generate one!
            self.camerathread = VimbaCameraThread()
        
        # start camera if it hasn't started already
        if(self.camerathread.is_active):
            print("Camera Thread is already running")
        else:
            print("Vimba: Starting Camera Thread")
            try:
                self.camerathread.start()
            except:
                print("Most likely, the camera will be started in the next round..")


    def start_preview(self, image_sink=None, fullscreen=False, window=None, preview_resolution=(480, 320)):
        """[summary]
        Start the camera's main frame grabber and 
        """
        self.preview = True 
        self.fullscreen = fullscreen # TODO: Need to implement that somehow
        self.window = window
        self.preview_resolution = preview_resolution
        self.image_sink = image_sink
        
        # start camera
        self.start_camera()
        self.camerathread.preview_resolution = self.preview_resolution
        
    def video_thread(self, output, framerate=20):
        while(self.recording):
            # get frame and save
            is_raw=True
            myframe = np.squeeze(self.getLatestFrame(is_raw=is_raw))
            if myframe.dtype == 'uint16':
                cv2.imwrite(output.split('.h264')[0]+'/Capture_'+str(self.i_frame)+'.tif', myframe)
            elif myframe.dtype == 'uint8':
                frame = Image.fromarray(myframe)
                frame.save(output, format=format, quality=quality)
            self.i_frame += 1
            
            
    def start_recording(self, output='', format='H264', bitrate=1, splitter_port=2, resize=None, quality=100, video_framerate=20):
        print("start_recording")
        if(not self.recording):
                self.recording = True
        self.vthread = threading.Thread(target = self.video_thread, args=(output, ))
        self.vthread.start()
        #self.vthread.join()


    def stop_recording(self, splitter_port=2):
        print("stop_recording")
        try:
            del self.vthread
        except Exception as e:
            print(str(e))
            
        if(self.recording):
            self.recording = False
        self.i_frame = 0 # reset frame counter 

    def stop_preview(self):
        #self.camerathread.stop()
        self.preview = False
    
    def capture(self, output="numpy", format='jpeg', quality=100, resize=None, bayer=False, use_video_port=False, thumbnail=None):
        """[summary]
        Get the latest frame and save it somewhere

        Args:
            output: String or file-like object to write capture data to
            fmt: Format of the capture.
            use_video_port: Capture from the video port used for streaming. Lower resolution, faster.
            resize: Resize the captured image.
            bayer: Store raw bayer data in capture
            thumbnail: Dimensions and quality (x, y, quality) of a thumbnail to generate, if supported

            output ([type]): [description]
            format ([type], optional): [description]. Defaults to None.
            resize ([type], optional): [description]. Defaults to None.
        """

        if(not self.camerathread.is_active):
            self.start_camera()

        # get frame and save
        is_raw=True
        myframe = np.squeeze(self.getLatestFrame(is_raw=is_raw))
        if myframe.dtype == 'uint16':
            cv2.imwrite(output.file.split('.jpeg')[0]+'.tif', myframe)
        elif myframe.dtype == 'uint8':
            frame = Image.fromarray(myframe)
            frame.save(output, format=format, quality=quality)
        return 
        
    def close(self):
        '''
        [Set Camera Parameters]
        '''
        self.camerathread.stop()
        del self.camerathread

    def setExposureTime(self, exposure_time=10e3):
        """[summary]

        Args:
            ExposureTime ([type], optional): [description]. Defaults to 10e6.
        """
        self.exposure_time = exposure_time
        self.camerathread.setExposureTime(self.exposure_time)

    def setGain(self, gain=0):
        """[summary]

        Args:
            gain (int, optional): [description]. Defaults to 0.
        """
        self.gain = gain
        self.camerathread.setGain(self.gain)

    def setBlacklevel(self, blacklevel=0):
        """[summary]

        Args:
            blacklevel (int, optional): [description]. Defaults to 0.
        """
        self.blacklevel = blacklevel
        self.camerathread.setBlacklevel(self.blacklevel)

    def set_window(self, window):
        """

        Args:
            window ([type]): [description]
        """
        self.window = window
        self.camerathread.setWindow(self.window)

    def set_fullscreen(self):
        pass
        # TODO: Need to implement this

    def getLatestFrame(self, is_raw = True):
        return self.camerathread.getLatestFrame(is_raw=is_raw)

    def _check_recording_stopped(self):
        pass
        # TODO: Need to implement that

    def getCameraConnected(self):
        return self.camerathread.getCameraConnected()

if __name__ == '__main__':

    try:
        camera = vicamera()
        camera.start_preview(image_sink='window')


        import time 
        time.sleep(10)
        
        camera.stop_preview()
    except:
        camera.stop_preview()
        camera.close()
