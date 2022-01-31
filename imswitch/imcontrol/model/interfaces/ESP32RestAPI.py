#!/usr/bin/env python
# coding: utf-8
#%%
"""
Simple client code for the ESP32 in Python - adapted from OFM Client
Copyright 2020 Richard Bowman, released under LGPL 3.0 or later
Copyright 2021 Benedict Diederich, released under LGPL 3.0 or later
"""
import requests
import json
import time
import numpy as np
import logging
import zeroconf
import threading
import json
import time
try:
    import cv2
    is_cv2 = True
except:
    is_cv2 = False
import os
import socket

from tempfile import NamedTemporaryFile
from imswitch.imcommon.model import initLogger

#import matplotlib.pyplot as plt

ACTION_RUNNING_KEYWORDS = ["idle", "pending", "running"]
ACTION_OUTPUT_KEYS = ["output", "return"]




class ESP32Client(object):
    # headers = {'ESP32-version': '*'}
    headers={"Content-Type":"application/json"}
    getmessage = ""
    is_connected = False

    filter_pos_r = 1000
    filter_pos_b = 2000
    filter_pos_g = 0

    backlash_x = 0
    backlash_y = 0
    backlash_z = 40
    is_driving = False
    is_sending = False

    def __init__(self, host, port=31950):
        if isinstance(host, zeroconf.ServiceInfo):
            # If we have an mDNS ServiceInfo object, try each address
            # in turn, to see if it works (sometimes you get addresses
            # that don't work, if your network config is odd).
            # TODO: figure out why we can get mDNS packets even when
            # the microscope is unreachable by that IP
            for addr in host.parsed_addresses():
                if ":" in addr:
                    self.host = f"[{addr}]"
                else:
                    self.host = addr
                self.port = host.port
                try:
                    self.get_json(self.base_uri)
                    break
                except:
                    logging.info(f"Couldn't connect to {addr}, we'll try another address if possible.")
        else:
            self.host = host
            self.port = port

        # check if host is up
        self.is_connected = self.isConnected()

        self.__logger = initLogger(self, tryInheritParent=True)
        self.__logger.debug(f"Connecting to microscope {self.host}:{self.port}")


    is_filter_init = False
    filter_position = 0

    steps_z_last = 0

    def isConnected(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            s.connect((self.host, int(self.port)))
            s.settimeout(2)
            s.shutdown(2)
            return True
        except:
            return False


    @property
    def base_uri(self):
        return f"http://{self.host}:{self.port}"

    def get_json(self, path, wait_for_result=False):
        if self.is_connected:
            t = threading.Thread(target=self.get_json_thread, args = (path))
            t.daemon = True
            t.start()
            if wait_for_result:
                t.join()
                return self.getmessage
            return None
        return None

    def get_json_thread(self, path):
        """Perform an HTTP GET request and return the JSON response"""
        if self.is_connected:
            if not path.startswith("http"):
                path = self.base_uri + path
            try:
                r = requests.get(path)
                r.raise_for_status()
                self.is_connected = True

                self.getmessage = r.json()
                self.is_sending = False
                return self.getmessage

            except Exception as e:
                self.__logger.error(e)
                self.is_connected = False
                self.is_sending = False
                # not connected
                return None
        else:
            return None

    def post_json(self, path, payload={}, headers=None, timeout=1, is_blocking=True):
        tmp_counter = 0
        while self.is_sending:
            time.sleep(.1)
            tmp_counter +=1
            if tmp_counter>100: break
        self.is_sending = True
        if is_blocking:
            r = self.post_json_thread(path, payload, headers, timeout)
            self.is_sending = False
            return r
        else:
            t = threading.Thread(target=self.post_json_thread, args = (path, payload, headers, timeout))
            t.daemon = True
            t.start()
            return None

    def post_json_thread(self, path, payload={}, headers=None, timeout=10):
        """Make an HTTP POST request and return the JSON response"""
        print(timeout)
        if not path.startswith("http"):
            path = self.base_uri + path
        if headers is None:
            headers = self.headers

        try:
            r = requests.post(path, json=payload, headers=headers,timeout=timeout)
            r.raise_for_status()
            r = r.json()
            self.is_connected = True
            self.is_sending = False
            return r
        except Exception as e:
            self.__logger.error(e)
            self.is_connected = False
            self.is_sending = False
            # not connected
            return None


    def get_temperature(self):
        path = "/temperature"
        r = self.get_json(path)
        return r['value']

    #% LED
    def set_led(self, colour=(0,0,0)):
        payload = {
            "red": colour[0],
            "green": colour[1],
            "blue": colour[2]
        }
        path = '/led'
        r = self.post_json(path, payload)
        return r



    def set_laser(self, channel='R', value=0, auto_filterswitch=False, timeout=20, is_blocking = True):
        if auto_filterswitch and value >0:
            self.switch_filter(channel, timeout=timeout,is_blocking=is_blocking)
        payload = {
            "value": value
        }
        path = ''
        if channel == 'R':
            path = '/laser_red'
        if channel == 'G':
            path = '/laser_green'
        if channel == 'B':
            path = '/laser_blue'
        if channel == 'W':
            path = '/led_white'
        if channel == "":
            path = "/laser"
        r = self.post_json(path, payload, is_blocking=is_blocking)
        return r


    def move_x(self, steps=100, speed=10, is_blocking=False):
        r = self.move_stepper(axis="x", steps=steps, speed=speed, timeout=1, backlash=self.backlash_x, is_blocking=is_blocking)
        return r

    def move_y(self, steps=100, speed=10, is_blocking=False):
        r = self.move_stepper(axis="y", steps=steps, speed=speed, timeout=1, backlash=self.backlash_y, is_blocking=is_blocking)
        return r

    def move_z(self, steps=100, speed=10, is_blocking=False):
        r = self.move_stepper(axis="z", steps=steps, speed=speed, timeout=1, backlash=self.backlash_z, is_blocking=is_blocking)
        return r

    def move_stepper(self, axis="z", steps=100, speed=10, timeout=1, backlash=20, is_blocking=False):
        path = '/move_'+axis


        if np.abs(steps) < 10:
            speed = 50

        # detect change in direction
        if np.sign(self.steps_z_last) != np.sign(steps):
            # we want to overshoot a bit
            print("Detected position change:")
            steps += (np.sign(steps)*backlash)
            print(steps)

        payload = {
            "steps": np.int(steps),
            "speed": np.int(speed),
        }
        self.steps_z_last = steps
        r = self.post_json(path, payload,timeout=timeout, is_blocking=is_blocking)
        self.is_driving = False
        return r

    def lens_x(self, value=100):
        payload = {
            "lens_value": value,
        }
        path = '/lens_x'
        r = self.post_json(path, payload)
        return r

    def lens_z(self, value=100):
        payload = {
            "lens_value": value,
        }
        path = '/lens_z'
        r = self.post_json(path, payload)
        return r


    def send_jpeg(self, image):
        if is_cv2:
            temp = NamedTemporaryFile()

            #add JPEG format to the NamedTemporaryFile
            iName = "".join([str(temp.name),".jpg"])

            #save the numpy array image onto the NamedTemporaryFile
            cv2.imwrite(iName,image)
            _, img_encoded = cv2.imencode('test.jpg', image)

            content_type = 'image/jpeg'
            headers = {'content-type': content_type}
            payload = img_encoded.tostring()
            path = '/uploadimage'

            #r = self.post_json(path, payload=payload, headers = headers)
            #requests.post(self.base_uri + path, data=img_encoded.tostring(), headers=headers)
            files = {'media': open(iName, 'rb')}
            if self.is_connected:
                requests.post(self.base_uri + path, files=files)

    def switch_filter(self, colour="R", timeout=20, is_filter_init=None, speed=250, is_blocking=True):

        # switch off all lasers first!
        self.set_laser("R", 0)
        time.sleep(.1)
        self.set_laser("G", 0)
        time.sleep(.1)
        self.set_laser("B", 0)
        time.sleep(.1)

        if is_filter_init is not None:
            self.is_filter_init = is_filter_init

        if not self.is_filter_init:
            self.move_filter(steps=-3000, speed=speed, is_blocking=is_blocking)
            self.is_filter_init = True
            self.filter_position = 0

        # measured in steps from zero position

        steps = 0
        if colour=="R":
            steps = self.filter_pos_r-self.filter_position
            self.filter_position = self.filter_pos_r
        if colour=="G":
            steps = self.filter_pos_g - self.filter_position
            self.filter_position = self.filter_pos_g
        if colour=="B":
            steps = self.filter_pos_b - self.filter_position
            self.filter_position = self.filter_pos_b

        self.move_filter(steps=steps, speed=speed, is_blocking=is_blocking)





    def send_ledmatrix(self, led_pattern):
        headers = {"Content-Type":"application/json"}
        path = '/matrix'
        payload = {
            "red": led_pattern[0,:,:].flatten().tolist(),
            "green": led_pattern[1,:,:].flatten().tolist(),
            "blue": led_pattern[2,:,:].flatten().tolist()
        }
        print(self.base_uri + path)
        print(payload)
        if self.is_connected:
            requests.post(self.base_uri + path, data=json.dumps(payload), headers=headers)


    def move_filter(self, steps=100, speed=10,timeout=250,is_blocking=False):
        payload = {
            "steps": steps,
            "speed": speed,
        }
        path = '/move_filter'
        r = self.post_json(path, payload,timeout=timeout,is_blocking=is_blocking)
        return r

    def galvo_pos_x(self, pos_x = 0, timeout=1):
        payload = {
            "value": pos_x
        }
        path = '/galvo/position_x'
        r = self.post_json(path, payload,timeout=timeout)
        return r

    def galvo_amp_y(self, amp_y = 0, timeout=1):
        payload = {
            "value": amp_y
        }
        path = '/galvo/amplitude_y'
        r = self.post_json(path, payload,timeout=timeout)
        return r
