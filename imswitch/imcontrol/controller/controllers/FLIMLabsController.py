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

try:
    import websocket # pip install websocket-client
    isFLIMLABS = True
except:
    isFLIMLABS = False
import struct
import threading
import time





class FLIMLabsController(LiveUpdatedController):
    """ Linked to FLIMLabsWidget."""

    sigImageReceived = Signal()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._logger = initLogger(self, tryInheritParent=False)
        if not isFLIMLABS:
            return
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
    
        # start the data receiving thread
        self.FLIMLabsSocket = WebSocketClient()
        self.FLIMLabsSocket.connect()

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
    
    
class WebSocketClient:
    def __init__(self, url='ws://localhost:3030/data', reconnect_interval=5):
        self.url = url
        self.reconnect_interval = reconnect_interval
        self.socket = None
        self.error_mode = False

    def connect(self):
        def on_message(ws, message):
            if self.error_mode:
                return
            binary_data = bytearray(message)
            for msg in self.deserialize_binary_message(binary_data):
                self.process_message(msg)

        def on_error(ws, error):
            print('WebSocket error:', error)
            self.error_mode = True
            ws.close()

        def on_close(ws, close_status_code, close_msg):
            print('WebSocket closed with code:', close_status_code)
            time.sleep(self.reconnect_interval)
            self.connect()

        def on_open(ws):
            print('WebSocket connected')

        self.socket = websocket.WebSocketApp(self.url,
                                             on_open=on_open,
                                             on_message=on_message,
                                             on_error=on_error,
                                             on_close=on_close)
        wst = threading.Thread(target=self.socket.run_forever)
        wst.daemon = True
        wst.start()

    def deserialize_binary_message(self, binary_data):
        messages = []
        y = 0
        while y < len(binary_data) - 1:
            message_type = binary_data[y]
            y += 1
            if message_type == 0:
                # LineData
                frame, line, channel, data_length = struct.unpack_from('<IIII', binary_data, y)
                y += 16
                data = struct.unpack_from('<' + 'I' * data_length, binary_data, y)
                y += data_length * 4
                messages.append(LineData(frame, line, channel, data))
            elif message_type == 1:
                # CurveData
                frame, channel, data_length = struct.unpack_from('<III', binary_data, y)
                y += 12
                data = struct.unpack_from('<' + 'I' * data_length, binary_data, y)
                y += data_length * 4
                messages.append(CurveData(frame, channel, data))
            elif message_type == 2:
                # CalibrationData
                frame, channel, harmonic = struct.unpack_from('<III', binary_data, y)
                y += 12
                phase, modulation = struct.unpack_from('<dd', binary_data, y)
                y += 16
                messages.append(CalibrationData(frame, channel, harmonic, phase, modulation))
            elif message_type == 3:
                # PhasorData
                frame, channel, harmonic, g_data_rows, g_data_row_length = struct.unpack_from('<IIIII', binary_data, y)
                y += 20
                g_data = []
                for _ in range(g_data_rows):
                    g_row = struct.unpack_from('<' + 'd' * g_data_row_length, binary_data, y)
                    g_data.append(g_row)
                    y += g_data_row_length * 8
                s_data_rows, s_data_row_length = struct.unpack_from('<II', binary_data, y)
                y += 8
                s_data = []
                for _ in range(s_data_rows):
                    s_row = struct.unpack_from('<' + 'd' * s_data_row_length, binary_data, y)
                    s_data.append(s_row)
                    y += s_data_row_length * 8
                messages.append(PhasorData(frame, channel, harmonic, g_data, s_data))
            elif message_type == 4:
                # ImagingExperimentEndData
                string_length = struct.unpack_from('<I', binary_data, y)[0]
                y += 4
                if string_length == 0:
                    intensity_file = None
                else:
                    intensity_file = binary_data[y:y+string_length].decode('utf-8')
                    y += string_length
                messages.append(ImagingExperimentEndData(intensity_file))
            else:
                self.error_mode = True
                print('Received unknown message type!!')
        return messages

    def process_message(self, msg):
        if isinstance(msg, LineData):
            self.process_line_data(msg)
        elif isinstance(msg, CurveData):
            self.process_curve_data(msg)
        elif isinstance(msg, CalibrationData):
            self.process_calibration_data(msg)
        elif isinstance(msg, PhasorData):
            self.process_phasor_data(msg)
        elif isinstance(msg, ImagingExperimentEndData):
            self.process_imaging_experiment_end_data(msg)

    def process_line_data(self, msg):
        # Implement your logic for LineData here
        print("Received LineData:", msg.frame, msg.line, msg.channel, msg.data)
        pass

    def process_curve_data(self, msg):
        # Implement your logic for CurveData here
        print("Received CurveData:", msg.frame, msg.channel, msg.data)
        pass

    def process_calibration_data(self, msg):
        # Implement your logic for CalibrationData here
        print("Received CalibrationData:", msg.frame, msg.channel, msg.harmonic, msg.phase, msg.modulation)
        pass

    def process_phasor_data(self, msg):
        # Implement your logic for PhasorData here
        print("Received PhasorData:", msg.frame, msg.channel, msg.harmonic, msg.g_data, msg.s_data)
        pass

    def process_imaging_experiment_end_data(self, msg):
        # Implement your logic for ImagingExperimentEndData here
        # Example: print("Experiment ended, intensity file:", msg.intensity_file)
        print("Experiment ended, intensity file:", msg.intensity_file)
        pass
class LineData:
    def __init__(self, frame, line, channel, data):
        self.frame = frame
        self.line = line
        self.channel = channel
        self.data = data

class CurveData:
    def __init__(self, frame, channel, data):
        self.frame = frame
        self.channel = channel
        self.data = data

class CalibrationData:
    def __init__(self, frame, channel, harmonic, phase, modulation):
        self.frame = frame
        self.channel = channel
        self.harmonic = harmonic
        self.phase = phase
        self.modulation = modulation

class PhasorData:
    def __init__(self, frame, channel, harmonic, g_data, s_data):
        self.frame = frame
        self.channel = channel
        self.harmonic = harmonic
        self.g_data = g_data
        self.s_data = s_data

class ImagingExperimentEndData:
    def __init__(self, intensity_file):
        self.intensity_file = intensity_file






    
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
