import numpy as np
from threading import Thread
import requests
import json


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

        # Connect FLIMLabsWidget signals
        if not imswitch.IS_HEADLESS:
            # Connect CommunicationChannel signals
            '''
            self._commChannel.sigUpdateImage.connect(self.update)
            self._widget.sigSnapClicked.connect(self.snapImageFlowCam)
            self._widget.sigSliderFocusValueChanged.connect(self.changeFocus)
            self._widget.sigSliderPumpSpeedValueChanged.connect(self.changePumpSpeed)
            self._widget.sigExposureTimeChanged.connect(self.changeExposureTime)
            self._widget.sigGainChanged.connect(self.changeGain)
            self._widget.sigPumpDirectionToggled.connect(self.changePumpDirection)


            # Connect buttons
            self._widget.buttonStart.clicked.connect(self.startFLIMLabsExperimentByButton)
            self._widget.buttonStop.clicked.connect(self.stopFLIMLabsExperimentByButton)
            self._widget.pumpMovePosButton.clicked.connect(self.movePumpPos)
            self._widget.pumpMoveNegButton.clicked.connect(self.movePumpNeg)
            # start measurment thread (pressure)
            '''
            

class FLIMLabsREST:
    def __init__(self, firmware_selected, laser_period, channels, firmware_width, firmware_height, offset_bottom, offset_left, offset_right, offset_top, host_url="http://localhost", port=3030):
        self.firmware_selected = firmware_selected
        self.laser_period = laser_period
        self.channels = channels
        self.firmware_width = firmware_width
        self.firmware_height = firmware_height
        self.offset_bottom = offset_bottom
        self.offset_left = offset_left
        self.offset_right = offset_right
        self.offset_top = offset_top
        self.base_url = host_url+":"+str(port)

    def make_request(self, payload, method='POST', path='/start', callback=None):
        url = self.base_url + path
        headers = {'Content-Type': 'application/json'}

        if method not in ['GET', 'HEAD']:
            response = requests.request(method, url, headers=headers, data=json.dumps(payload))
        else:
            response = requests.request(method, url, headers=headers)

        if response.status_code == 200:
            data = response.json()
            if callback:
                callback(data)
            return data
        else:
            # Handle error response
            print(f"Error: {response.status_code}")
            return None

    def start_scouting(self, reconstruction, dwell_time):
        payload = {
            "firmware": self.firmware_selected,
            "laser_period": self.laser_period,
            "experiment": {
                "type": "imaging",
                "params": {
                    "reconstruction": reconstruction,
                    "dwell_time": dwell_time,
                    "step": "scouting",
                    "image_width": self.firmware_width,
                    "image_height": self.firmware_height,
                    "offset_bottom": self.offset_bottom,
                    "offset_left": self.offset_left,
                    "offset_right": self.offset_right,
                    "offset_top": self.offset_top,
                    "channels": [i + 1 in self.channels for i in range(8)]
                }
            }
        }
        self.make_request(payload)

    def start_calibration(self, reconstruction, dwell_time, harmonics, tau_ns, max_frames):
        payload = {
            "firmware": self.firmware_selected,
            "laser_period": self.laser_period,
            "experiment": {
                "type": "imaging",
                "params": {
                    "reconstruction": reconstruction,
                    "dwell_time": dwell_time,
                    "step": "calibration",
                    "image_width": self.firmware_width,
                    "image_height": self.firmware_height,
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

    def start_imaging(self, reconstruction, dwell_time, max_frames, calibration_offsets):
        payload = {
            "firmware": self.firmware_selected,
            "laser_period": self.laser_period,
            "experiment": {
                "type": "imaging",
                "params": {
                    "reconstruction": reconstruction,
                    "dwell_time": dwell_time,
                    "step": "imaging",
                    "image_width": self.firmware_width,
                    "image_height": self.firmware_height,
                    "offset_bottom": self.offset_bottom,
                    "offset_left": self.offset_left,
                    "offset_right": self.offset_right,
                    "offset_top": self.offset_top,
                    "channels": [i + 1 in self.channels for i in range(8)],
                    "max_frames": max_frames,
                    "calibration_offsets": calibration_offsets
                }
            }
        }
        self.make_request(payload)


if __name__ == '__main__':
    
    # Assuming FLIMLabsREST class is defined as shown previously

    # Create an instance with the required initialization parameters
    imaging_control = FLIMLabsREST(
        firmware_selected="your_firmware",
        laser_period=123,  # example laser period
        channels=[1, 2, 3],  # example channels
        firmware_width=800,
        firmware_height=600,
        offset_bottom=10,
        offset_left=10,
        offset_right=10,
        offset_top=10, 
        host_url="http://192.168.178.60"
    )
    
    imaging_control.start_calibration(
        reconstruction="some_reconstruction_value",
        dwell_time=500,  # example dwell time
        harmonics="some_harmonics_value",
        tau_ns=50,  # example tau value
        max_frames=1000  # example max frames
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
