import copy
import cv2
import threading
import queue
import numpy as np
import os
import time 

from typing import Optional
from vimba import *

FRAME_QUEUE_SIZE = 1

# TODO: REMOVE THIS HERE
T_PERIODE = 0.5 # [s] - time between acquired frames

WINDOW_START_FROM_LEFT = 80
WINDOW_START_FROM_TOP = 80
IMAGE_CAPTION = 'UC2-Livestream'


def create_dummy_frame(width, height) -> np.ndarray:
    cv_frame = np.zeros((width, height, 1), np.uint8)
    cv_frame[:] = 0

    cv2.putText(cv_frame, 'No Stream available. Please connect a Camera.', org=(30, 30),
                fontScale=1, color=255, thickness=1, fontFace=cv2.FONT_HERSHEY_COMPLEX_SMALL)

    return cv_frame

class FrameConsumer(threading.Thread):
    """
    
    2. Opens an image consumer, could be 
    a.) window
    b.) file
    c.) stream

    Args:
        threading ([type]): [description]
    """
    def __init__(self, frame_queue: queue.Queue, image_sink='window', filename=None, window=None):
        """
        Args:
            frame_queue (queue.Queue): [description]
            image_sink (str, optional): [description]. Defaults to 'window'.
            filename ([type], optional): [description]. Defaults to None.
            window ([type], optional): [description]. Defaults to None.
        """

        threading.Thread.__init__(self)

        # latest frame from camera
        self.latest_frame = None
        self.latest_frame_raw = None # for full resolution

        self.resolution_preview = (320, 240)

        # TODO: Change this to cope with the parameters handed to the window dimensions
        self.window = [WINDOW_START_FROM_LEFT, WINDOW_START_FROM_TOP, self.resolution_preview[0], self.resolution_preview[1]]

        self.is_connected = False # camera connected?

        self.is_record = False
        self.is_stream = False
        self.is_display = False 
        
        self.is_window_on_top = False
        # choose which image sink we want to choose
        if image_sink=='window':
            print(" We want to display the stream of images in a window ")
            self.is_display = True
            self.is_window_on_top = False
        if image_sink=='file':
            print(" We want to save the stream of images on the disk ")
            self.is_record = True
            self.filename = filename
        if image_sink=='stream':
            print(" We want to stream the stream of images to the network ")
            self.is_stream = True
        if image_sink is None:
            self.is_stream = False
            self.is_display = False
        
        self.is_stop = False
        self.alive = False

        self.log = Log.get_instance()
        self.frame_queue = frame_queue
        self.iframe = 0
        
        # timing for frame acquisition
        self.t_min = T_PERIODE  # s
        self.t_last = 0
        self.t_now = 0

        self.frame_callback = None
        

    def run(self):
        KEY_CODE_ENTER = 13

        frames = {}
        self.alive = True

        self.log.info('Thread \'FrameConsumer\' started.')

        while self.alive:
            # Update current state by dequeuing all currently available frames.
            frames_left = self.frame_queue.qsize()

            # get time for frame acquisition
            self.t_now = time.time()

            while frames_left:
                try:
                    cam_id, frame = self.frame_queue.get_nowait()

                except queue.Empty:
                    break

                # Add/Remove frame from current state.
                if frame:
                    frames[cam_id] = frame

                else:
                    frames.pop(cam_id, None)

                frames_left -= 1
            
            # Construct image by stitching frames together.
            if frames:
                self.is_connected = True
                images = [frames[cam_id] for cam_id in sorted(frames.keys())]
                np_images_raw = np.concatenate(images, axis=1)

                # resize to fit in the window
                np_images = cv2.resize(np_images_raw, (self.resolution_preview[0], self.resolution_preview[1]), interpolation=cv2.INTER_NEAREST)

            else:
                # If there are no frames available, show dummy image instead
                np_images = create_dummy_frame(self.resolution_preview[1],self.resolution_preview[0])
                np_images_raw = np_images
                self.is_connected = False

            # save latest frame and make it accessible 
            self.latest_frame = np_images
            self.latest_frame_raw = np_images_raw

            if self.is_display:
                self.log.info('Opening the window to display the frames at (X/Y): '+str(self.window[0])+"/"+str(self.window[1]))
                cv2.imshow(IMAGE_CAPTION, self.latest_frame)
                cv2.moveWindow(IMAGE_CAPTION, self.window[0], self.window[1])

            # save frames as they come
            if self.is_record: # and (np.abs(time.time()-self.t_last)>self.t_min): # make sure we pick frames after T period
                filename = self.filename+'/BURST_t-'+str(T_PERIODE)+'_'+str(self.iframe)+'.tif'
                self.log.info('Saving images at: '+filename)
                self.t_last = time.time()
                print(np_images.shape)
                cv2.imwrite(filename, np_images)
                self.iframe += 1

        self.log.info('Thread \'FrameConsumer\' terminated.')

    def crop_square(self, frame):
        dim_to_crop = np.min(frame.as_numpy_ndarray().shape())
        frame[frame.shape[0]//2-dim_to_crop//2:frame.shape[0]//2+dim_to_crop//2,
                frame.shape[1]//2-dim_to_crop//2:frame.shape[1]//2+dim_to_crop//2]
        return frame

    def getLatestFrame(self, is_raw=True):
        """[summary]

        Returns:
            [type]: [description]
        """
        if is_raw:
            frame = self.latest_frame_raw
        else: 
            frame = self.latest_frame
        return self.crop_square(frame)
        
    def setWindow(self, window):
        # self.window = WINDOW_START_FROM_LEFT, WINDOW_START_FROM_TOP, WINDOW_HEIGHT, WINDOW_WIDTH
        self.window = WINDOW_START_FROM_LEFT, WINDOW_START_FROM_TOP, window[2], window[3]

    def setPreviewResolution(self, size=(480,320)):
        self.resolution_preview = size

    def getCameraConnected(self):
        return self.is_connected
