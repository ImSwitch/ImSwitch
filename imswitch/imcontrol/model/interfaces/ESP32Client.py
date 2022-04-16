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



class galvo(object):
    def __init__(self, channel=1, frequency=1000, offset=0, amplitude=1/2, clk_div=0):
        '''
        defaults:
            dac->Setup(DAC_CHANNEL_1, 0, 1, 0, 0, 2);
            dac->Setup(dac_channel, clk_div, frequency, scale, phase, invert);
      '''
        self.channel= channel
        self.frequency = frequency
        self.offset = offset
        self.amplitude = amplitude
        self.clk_div = clk_div
        self.path = "/dac_act"

    


    def return_dict(self):
        dict = {
        "task":self.path,
        "dac_channel": self.channel, # 1 or 2
        "frequency": self.frequency,
        "offset": self.offset,
        "amplitude":self.amplitude,
        "clk_div": self.clk_div
        }
        return dict



class ESP32Client(object):
    # headers = {'ESP32-version': '*'}
    headers={"Content-Type":"application/json"}
    getmessage = ""
    is_connected = False

    microsteppingfactor_filter=16 # run more smoothly
    filter_pos_1 = 2000*microsteppingfactor_filter
    filter_pos_3 = 3500*microsteppingfactor_filter
    filter_pos_2 = 0*microsteppingfactor_filter
    filter_pos_init = -5000*microsteppingfactor_filter

    backlash_x = 0
    backlash_y = 0
    backlash_z = 0
    is_driving = False
    is_sending = False

    is_enabled = True

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


        self.galvo1 = galvo(channel=1)
        self.galvo2 = galvo(channel=2)



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
            self.is_connected = True # attempting to initiliaze connection
            try:
                self.serialdevice = serial.Serial(port=self.serialport, baudrate=baudrate, timeout=1)
                time.sleep(2) # let it warm up
            except:
                # try to find the PORT
                _available_ports = serial.tools.list_ports.comports(include_links=False)
                for iport in _available_ports:
                    # list of possible serial ports
                    if IS_IMSWITCH: self.__logger.debug(iport.device)
                    portslist = ("COM", "/dev/tt", "/dev/a", "/dev/cu.SLA","/dev/cu.wchusb") # TODO: Hardcoded :/
                    descriptionlist = ("CH340")
                    if iport.device.startswith(portslist) or iport.description.find(descriptionlist) != -1:
                        try:
                            self.serialdevice = serial.Serial(port=iport.device, baudrate=baudrate, timeout=1)
                            time.sleep(2)
                            _state = self.get_state()
                            _identifier_name = _state["identifier_name"]
                            self.set_state(debug=False)
                            if True: # _identifier_name == "UC2_Feather":
                                self.serialport = iport.device
                                return

                        except Exception as e:
                            if IS_IMSWITCH:
                                self.__logger.debug("Trying out port "+iport.device+" failed")
                                self.__logger.error(e)
                            self.is_connected = False
        else:
            self.is_connected = False
            if IS_IMSWITCH: self.__logger.error("No ESP32 device is connected - check IP or Serial port!")

        self.__logger.debug("We are connected: "+str(self.is_connected))

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
        elif self.is_serial and self.is_connected:
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
            try:
                payload["task"]
            except:
                payload["task"] = path
            try:
                is_blocking = payload['isblock']
            except:
                is_blocking = True
            self.writeSerial(payload)
            #self.__logger.debug(payload)
            returnmessage = self.readSerial(is_blocking=is_blocking, timeout=timeout)
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
                #self.__logger.debug(rmessage)
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


    '''
    HIGH-LEVEL Functions that rely on basic REST-API functions
    '''

    def move_x(self, steps=100, speed=1000, is_blocking=False, is_absolute=False, is_enabled=False):
        r = self.move_stepper(steps=(steps,0,0), speed=speed, timeout=1, backlash=(self.backlash_x,0,0), is_blocking=is_blocking, is_absolute=is_absolute, is_enabled=is_enabled)
        return r

    def move_y(self, steps=100, speed=1000, is_blocking=False, is_absolute=False, is_enabled=False):
        r = self.move_stepper(steps=(0,steps,0), speed=speed, timeout=1, backlash=(0,self.backlash_y,0), is_blocking=is_blocking, is_absolute=is_absolute, is_enabled=is_enabled)
        return r

    def move_z(self, steps=100, speed=1000, is_blocking=False, is_absolute=False, is_enabled=False):
        r = self.move_stepper(steps=(0,0,steps), speed=speed, timeout=1, backlash=(0,0,self.backlash_z), is_blocking=is_blocking, is_absolute=is_absolute, is_enabled=is_enabled)
        return r

    def move_xyz(self, steps=(10,10,10), speed=(1000,1000,1000), speed1=None, speed2=None, speed3=None, is_blocking=False, is_absolute=False, is_enabled=False):
        if len(speed)!= 3:
            speed = (speed,speed,speed)

        r = self.move_stepper(steps=steps, speed=speed, timeout=1, backlash=(self.backlash_x,self.backlash_y,self.backlash_z), is_blocking=is_blocking, is_absolute=is_absolute, is_enabled=is_enabled)
        return r

    def send_jpeg(self, image):
        #TODO: This has not been tested! 
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

    def switch_filter(self, laserid=1, timeout=20, is_filter_init=None, speed=250, is_blocking=True):

        # switch off all lasers first!
        self.set_laser(1, 0)
        self.set_laser(2, 0)
        self.set_laser(3, 0)

        if is_filter_init is not None:
            self.is_filter_init = is_filter_init

        if not self.is_filter_init:
            self.move_filter(steps=self.filter_pos_init, speed=speed*self.microsteppingfactor_filter, is_blocking=is_blocking)
            self.is_filter_init = True
            self.filter_position = 0

        # measured in steps from zero position

        steps = 0
        if laserid==1:
            steps = self.filter_pos_1 - self.filter_position
            self.filter_position = self.filter_pos_1
        if laserid==2:
            steps = self.filter_pos_2 - self.filter_position
            self.filter_position = self.filter_pos_2
        if laserid==3:
            steps = self.filter_pos_3 - self.filter_position
            self.filter_position = self.filter_pos_3

        self.move_filter(steps=steps, speed=speed*self.microsteppingfactor_filter, is_blocking=is_blocking)



    def move_filter(self, steps=100, speed=200,timeout=250,is_blocking=False, axis=2):
        steps_xyz = (0,steps,0)
        r = self.move_stepper(steps=steps_xyz, speed=speed, timeout=1, is_blocking=is_blocking)
        return r
    
    
    
    '''
    LOW-LEVEL FUNCTIONS
    
    These functions directly relate to the REST-API
    '''
    
    '''
    ##############################################################################################################################
    LED ARRAY
    ##############################################################################################################################
    '''
    def send_LEDMatrix_array(self, led_pattern, timeout=1):
        '''
        Send an LED array pattern e.g. an RGB Matrix: led_pattern=np.zeros((3,8,8))
        '''
        path = '/ledarray_act'
        payload = {
            "red": led_pattern[0,:,:].flatten().tolist(),
            "green": led_pattern[1,:,:].flatten().tolist(),
            "blue": led_pattern[2,:,:].flatten().tolist(),
            "arraySize": led_pattern.shape[1]*led_pattern.shape[2],
            "LEDArrMode": "array"
        }
        r = self.post_json(path, payload, timeout=timeout)

    def send_LEDMatrix_full(self, intensity = (255,255,255),timeout=1):
        '''
        set all LEDs with te same RGB value: intensity=(255,255,255)
        '''
        path = '/ledarray_act'
        payload = {
            "red": intensity[0],
            "green": intensity[1],
            "blue": intensity[2],
            "LEDArrMode": "full"
        }
        print("Setting LED Pattern (full): "+ str(intensity))
        r = self.post_json(path, payload, timeout=timeout)
    
    def send_LEDMatrix_special(self, pattern="left", intensity = (255,255,255),timeout=1):
        '''
        set all LEDs inside a certain pattern (e.g. left half) with the same RGB value: intensity=(255,255,255), rest 0
        '''
        path = '/ledarray_act'
        payload = {
            "red": intensity[0],
            "green": intensity[1],
            "blue": intensity[2],
            "LEDArrMode": pattern
        }
        print("Setting LED Pattern (full): "+ str(intensity))
        r = self.post_json(path, payload, timeout=timeout)
    
        
    def send_LEDMatrix_single(self, indexled=0, intensity=(255,255,255), Nleds=8*8, timeout=1):
        '''
        update only a single LED with a colour:  indexled=0, intensity=(255,255,255)
        '''
        path = '/ledarray_act'
        payload = {
            "red": intensity[0],
            "green": intensity[1],
            "blue": intensity[2],
            "indexled": indexled,
            "Nleds": Nleds,
            "LEDArrMode": "single"
        }
        self.__logger.debug("Setting LED PAttern: "+str(indexled)+" - "+str(intensity))
        r = self.post_json(path, payload, timeout=timeout)
        
    def send_LEDMatrix_multi(self, indexled=(0), intensity=((255,255,255)), Nleds=8*8, timeout=1):
        '''
        update a list of individual LEDs with a colour:  led_pattern=(1,2,6,11), intensity=((255,255,255),(125,122,1), ..)
        '''
        path = '/ledarray_act'
        payload = {
            "red": intensity[0],
            "green": intensity[1],
            "blue": intensity[2],
            "indexled": indexled,
            "Nleds": Nleds,
            "LEDArrMode": "single"
        }
        self.__logger.debug("Setting LED PAttern: "+str(indexled)+" - "+str(intensity))
        r = self.post_json(path, payload, timeout=timeout)        
        
    
    def get_LEDMatrix(self, timeout=1):
        '''
        get information about pinnumber and number of leds
        '''
        path = "/ledarray_get"
        payload = {
            "task":path
        }
        r = self.post_json(path, payload, timeout=timeout)
        return r       
    
    def set_LEDMatrix(self, LED_ARRAY_PIN=1, LED_N_X=8, LED_N_Y=8, timeout=1):
        '''
        set information about pinnumber and number of leds
        '''
        path = '/ledarray_set'
        payload = {
            "LED_ARRAY_PIN": intensity[0],
            "LED_N_X": intensity[1],
            "LED_N_Y": intensity[2],
            "indexled": indexled,
            "Nleds": Nleds,
            "LEDArrMode": "single"
        }
        r = self.post_json(path, payload, timeout=timeout)      
        return r        

        
    '''
    ##############################################################################################################################
    MOTOR
    ##############################################################################################################################
    '''
    
    def move_forever(self, speed=(0,0,0), is_stop=False, timeout=1):
        '''
        This tells the motor to run forever at a constant speed
        '''
        payload = {
        "task":"/motor_act",
        "speed0": np.int(speed[0]), # TODO: need a fourth axis?
        "speed1": np.int(speed[0]),
        "speed2": np.int(speed[1]),
        "speed3": np.int(speed[2]),
        "isforever": np.int(not is_stop), 
        "isaccel":1,
        "isstop": np.int(is_stop)
        }
        self.is_driving = True
        r = self.post_json(path, payload, timeout=timeout)
        if is_stop:
            self.is_driving = False
        return r

    def move_stepper(self, steps=(0,0,0), speed=(1000,1000,1000), is_absolute=False, timeout=1, backlash=(0,0,0), is_blocking=True, is_enabled=False):
        '''
        This tells the motor to run at a given speed for a specific number of steps; Multiple motors can run simultaneously
        '''
        if type(speed)!=list and type(speed)!=tuple  :
            speed = (speed,speed,speed)

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
            "isblock": int(is_blocking),
            "isabs": int(is_absolute),
            "speed1": np.int(speed[0]),
            "speed2": np.int(speed[1]),
            "speed3": np.int(speed[2]),
            "isen": np.int(is_enabled)
        }
        self.steps_last_0 = steps_0
        self.steps_last_1 = steps_1
        self.steps_last_2 = steps_2
        self.is_driving = True
        r = self.post_json(path, payload, timeout=timeout)
        self.is_driving = False
        return r
    
    
    def set_motor_maxSpeed(self, axis=0, maxSpeed=10000):
        path = "/motor_set",
        payload = {
            "task": path,
            "axis": axis,
            "maxspeed": maxSpeed
        }
        r = self.post_json(path, payload)
        return r
        
    def set_motor_currentPosition(self, axis=0, currentPosition=10000):
        path = "/motor_set",
        payload = {
            "task": path,
            "axis": axis,
            "currentposition": currentPosition
        }
        r = self.post_json(path, payload)
        return r
    
    def set_motor_acceleration(self, axis=0, acceleration=10000):
        path = "/motor_set",
        payload = {
            "task": path,
            "axis": axis,
            "acceleration": acceleration
        }
        r = self.post_json(path, payload)
        return r
    
    def set_motor_pinconfig(self, axis=0, pinstep=0, pindir=0):
        path = "/motor_set",
        payload = {
            "task": path,
            "axis": axis,
            "pinstep": pinstep,
            "pindir": pindir
        }
        r = self.post_json(path, payload)
        return r
  
    def set_motor_enable(self, is_enable=1):
        path = "/motor_set",
        payload = {
            "task": path,
            "isen": is_enable
        }
        r = self.post_json(path, payload)
        return r

    def set_motor_enable(self, axis=0, sign=1):
        path = "/motor_set",
        payload = {
            "task": path,
            "axis": axis,
            "sign": sign
        }
        r = self.post_json(path, payload)
        return r      

        
    '''
    ##############################################################################################################################
    Sensors
    ##############################################################################################################################
    '''
    def read_sensor(self, sensorID=0, NAvg=100):
        path = "/readsensor_act"
        payload = {
            "readsensorID": sensorID,
            "N_sensor_avg": NAvg,
        }
        r = self.post_json(path, payload)
        try:
            sensorValue = r['sensorValue']
        except:
            sensorValue = None
        return sensorValue
    # TODO: Get/SET methods missing
    '''
    ##############################################################################################################################
    LEDs
    ##############################################################################################################################
    '''    
    def set_led(self, colour=(0,0,0)):
        payload = {
            "red": colour[0],
            "green": colour[1],
            "blue": colour[2]
        }
        path = '/led'
        r = self.post_json(path, payload)
        return r


    def set_galvo_freq(self, axis=1, value=1000):
        if axis+1 == 1:
            self.galvo1.frequency=value
            payload = self.galvo1.return_dict()
        else:
            self.galvo2.frequency=value
            payload = self.galvo2.return_dict()

        r = self.post_json(payload["task"], payload, timeout=1)
        return r

    def set_galvo_amp(self, axis=1, value=1000):
        if axis+1 == 1:
            self.galvo1.amplitude=value
            payload = self.galvo1.return_dict()
        else:
            self.galvo2.amplitude=value
            payload = self.galvo2.return_dict()

        r = self.post_json(payload["task"], payload, timeout=1)
        return r

    def get_state(self, timeout=5):
        path = "/state_get"

        payload = {
            "task":path
        }
        r = self.post_json(path, payload, timeout=timeout)
        return r

    def set_state(self, debug=False, timeout=1):
        path = "/state_set"

        payload = {
            "task":path,
            "isdebug":int(debug)
        }
        r = self.post_json(path, payload, timeout=timeout)
        return r

    def set_direction(self, axis=1, sign=1, timeout=1):
        path = "/motor_set"

        payload = {
            "task":path,
            "axis": axis,
            "sign": sign
        }

        r = self.post_json(path, payload, timeout=timeout)
        return r



    def get_position(self, axis=1, timeout=1):
        path = "/motor_get"

        payload = {
            "task":path,
            "axis": axis
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

    def set_laser(self, channel=1, value=0, auto_filterswitch=False, timeout=20, is_blocking = True):
        if auto_filterswitch and value >0:
            self.switch_filter(channel, timeout=timeout,is_blocking=is_blocking)

        path = '/laser_act'

        payload = {
            "task": path,
            "LASERid": channel,
            "LASERval": value,
            "LASERDdespeckle": int(value*.1)
        }

        r = self.post_json(path, payload)
        return r

    def sendTrigger(self, triggerId=0):
        path = '/digital_act'
        
        payload = {
            "task": path,
            "digitalid": triggerId,
            "digitalval": -1,
        }

        r = self.post_json(path, payload)
        return r