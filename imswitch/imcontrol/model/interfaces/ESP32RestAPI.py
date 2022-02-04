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
import threading
import json
import time
import os
import sys


try:
    import cv2
    is_cv2 = True
except:
    is_cv2 = False
import socket
import serial
import serial.tools.list_ports

from tempfile import NamedTemporaryFile

try: 
    from imswitch.imcommon.model import initLogger
    IS_IMSWITCH = True
except: 
    print("No imswitch available")
    IS_IMSWITCH = False
    

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
    
    is_wifi = False
    is_serial = False
    
    is_filter_init = False
    filter_position = 0

    steps_last = 0
    
    def __init__(self, host=None, port=31950, serialport=None, baudrate=115200):
        
        if host is not None:
            # use client in wireless mode
            self.is_wifi = True
            self.host = host
            self.port = port
    
            # check if host is up
            self.is_connected = self.isConnected()
    
            if IS_IMSWITCH:
                self.__logger = initLogger(self, tryInheritParent=True)
                self.__logger.debug(f"Connecting to microscope {self.host}:{self.port}")

        elif serialport is not None:
            # use client in wired mode
            self.serialport = serialport # e.g.'/dev/cu.SLAB_USBtoUART'
            self.is_serial = True
            
            self.__logger.debug('Searching for SERIAL devices...')
            _available_ports = serial.tools.list_ports.comports(include_links=False)
            for iport in _available_ports:
                try:
                    self.serialdevice = serial.Serial(port=serialport, baudrate=baudrate, timeout=1)
                    _state = self.get_state()
                    _identifier_name = _state["identifier_name"]
                    if _identifier_name ]== "UC2_Feather":
                        return
                except:
                    self.__logger.debug("Trying out port "+iport.device+" failed")
                


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

    def get_json_thread(self, path, wait_for_result=False):
        if self.is_connected and self.is_wifi:
            t = threading.Thread(target=self.get_json_thread, args = (path))
            t.daemon = True
            t.start()
            if wait_for_result:
                t.join()
                return self.getmessage
            return None
        return None

    def get_json(self, path):
        """Perform an HTTP GET request and return the JSON response"""
        if self.is_connected and self.is_wifi:
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
        elif self.is_serial:
            path = path.replace(self.base_uri,"")
            message = {"task":path}
            message = json.dumps(message)
            self.serialdevice.flushInput()
            self.serialdevice.flushOutput()    
            returnmessage = self.serialdevice.write(message.encode(encoding='UTF-8'))
            return returnmessage
        else:
            return None

    def post_json_thread(self, path, payload={}, headers=None, timeout=1, is_blocking=True):
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

    def post_json(self, path, payload={}, headers=None, timeout=10):
        """Make an HTTP POST request and return the JSON response"""
        if self.is_connected and self.is_wifi:
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
        elif self.is_serial:
            payload["task"] = path
            self.writeSerial(payload)
            returnmessage = self.readSerial()
            return returnmessage

    def writeSerial(self, payload):
        self.serialdevice.flushInput()
        self.serialdevice.flushOutput()    
        if type(payload)==dict:
            payload = json.dumps(payload)
        self.serialdevice.write(payload.encode(encoding='UTF-8'))
        
    def readSerial(self, is_blocking=True):
        returnmessage = ''
        rmessage = '' 
        icounter = 0
        while is_blocking:
            rmessage =  self.serialdevice.readline().decode()
            returnmessage += rmessage
            icounter+=1
            if rmessage.find("//")==0 or icounter>50: break
        
        # casting to dict
        try:
            returnmessage = json.loads(returnmessage.split("--")[0].split("++")[-1])
        except:
            self.__logger.debu("Casting json string from serial to Python dict failed")

        return returnmessage
       
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
    
    
    def get_state(self, timeout=1):
        path = "/state_get"
        
        payload = {
            "task":path
        }
        r = self.post_json(path, payload, timeout=timeout)
        return r



    def set_laser(self, channel='R', value=0, auto_filterswitch=False, timeout=20, is_blocking = True):
        if auto_filterswitch and value >0:
            self.switch_filter(channel, timeout=timeout,is_blocking=is_blocking)
        
        path = '/LASER_act'
        if channel == 'R':
            LASERid = 1
        if channel == 'G':
            LASERid = 2
        if channel == 'B':
            LASERid = 3
            
        payload = {
            "task": path, 
            "LASERid": LASERid,
            "LASERval": value   
        }

        r = self.post_json(path, payload)
        return r


    def move_x(self, steps=100, speed=1000, is_blocking=False):
        r = self.move_stepper(axis=1, steps=steps, speed=speed, timeout=1, backlash=self.backlash_x, is_blocking=is_blocking)
        return r

    def move_y(self, steps=100, speed=1000, is_blocking=False):
        r = self.move_stepper(axis=2, steps=steps, speed=speed, timeout=1, backlash=self.backlash_y, is_blocking=is_blocking)
        return r

    def move_z(self, steps=100, speed=1000, is_blocking=False):
        r = self.move_stepper(axis=3, steps=steps, speed=speed, timeout=1, backlash=self.backlash_z, is_blocking=is_blocking)
        return r

    def move_stepper(self, axis=1, steps=100, speed=10, is_absolute=False, timeout=1, backlash=20, is_blocking=False):
        
        path = "/motor_act"
        
        # detect change in direction
        if np.sign(self.steps_last) != np.sign(steps):
            # we want to overshoot a bit
            print("Detected position change:")
            steps += (np.sign(steps)*backlash)
            print(steps)

        payload = {
            "task":"/motor_act", 
            "position": np.int(steps),
            "isblocking": is_blocking,
            "isabsolute": is_absolute,
            "speed": np.int(speed),
            "axis": axis
        }
        self.steps_last = steps
        self.is_driving = True
        r = self.post_json(path, payload, timeout=timeout)
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


    def move_filter(self, steps=100, speed=200,timeout=250,is_blocking=False, axis=2):
        r = self.move_stepper(axis=axis, steps=steps, speed=speed, timeout=1, backlash=self.backlash_z, is_blocking=is_blocking)
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
