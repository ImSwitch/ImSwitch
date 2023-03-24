import json
import os
import threading

import numpy as np

from imswitch.imcommon.model import dirtools, initLogger
from ..basecontrollers import ImConWidgetController


class UC2ConfigController(ImConWidgetController):
    """Linked to UC2ConfigWidget."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__logger = initLogger(self)

        
        self.UC2ConfigDir = os.path.join(dirtools.UserFileDirs.Root, 'imcontrol_UC2Config')
        if not os.path.exists(self.UC2ConfigDir):
            os.makedirs(self.UC2ConfigDir)
        # get Updatemanager
        self.updater = self._master.UC2ConfigManager
        
        return
        # 1. load config from device
        self.mConfigDevice = self.loadConfigFromDevice()
        
        # 1a. switch-back to old configuration if device not valid
        if len(self.mConfigDevice)<4:
            self.mConfigDevice = self.loadDefaultConfigFromFile()
            self._widget.controlPanel.updateFirmwareDeviceLabel.setText("Something's wrong with the \n device/firmware, please reflash/reconnect!")

        # 1b. load default config if device not valid -> E.G. after flashing
        if "motorconfig" in self.mConfigDevice and self.mConfigDevice['motorconfig'][1]["enable"]==0: # the defaultconfig has not been written
            try:
                self.__logger.debug("Trying to load default config from file")
                self.mConfigDevice = self.loadDefaultConfigFromFile()
                self._master.UC2ConfigManager.setpinDef(self.mConfigDevice)
            except Exception as e:
                self.__logger.error(e)
        else:
            self.__logger.error("Device not connected?!")

        # 2. display device configs in the GUI  
        self.displayConfig(config=self.mConfigDevice)
        
        #here we should write the default pindef for uc2 standalone or esp32 standalone
        
        # save parameters on the disk
        self.defaultPinDefFile = "pinDef.json"
        
        self._widget.controlPanel.saveButton.clicked.connect(self.saveParams)
        self._widget.controlPanel.loadButton.clicked.connect(self.displayConfig)
        self._widget.controlPanel.updateFirmwareDeviceButton.clicked.connect(self.updateFirmware)
        self._widget.applyChangesButton.clicked.connect(self.applyParams)
        self._widget.reconnectButton.clicked.connect(self.reconnect)
        
        self.isFirmwareUpdating = False
        
    def loadConfigFromDevice(self):
        return self._master.UC2ConfigManager.loadPinDefDevice() 

    def loadDefaultConfigFromFile(self):
        return self._master.UC2ConfigManager.getDefaultConfig() 

    def loadConfigToDevice(self, config):
        pass

    def saveParams(self):
        UC2Config_info_dict = self.getInfoDict(self._widget.UC2ConfigParameterTree.p,
                                         self._widget.pinDefParameterTree.p)
        with open(os.path.join(self.UC2ConfigDir, self.defaultPinDefFile), 'w') as f:
            json.dump(UC2Config_info_dict, f, indent=4)
        
    def getInfoDict(self, generalParams=None, pinDefParams=None):
        state_general = None
        state_pinDef = None

        if generalParams is not None:
            # create dict for general params
            generalparamnames = ["radius", "sigma", "rotationAngle"]
            state_general = {generalparamname: float(
                generalParams.param("general").param(generalparamname).value()) for generalparamname
                             in generalparamnames}

        if pinDefParams is not None:
            # create dict for pinDefration params
            pinDefparamnames = pinDefParams.childs[0].names
            state_pinDef = {}
            for key in pinDefparamnames:
                state_pinDef[key] = int(pinDefParams.childs[0][key])

        info_dict = {
            "general": state_general,
            "pinDef": state_pinDef
        }
        return info_dict

    def displayConfig(self, config=None):
        if config is not None and config:
            state_general = None # TODO: Implement
            state_pinDef = config
        
        else: # TODO: Enabling sideloading the configuration? But ESP will be offline anyway..
            with open(os.path.join(self.UC2ConfigDir, self.defaultPinDefFile), 'rb') as f:
                UC2Config_info_dict = json.load(f)
                state_general = UC2Config_info_dict["general"]
                state_pinDef = UC2Config_info_dict["pinDef"]
        self.setParamTree(state_general=state_general, state_pinDef=state_pinDef)
        #self._master.UC2ConfigManager.setGeneral(state_general)
    
    def updateFirmware(self, filename=None):
        if not(self.isFirmwareUpdating):
            self._widget.controlPanel.updateFirmwareDeviceButton.setEnabled(False)
            threading.Thread(target=self.updateFirmwareThread, args=(filename,)).start()
            self.isFirmwareUpdating = True
        
    def updateFirmwareThread(self, filename=None):
        # 1. download firmware
        self._widget.controlPanel.updateFirmwareDeviceLabel.setText('Downloading firmware...')
        FWdownloaded = self._master.UC2ConfigManager.downloadFirmware(filename)
        
        # 2.1 close serial connection
        
        # 2.2 flash firmware
        if FWdownloaded:
            self._widget.controlPanel.updateFirmwareDeviceLabel.setText('Flashing firmware...')
            FWflashed = self._master.UC2ConfigManager.flashFirmware()
        else:
            self._widget.controlPanel.updateFirmwareDeviceLabel.setText('Firmware not downloaded.')
            return
        
        
        # 3. delete firmware
        if FWflashed:
            self._widget.controlPanel.updateFirmwareDeviceLabel.setText('Deleting firmware...')
            self._master.UC2ConfigManager.removeFirmware()
        else:
            self._master.UC2ConfigManager.removeFirmware()
            self._widget.controlPanel.updateFirmwareDeviceLabel.setText('Firmware not flashed.')
            return
        
        self._widget.controlPanel.updateFirmwareDeviceLabel.setText('Firmware was flashed.')
            
        # 4. reestablish serial connection
        self._master.UC2ConfigManager.initSerial()
        self.isFirmwareUpdating = False
        
        # 5. re-write config to device
        self.mConfigDevice = self.loadDefaultConfigFromFile()
        self._master.UC2ConfigManager.setpinDef(self.mConfigDevice)
        
        self._widget.controlPanel.updateFirmwareDeviceButton.setEnabled(True)
        
    def removeFirmware(self, firmwarePath):
        return self.firmwareUpdater.removeFirmware()

    def setParamTree(self, state_general, state_pinDef):
        generalParams = self._widget.UC2ConfigParameterTree.p
        pinDefParams = self._widget.pinDefParameterTree.p

        if pinDefParams is not None:
            # create dict for pinDefration params
            pinDefparamnames = pinDefParams.childs[0].names
            # assign values to the MCU pin definition
            esp32pindef = self.espToPinDefParanames(state_pinDef)

            # assign values to GUI
            for key in pinDefparamnames:
                try:
                    pinDefParams.childs[0].param(key).setValue(esp32pindef[key])
                except KeyError:
                    pass

            # assign values to
            
    def espToPinDefParanames(self, espPinDef):
        # this comes from the former description of the pinDef
        pinDefparamnames = {}
        pinDefparamnames['motXstp'] = espPinDef['motorconfig'][1]['step']
        pinDefparamnames['motXdir'] = espPinDef['motorconfig'][1]['dir']
        pinDefparamnames['motYstp'] = espPinDef['motorconfig'][2]['step']
        pinDefparamnames['motYdir'] = espPinDef['motorconfig'][2]['dir']
        pinDefparamnames['motZstp'] = espPinDef['motorconfig'][3]['step']
        pinDefparamnames['motZdir'] = espPinDef['motorconfig'][3]['dir']
        pinDefparamnames['motAstp'] = espPinDef['motorconfig'][0]['step']
        pinDefparamnames['motAdir'] = espPinDef['motorconfig'][3]['dir']
        pinDefparamnames['motEnable'] = espPinDef['motorconfig'][0]['enable']
        pinDefparamnames['ledArrPin'] = espPinDef['ledconfig']['ledArrPin']
        pinDefparamnames['ledArrNum'] = espPinDef['ledconfig']['ledArrNum']
        pinDefparamnames['digitalPin1'] = 0
        pinDefparamnames['digitalPin2'] = 0
        pinDefparamnames['digitalPin3'] = 0
        pinDefparamnames['analogPin1'] = 0
        pinDefparamnames['analogPin2'] = 0
        pinDefparamnames['analogPin3'] = 0
        pinDefparamnames['laserPin1'] = espPinDef["laserconfig"]["LASER1pin"]
        pinDefparamnames['laserPin2'] = espPinDef["laserconfig"]["LASER2pin"]
        pinDefparamnames['laserPin3'] = espPinDef["laserconfig"]["LASER3pin"]
        pinDefparamnames['dacFake1'] = 0
        pinDefparamnames['dacFake2'] = 0
        return pinDefparamnames
    
    
    def pinDefParanamesToEsp(self, pinDefparamnames):
        # this comes from the former description of the pinDef
        espPinDef = {
                "motorconfig":[
                    {
                        "stepperid":0,
                        "dir":pinDefparamnames['motAdir'],
                        "step":pinDefparamnames['motAstp'],
                        "enable":pinDefparamnames['motEnable'],
                    },
                    {
                        "stepperid":1,
                        "dir":pinDefparamnames['motXdir'],
                        "step":pinDefparamnames['motXstp'],
                        "enable":pinDefparamnames['motEnable'],
                    },
                    {
                        "stepperid":2,
                        "dir":pinDefparamnames['motYdir'],
                        "step":pinDefparamnames['motYstp'],
                        "enable":pinDefparamnames['motEnable'],
                    },
                    {
                        "dir":pinDefparamnames['motZdir'],
                        "step":pinDefparamnames['motZstp'],
                        "enable":pinDefparamnames['motEnable'],
                    }
                ],
                "ledconfig":{
                    "ledArrNum":pinDefparamnames['ledArrNum'],
                    "ledArrPin":pinDefparamnames['ledArrPin'],
                },
                "laserconfig":{
                    "LASER1pin":pinDefparamnames['laserPin1'],
                    "LASER2pin":pinDefparamnames['laserPin2'],
                    "LASER3pin":pinDefparamnames['laserPin3']
                },
                "stateconfig":{
                    "identifier_name":"UC2_Feather",
                    "identifier_id":"V1.2",
                    "identifier_date":"Nov  7 202212:52:14",
                    "identifier_author":"BD",
                    "IDENTIFIER_NAME":""
                }
                }
        return espPinDef
        

    def applyParams(self):
        UC2Config_info_dict = self.getInfoDict(generalParams=self._widget.UC2ConfigParameterTree.p,
                                         pinDefParams=self._widget.pinDefParameterTree.p)
        self.mConfigOffline = UC2Config_info_dict["pinDef"]
        shared_items = self._master.UC2ConfigManager.setpinDef(self.pinDefParanamesToEsp(self.mConfigOffline))
        self._widget.controlPanel.updateFirmwareDeviceLabel.setText("Updated items: "+str(len(shared_items))+"/"+str(len(self.pinDefParanamesToEsp(self.mConfigOffline))))
        self._logger.debug('Apply changes to pinDef.')

    def reconnect(self):
        self._logger.debug('Reconnecting to ESP32 device.')
        self._widget.controlPanel.updateFirmwareDeviceLabel.setText("Reconnecting to ESP32 device.")
        mThread = threading.Thread(target=self._master.UC2ConfigManager.initSerial)
        mThread.start()
        mThread.join()
        self._widget.controlPanel.updateFirmwareDeviceLabel.setText("We are connected: "+str(self._master.UC2ConfigManager.isConnected()))
        
        


# Copyright (C) 2020-2021 ImSwitch developers
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
