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
    def __init__(self, frame_queue: queue.Queue):
        threading.Thread.__init__(self)

        # latest frame from camera
        self.latest_frame = None
        self.latest_frame_raw = None # for full resolution
        self.resolution_preview = (320, 240)

        self.is_connected = False # camera connected?
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
        frames = {}
        self.alive = True
        self.log.info('Thread \'FrameConsumer\' started.')
        while self.alive:
            # Update current state by dequeuing all currently available frames.
            frames_left = self.frame_queue.qsize()

            # get time for frame acquisition
            self.t_now = time.time()

            # retrieve frame
            try:
                _, frame = self.frame_queue.get_nowait()
                self.is_connected = True
                images = frame.as_numpy_ndarray()
                np_images = np.concatenate(images, axis=1)

            except:
                # If there are no frames available, show dummy image instead
                np_images = create_dummy_frame(self.resolution_preview[1],self.resolution_preview[0])
                self.is_connected = False

            # save latest frame and make it accessible 
            self.latest_frame = np_images


        self.log.info('Thread \'FrameConsumer\' terminated.')

    def crop_square(self, frame):
        frame_np = frame.as_np_array()
        dim_to_crop = np.min(frame_np.shape())
        frame_np[frame_np.shape[0]//2-dim_to_crop//2:frame_np.shape[0]//2+dim_to_crop//2,
                frame_np.shape[1]//2-dim_to_crop//2:frame_np.shape[1]//2+dim_to_crop//2]
        return frame_np

    def getLatestFrame(self, is_raw=True):
        """[summary]

        Returns:
            [type]: [description]
        """
        if is_raw:
            frame = self.latest_frame
        else: 
            frame = cv2.resize(self.latest_frame, (self.resolution_preview[0], self.resolution_preview[1]), interpolation=cv2.INTER_NEAREST)
        return self.crop_square(frame)
        
    def setWindow(self, window):
        # self.window = WINDOW_START_FROM_LEFT, WINDOW_START_FROM_TOP, WINDOW_HEIGHT, WINDOW_WIDTH
        self.window = WINDOW_START_FROM_LEFT, WINDOW_START_FROM_TOP, window[2], window[3]

    def setPreviewResolution(self, size=(480,320)):
        self.resolution_preview = size

    def getCameraConnected(self):
        return self.is_connected
