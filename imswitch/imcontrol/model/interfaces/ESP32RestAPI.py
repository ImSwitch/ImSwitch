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
import requests 
import json
import time
import cv2
from tempfile import NamedTemporaryFile 
from imswitch.imcommon.model import initLogger

#import matplotlib.pyplot as plt

ACTION_RUNNING_KEYWORDS = ["idle", "pending", "running"]
ACTION_OUTPUT_KEYS = ["output", "return"]




class ESP32Client(object):
    # headers = {'ESP32-version': '*'}
    headers={"Content-Type":"application/json"}

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
            #self.get_json(self.base_uri)
        self.__logger = initLogger(self, tryInheritParent=True)
        self.__logger.debug(f"Connecting to microscope {self.host}:{self.port}")


    is_filter_init = False
    filter_position = 0

    is_connected = False

    is_working = False
        
    @property
    def base_uri(self):
        return f"http://{self.host}:{self.port}"

    def get_json_thread(self, path):
        """Perform an HTTP GET request and return the JSON response"""
        if not path.startswith("http"):
            path = self.base_uri + path
        try:
            r = requests.get(path)
            r.raise_for_status()
            self.is_working = False
            return r.json()
        except Exception as e:
            self.__logger.error(e)
            self.is_working = False
            # not connected
            return None

    def get_json(self, path):
        if not self.is_working:
            self.is_working = True
            t = threading.Thread(target=self.get_json_thread, args = (path))
            t.daemon = True
            t.start()
        return None

    def post_json(self, path, payload={}, headers=None, timeout=3):
        if not self.is_working:
            self.is_working = True
            t = threading.Thread(target=self.post_json_thread, args = (path, payload, headers, timeout))
            t.daemon = True
            t.start()
        return None

    def post_json_thread(self, path, payload={}, headers=None, timeout=10):
        """Make an HTTP POST request and return the JSON response"""
        if not path.startswith("http"):
            path = self.base_uri + path
        if headers is None:
            headers = self.headers
        
        try:
            r = requests.post(path, json=payload, headers=headers,timeout=timeout)
            r.raise_for_status()
            r = r.json()
            self.is_working = False
            return r
        except Exception as e:
            self.__logger.error(e)
            self.is_working = False
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
    
    def set_laser(self, value):
        payload = {
            "value": value
        }
        path = '/laser'
        r = self.post_json(path, payload)
        return r    

    def set_laser(self, channel='R', value=0, auto_filterswitch=False):
        if auto_filterswitch and value >0:
            self.switch_filter(channel)
        payload = {
            "value": value
        }
        if channel == 'R':
            path = '/laser_red'
        if channel == 'G':
            path = '/laser_green'
        if channel == 'B':
            path = '/laser_blue'
        if channel == 'W':
            path = '/led_white'
        r = self.post_json(path, payload)
        return r        

    def set_laser_red(self, value, auto_filterswitch=False):
        return self.set_laser('R', value, auto_filterswitch)
    
    def set_laser_green(self, value, auto_filterswitch=False):
        return self.set_laser('G', value, auto_filterswitch)
    
    def set_laser_blue(self, value, auto_filterswitch=False):
        return self.set_laser('B', value, auto_filterswitch)
        
    def move_x(self, steps=100, speed=10):
        payload = {
            "steps": steps, 
            "speed": speed,            
        }
        path = '/move_x'
        r = self.post_json(path, payload)
        return r
    
    def move_y(self, steps=100, speed=10):
        payload = {
            "steps": steps, 
            "speed": speed,            
        }
        path = '/move_y'
        r = self.post_json(path, payload)
        return r
    
    def lens_x(self, value=100):
        payload = {
            "lens_value": value,            
        }
        path = '/lens_x'
        r = self.post_json(path, payload)
        return r

    def move_z(self, steps=100, speed=10,timeout=1):
        payload = {
            "steps": steps, 
            "speed": speed,            
        }
        path = '/move_z'
        r = self.post_json(path, payload,timeout=timeout)
        return r

    def move_filter(self, steps=100, speed=10,timeout=1):
        payload = {
            "steps": steps, 
            "speed": speed,            
        }
        path = '/move_filter'
        r = self.post_json(path, payload,timeout=timeout)
        return r
    
    def lens_z(self, value=100):
        payload = {
            "lens_value": value,            
        }
        path = '/lens_z'
        r = self.post_json(path, payload)
        return r

    
    def send_jpeg(self, image):

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
        requests.post(self.base_uri + path, files=files)
        
    def switch_filter(self, colour="R", timeout=20, is_filter_init=None, speed=20):
        
        # switch off all lasers first!        
        self.set_laser_red(0)
        self.set_laser_blue(0)
        self.set_laser_green(0)

        if is_filter_init is not None:
            self.is_filter_init = is_filter_init
            
        if not self.is_filter_init:
            self.move_filter(steps=-2000, speed=speed)
            time.sleep(4)
            self.is_filter_init = True
            self.filter_position = 0
            
        # measured in steps from zero position
        pos_blue = 300
        pos_green = 900
        pos_red = 1500
            
        steps = 0
        if colour=="R":
            steps = pos_red-self.filter_position
            self.filter_position = pos_red
        if colour=="G":
            steps = pos_green - self.filter_position
            self.filter_position = pos_green
        if colour=="B":
            steps = pos_blue - self.filter_position
            self.filter_position = pos_blue
            
        self.move_filter(steps=steps, speed=speed)
            
        
             
        
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
        requests.post(self.base_uri + path, data=json.dumps(payload), headers=headers)
        #r = self.post_json(path, payload=payload, headers = headers)
        
           
    def move_filter(self, steps=100, speed=10,timeout=1):
        payload = {
            "steps": steps, 
            "speed": speed,            
        }
        path = '/move_filter'
        r = self.post_json(path, payload,timeout=timeout)
        return r
    
        
if __name__ == "__main__":
            
        
    #%
    host = '192.168.43.226'
    host = '192.168.2.147'
    host = '192.168.2.151'
    esp32 = ESP32Client(host, port=80)
    
    #esp32.set_led((100,2,5))
    #esp32.move_x(steps=2000, speed=8)
    #esp32.move_y(steps=2000, speed=6)
    
    #%%
    esp32.lens_x(value=10000)
    esp32.lens_z(value=10000)
    #%%
    for ix in range(0,32000,100):
        esp32.lens_x(value=ix)
        for iy in range(0,32000,100):
            esp32.lens_z(value=iy)
    esp32.lens_z(value=0)
    esp32.lens_x(value=0)
    
    #%%
    esp32.lens_x(value=0)
    esp32.lens_z(value=0)
    #%%
    for iy in range(0,1000,1):
        esp32.set_laser(np.sin(iy/1000*np.pi*100)*10000)
    
        
    #%%
    esp32.move_z(steps=500,  speed=1000)
    
    #%%
    for i in range(100):
        print(i)
        esp32.move_z(steps=i*100, speed=i*100)
        
    
    #%%
    for i in range(100):
        print(i)
        esp32.post(value = i)
    
    #%%
    esp32.set_laser_red(10000)
    esp32.set_laser_blue(10000)
    esp32.set_laser_green(10000)
    
    time.sleep(1)
    
    esp32.set_laser_red(0)
    esp32.set_laser_blue(0)
    esp32.set_laser_green(0)
    #%%
    esp32.move_filter(steps=-800, speed=20)
    # %%
    esp32.set_laser_red(0)
    esp32.set_laser_blue(0000)
    
    #%%
    esp32.set_laser_red(0)
    
    #%%
    esp32.set_led(colour=(0,255,255))
    
    #%%
    esp32.switch_filter()
    
    #%%
    image = np.random.randn(320,240)*255
    esp32.send_jpeg(image)
    
    #%%
    N_leds = 4
    I_max = 100
    iiter = 0 
    while(True):
        iiter+=1
        
        image = np.ones((320,240))*(iiter%2)*255 # np.random.randn(320,240)*
        esp32.send_jpeg(np.uint8(image))
        led_pattern = np.array((np.reshape(np.random.randint(0,I_max ,N_leds**2),(N_leds,N_leds)),
                       np.reshape(np.random.randint(0,I_max ,N_leds**2),(N_leds,N_leds)),
                       np.reshape(np.random.randint(0,I_max ,N_leds**2),(N_leds,N_leds))))
        
        esp32.send_ledmatrix(led_pattern)


# Copyright (C) ImSwitch developers 2021
# This file is part of ImSwitch.
#
# ImSwitch is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# ImSwitch is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
