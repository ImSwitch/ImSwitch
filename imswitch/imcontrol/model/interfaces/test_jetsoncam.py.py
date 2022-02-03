# MIT License
# Copyright (c) 2019 JetsonHacks
# See license
# Using a CSI camera (such as the Raspberry Pi Version 2) connected to a
# NVIDIA Jetson Nano Developer Kit using OpenCV
# Drivers for the camera and OpenCV are included in the base image

import cv2
import numpy as np
# gstreamer_pipeline returns a GStreamer pipeline for capturing from the CSI camera
# Defaults to 1280x720 @ 60fps
# Flip the image by setting the flip_method (most common values: 0 and 2)
# display_width and display_height determine the size of the window on the screen

'''
def gstreamer_pipeline(
    capture_width=1280,
    capture_height=720,
    display_width=1280,
    display_height=720,
    framerate=60,
    flip_method=0,
):
    return "nvarguscamerasrc sensor_id=0 ! 'video/x-raw(memory:NVMM),width=3280, height=2464, framerate=21/1, format=NV12' !   nvvidconv flip-method=0 ! 'video/x-raw,width=960, height=720' !  nvvidconv ! nvegltransform ! nveglglessink -e"

def show_camera():
    # To flip the image, modify the flip_method parameter (0 and 2 are the most common)
    
    #https://forums.developer.nvidia.com/t/reading-frames-from-jetson-nano-csi-camera-with-v4l2/117804/14
    return 'v4l2-ctl -d /dev/video0 -c sensor_mode=2 --set-fmt-video=width=1920,height=1080,pixelformat=“RG10”'
    #v4l2-ctl -d /dev/video0 -c gain=170 -c override_enable=1 -c bypass_mode=0 -c exposure=33333 -c frame_rate=30000000
    #v4l2-ctl -d /dev/video0 --stream-skip=100 --stream-count=1 --stream-mmap --stream-to=frame.raw
'''


import cv2
capture = cv2.VideoCapture(0, cv2.CAP_V4L2)
capture.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'))
width = 1920.; height = 1080.
capture.set(cv2.CAP_PROP_FRAME_WIDTH, width)
capture.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
capture.get(3)
capture.get(4)
_, frame = capture.read()
gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
print(gray)

capture.release()
