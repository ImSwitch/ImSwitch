import numpy as np
from threading import Thread
import requests
import json
import time

from imswitch.imcommon.model import dirtools, modulesconfigtools, ostools, APIExport
from imswitch.imcommon.framework import Signal, Worker, Mutex, Timer
from imswitch.imcontrol.view import guitools
from imswitch.imcommon.model import initLogger
from imswitch.imcontrol.controller.basecontrollers import LiveUpdatedController
import imswitch




class FLIMLabsController(LiveUpdatedController):
    """ Linked to FLIMLabsWidget."""

    sigImageReceived = Signal()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._logger = initLogger(self, tryInheritParent=False)

        # connect camera and stage
        self.positionerName = self._master.positionersManager.getAllDeviceNames()[0]
        self.positioner = self._master.positionersManager[self.positionerName]


        self.FLIMLabsC = FLIMLabsREST(
            #firmware_selected="your_firmware",
            laser_period=12.5,  # example laser period
            #channels=[1, 2, 3],  # example channels
            image_width=100,
            image_height=100,
            offset_bottom=0,
            offset_left=0,
            offset_right=0,
            offset_top=0, 
            host_url="http://localhost"
        )
    


        # Connect FLIMLabsWidget signals
        if not imswitch.IS_HEADLESS:
            # Connect CommunicationChannel signals
            
            # scouting
            self._widget.start_button_scouting.clicked.connect(self.start_scouting)
            self._widget.stop_button_scouting.clicked.connect(self.stop_scouting)
            
            # reference
            self._widget.start_button_reference.clicked.connect(self.start_reference)
            self._widget.stop_button_reference.clicked.connect(self.stop_reference)

            # imaging
            self._widget.start_button_imaging.clicked.connect(self.start_imaging)
            self._widget.stop_button_imaging.clicked.connect(self.stop_imaging)
            
            
    def start_scouting(self):
        mParametersScouting = self._widget.getScoutingParameters()
        mParametersStageScanning = self._widget.getStageScanningParameters()
        
        self.setFLIMLabsParameters(mParametersScouting)
        self.FLIMLabsC.start_scouting(
        dwell_time=mParametersScouting["pixelDwelltime"], 
        nFrames = mParametersScouting["nFrames"])
        time.sleep(.5) # settle 
        self.startStageScanning(mParametersStageScanning)

    def stop_scouting(self):
        self.FLIMLabsC.stop_scouting()
        try:
            self.positioner.stopStageScanning()
        except:
            pass
        
    def start_reference(self):
        mParametersReference = self._widget.getReferenceParameters()
        mParametersStageScanning = self._widget.getStageScanningParameters()
        
        self.setFLIMLabsParameters(mParametersReference)
        self.FLIMLabsC.start_calibration(
            dwell_time=mParametersReference["pixelDwelltime"], 
            tau_ns=mParametersReference["decayTime"], 
            max_frames=mParametersReference["nFrames"])
        time.sleep(.5)
        self.startStageScanning(mParametersStageScanning)

    def startStageScanning(self, mParametersStageScanning):
        try:
            #  start scanner 
            nStepsLine = mParametersStageScanning["nStepsLine"]
            dStepsLine = mParametersStageScanning["dStepsLine"]
            nTriggerLine = mParametersStageScanning["nTriggerLine"]
            nStepsPixel = mParametersStageScanning["nStepsPixel"]
            dStepsPixel = mParametersStageScanning["dStepsPixel"]
            nTriggerPixel = mParametersStageScanning["nTriggerPixel"]
            delayTimeStep = mParametersStageScanning["delayTimeStep"]
            nFrames = mParametersStageScanning["nFrames"]
            self.positioner.startStageScanning(nStepsLine, dStepsLine, nTriggerLine, nStepsPixel, dStepsPixel, nTriggerPixel, delayTimeStep, nFrames)
        except:
            pass
        
    def stop_reference(self):
        self.FLIMLabsC.stop_reference()
        try:
            self.positioner.stopStageScanning()
        except:
            pass
        
    def start_imaging(self):
        mParametersImaging = self._widget.getImagingParameters()
        mParametersStageScanning = self._widget.getStageScanningParameters()
        
        self.setFLIMLabsParameters(mParametersImaging)
        self.FLIMLabsC.start_imaging(
            max_frames=mParametersImaging["nFrames"])
        time.sleep(.5)
        self.startStageScanning(mParametersStageScanning)
        
    def stop_imaging(self):
        self.FLIMLabsC.stop_imaging()
        try:
            self.positioner.stopStageScanning()
        except:
            pass
        
    def setFLIMLabsParameters(self, mParameters):
        self.FLIMLabsC.setPixelX(mParameters["Npixel_x"])
        self.FLIMLabsC.setPixelY(mParameters["Npixel_y"])
        self.FLIMLabsC.setPixelOffsetLeft(mParameters["pixelOffsetLeft"])
        self.FLIMLabsC.setPixelOffsetRight(mParameters["pixelOffsetRight"])
        self.FLIMLabsC.setPixelOffsetTop(mParameters["pixelOffsetTop"])
        self.FLIMLabsC.setPixelOffsetBottom(mParameters["pixelOffsetBottom"])
        self.FLIMLabsC.setPixelSize(mParameters["pixelsize"])
        
        
            

class FLIMLabsREST:
    def __init__(self, firmware_selected="firmwares\\\\image_pattern_2.bit",
                 laser_period=10, 
                 channels=[True,False,False,False,False,False,False,False],
                 image_width=100,
                 image_height=100,
                    offset_bottom=0,
                      offset_left=0,
                        offset_right=0,
                          offset_top=0,
                            host_url="http://localhost", port=3030):
        self.firmware_selected = firmware_selected
        self.laser_period = laser_period
        self.image_width = image_width
        self.image_height = image_height
        self.offset_bottom = offset_bottom
        self.offset_left = offset_left
        self.offset_right = offset_right
        self.offset_top = offset_top
        self.base_url = host_url+":"+str(port)
        self.channels = [True,False,False,False,False,False,False,False]

    def make_request(self, payload, method='POST', path='/start', callback=None):
        url = self.base_url + path
        headers = {'Content-Type': 'application/json'}
        if method not in ['GET', 'HEAD']:
            try: response = requests.request(method, url, headers=headers, data=json.dumps(payload), timeout=1) #
            except: 
                print("Error: request timed out")
                return None 
        else:
            response = requests.request(method, url, headers=headers, timeout=1)

        if response.status_code == 200:
            data = response.json()
            if callback:
                callback(data)
            return data
        else:
            # Handle error response
            print(f"Error: {response.status_code}")
            return None

    def start_scouting(self, reconstruction="PLF", nFrames=1, dwell_time=1):
        path = "/start"
        payload = {
            "firmware": self.firmware_selected,
            "laser_period": self.laser_period,
            "experiment": {
                "type": "imaging",
                "params": {
                    "reconstruction": reconstruction,
                    "dwell_time": dwell_time,
                    "step": "scouting",
                    "image_width": self.image_width,
                    "image_height": self.image_height,
                    "offset_bottom": self.offset_bottom,
                    "offset_left": self.offset_left,
                    "offset_right": self.offset_right,
                    "offset_top": self.offset_top,
                    "channels": self.channels,
                    "max_frames": nFrames
                }
            }
        }
        self.make_request(payload=payload, path=path)

    def stop_scouting(self):
        path = "/stop"
        payload = {}
        self.make_request(payload=payload, path=path)

    def stop_reference(self):
        path = "/stop"
        payload = {}
        self.make_request(payload=payload, path=path)
        
    def start_calibration(self, reconstruction="PLF", dwell_time=1, harmonics=1, tau_ns=10, max_frames=10):
        payload = {
            "firmware": self.firmware_selected,
            "laser_period": self.laser_period,
            "experiment": {
                "type": "imaging",
                "params": {
                    "reconstruction": reconstruction,
                    "dwell_time": dwell_time,
                    "step": "calibration",
                    "image_width": self.image_width,
                    "image_height": self.image_height,
                    "offset_bottom": self.offset_bottom,
                    "offset_left": self.offset_left,
                    "offset_right": self.offset_right,
                    "offset_top": self.offset_top,
                    "channels": [i + 1 in self.channels for i in range(8)],
                    "harmonics": harmonics,
                    "tau_ns": tau_ns,
                    "max_frames": max_frames
                }
            }
        }
        self.make_request(payload)

    def start_imaging(self, reconstruction, dwell_time, max_frames):
        payload = {
            "firmware": self.firmware_selected,
            "laser_period": self.laser_period,
            "experiment": {
                "type": "imaging",
                "params": {
                    "reconstruction": reconstruction,
                    "dwell_time": dwell_time,
                    "step": "imaging",
                    "image_width": self.image_width,
                    "image_height": self.image_height,
                    "offset_bottom": self.offset_bottom,
                    "offset_left": self.offset_left,
                    "offset_right": self.offset_right,
                    "offset_top": self.offset_top,
                    "channels": [i + 1 in self.channels for i in range(8)],
                    "max_frames": max_frames
                }
            }
        }
        self.make_request(payload)
        
    
    def setPixelX(self, Npixel_X):
        self.image_width = Npixel_X
        
    def setPixelY(self, Npixel_Y):
        self.image_height = Npixel_Y
    
    def setPixelOffsetLeft(self, offset_left):
        self.offset_left = offset_left
    
    def setPixelOffsetRight(self, offset_right):
        self.offset_right = offset_right
        
    def setPixelOffsetTop(self, offset_top):
        self.offset_top = offset_top
        
    def setPixelOffsetBottom(self, offset_bottom):
        self.offset_bottom = offset_bottom
        
    def setPixelSize(self, pixelsize):
        self.pixelsize = pixelsize
    
    def checkCard(self):
        path = "/check"
        payload = {}
        data = self.make_request(payload=payload, path=path)
        if data["serial_number"]:
            print('Card found: ' + data["serial_number"])
            return True
        else:
            print('Check card error: ' + data["error"])
            return False

    def startLaserPeriodDetection(self):
        path = "/detect_laser_period"
        payload = {
            "experiment": {
                "type": "laser_period_detection",
            }
        }
        data = self.make_request(payload=payload, path=path)
        if data and data.status != 400:
            print('LASER PERIOD:', data)
            print('Laser period detected: ' + data.laser_period + 'ns, frequency: ' + data.frequency + 'MHz')
            self.laser_period = data.laser_period
            return True
        else:
            print(data)
            print('Laser period detection failed!', data.error)
            return False
        
        


if __name__ == '__main__':
    
    # Assuming FLIMLabsREST class is defined as shown previously

    # Create an instance with the required initialization parameters
    imaging_control = FLIMLabsREST(
        #firmware_selected="your_firmware",
        laser_period=12.5,  # example laser period
        #channels=[1, 2, 3],  # example channels
        image_width=100,
        image_height=100,
        offset_bottom=0,
        offset_left=0,
        offset_right=0,
        offset_top=0, 
        host_url="http://localhost"
    )
    
    imaging_control.start_scouting(
        dwell_time=1  # example dwell time
    )




    
# Copyright (C) 2020-2023 ImSwitch developers
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
