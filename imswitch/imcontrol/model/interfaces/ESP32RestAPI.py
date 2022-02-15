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
    backlash_z = 100
    is_driving = False
    is_sending = False

    is_wifi = False
    is_serial = False

    is_filter_init = False
    filter_position = 0

    steps_last_0 = 0
    steps_last_1 = 0
    steps_last_2 = 0

    def __init__(self, host=None, port=31950, serialport=None, baudrate=115200):


        if IS_IMSWITCH:
            if IS_IMSWITCH: self.__logger = initLogger(self, tryInheritParent=True)


        if host is not None:
            # use client in wireless mode
            self.is_wifi = True
            self.host = host
            self.port = port

            # check if host is up
            self.is_connected = self.isConnected()
            if IS_IMSWITCH: self.__logger.debug(f"Connecting to microscope {self.host}:{self.port}")

        elif serialport is not None:
            # use client in wired mode
            self.serialport = serialport # e.g.'/dev/cu.SLAB_USBtoUART'
            self.is_serial = True

            if IS_IMSWITCH: self.__logger.debug(f'Searching for SERIAL devices...')
            try:
                self.serialdevice = serial.Serial(port=self.serialport, baudrate=baudrate, timeout=1)
                time.sleep(2) # let it warm up
                self.is_connected = True
            except:
                # try to find the PORT
                _available_ports = serial.tools.list_ports.comports(include_links=False)
                for iport in _available_ports:
                    # list of possible serial ports
                    if IS_IMSWITCH: self.__logger.debug(iport.device)
                    portslist = ("COM", "/dev/tt", "/dev/a", "/dev/cu.SLA","/dev/cu.wchusb") # TODO: Hardcoded :/
                    if iport.device.startswith(portslist):
                        try:
                            self.serialdevice = serial.Serial(port=iport.device, baudrate=baudrate, timeout=1)
                            _state = self.get_state()
                            _identifier_name = _state["identifier_name"]
                            if _identifier_name == "UC2_Feather":
                                self.serialport = iport.device
                                self.is_connected = True
                                return

                        except Exception as e:
                            if IS_IMSWITCH:
                                self.__logger.debug("Trying out port "+iport.device+" failed")
                                self.__logger.error(e)
                            self.is_connected = False
        else:
            self.is_connected = False
            if IS_IMSWITCH: self.__logger.error("No ESP32 device is connected - check IP or Serial port!")

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
                if IS_IMSWITCH: self.__logger.error(e)
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


    def post_json(self, path, payload={}, headers=None, timeout=1):
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
                if IS_IMSWITCH: self.__logger.error(e)
                self.is_connected = False
                self.is_sending = False
                # not connected
                return None
        elif self.is_connected and self.is_serial:
            payload["task"] = path
            try:
                is_blocking = payload['isblocking']
            except:
                is_blocking = True
            self.writeSerial(payload)
            returnmessage = self.readSerial(is_blocking=is_blocking)
            #, timeout=timeout)
            return returnmessage
        else:
            return -1

    def writeSerial(self, payload):
        self.serialdevice.flushInput()
        self.serialdevice.flushOutput()
        if type(payload)==dict:
            payload = json.dumps(payload)
        self.serialdevice.write(payload.encode(encoding='UTF-8'))

    def readSerial(self, is_blocking=True, timeout = 15): # TODO: hardcoded timeout - not code
        returnmessage = ''
        rmessage = ''
        _time0 = time.time()
        while is_blocking:
            try:
                rmessage =  self.serialdevice.readline().decode()
                returnmessage += rmessage
                if rmessage.find("--")==0 or (time.time()-_time0)>timeout: break
            except:
                pass
        # casting to dict
        try:
            returnmessage = json.loads(returnmessage.split("--")[0].split("++")[-1])
        except:
            if IS_IMSWITCH: self.__logger.debug("Casting json string from serial to Python dict failed")
            else: print("Casting json string from serial to Python dict failed")
            returnmessage = ""
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


    def set_galvo(self, dac_channel=1, frequency=1, offset=0, amplitude=0, clk_div=1000, timeout=1):

        path = "/dac_act"
        payload = {
            "task":path,
            "dac_channel": dac_channel, # 1 or 2
            "frequency":frequency,
            "offset":offset,
            "amplitude":amplitude,
            "clk_div": clk_div
        }
        r = self.post_json(path, payload, timeout=timeout)
        return r

    def get_state(self, timeout=1):
        path = "/state_get"

        payload = {
            "task":path
        }
        r = self.post_json(path, payload, timeout=timeout)
        return r

    def get_position(self, axis=1, timeout=1):
        path = "/motor_get"

        payload = {
            "task":path,
        }
        r = self.post_json(path, payload, timeout=timeout)
        _position = r["position"]
        return _position

    def set_position(self, axis=1, position=0, timeout=1):
        path = "/motor_set"
        if axis=="X": axis=1
        if axis=="Y": axis=2
        if axis=="Z": axis=3

        payload = {
            "task":path,
            "axis":axis,
            "currentposition": position
        }
        r = self.post_json(path, payload, timeout=timeout)

        return r

    def set_laser(self, channel='R', value=0, auto_filterswitch=False, timeout=20, is_blocking = True):
        if auto_filterswitch and value >0:
            self.switch_filter(channel, timeout=timeout,is_blocking=is_blocking)

        path = '/laser_act'
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


    def move_x(self, steps=100, speed=1000, is_blocking=False, is_absolute=False):
        r = self.move_stepper(steps=(steps,0,0), speed=speed, timeout=1, backlash=(self.backlash_x,0,0), is_blocking=is_blocking, is_absolute=is_absolute)
        return r

    def move_y(self, steps=100, speed=1000, is_blocking=False, is_absolute=False):
        r = self.move_stepper(steps=(0,steps,0), speed=speed, timeout=1, backlash=(0,self.backlash_y,0), is_blocking=is_blocking, is_absolute=is_absolute)
        return r

    def move_z(self, steps=100, speed=1000, is_blocking=False, is_absolute=False):
        r = self.move_stepper(steps=(0,0,steps), speed=speed, timeout=1, backlash=(0,0,self.backlash_z), is_blocking=is_blocking, is_absolute=is_absolute)
        return r

    def move_xyz(self, steps=(10,10,10), speed=1000, is_blocking=False, is_absolute=False):
        r = self.move_stepper(steps=steps, speed=speed, timeout=1, backlash=(self.backlash_x,self.backlash_y,self.backlash_z), is_blocking=is_blocking, is_absolute=is_absolute)
        return r

    def move_stepper(self, steps=(0,0,0), speed=10, is_absolute=False, timeout=1, backlash=(0,0,0), is_blocking=False):

        path = "/motor_act"

        # detect change in direction
        if np.sign(self.steps_last_0) != np.sign(steps[0]):
            # we want to overshoot a bit
            steps_0 = steps[0] + (np.sign(steps[0])*backlash[0])
        else: steps_0 = steps[0]
        if np.sign(self.steps_last_1) != np.sign(steps[1]):
            # we want to overshoot a bit
            steps_1 =  steps[1] + (np.sign(steps[1])*backlash[1])
        else: steps_1 = steps[1]
        if np.sign(self.steps_last_2) != np.sign(steps[2]):
            # we want to overshoot a bit
            steps_2 =  steps[2] + (np.sign(steps[2])*backlash[2])
        else: steps_2 = steps[2]

        payload = {
            "task":"/motor_act",
            "pos1": np.int(steps_0),
            "pos2": np.int(steps_1),
            "pos3": np.int(steps_2),
            "isblock": is_blocking,
            "isabs": is_absolute,
            "speed": np.int(speed),
        }
        self.steps_last_0 = steps_0
        self.steps_last_1 = steps_1
        self.steps_last_2 = steps_2
        self.is_driving = True
        r = self.post_json(path, payload, timeout=timeout)
        self.is_driving = False
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
        steps_xyz = (0,0,0)
        steps_xyz[axis-1] = steps
        r = self.move_stepper(steps=steps_xyz, speed=speed, timeout=1, is_blocking=is_blocking)
        return r
