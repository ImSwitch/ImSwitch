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
            
        # load config from device
        self.mConfigDevice = self.loadConfigFromDevice()
        # switch-back to old configuration
        if len(self.mConfigDevice)<4:
            self.mConfigDevice = self.loadDefaultConfig()
            self._widget.controlPanel.updateFirmwareDeviceLabel.setText("Something's wrong with the \n device/firmware, please reflash/reconnect!")
        
        # display device configs
        self.loadParams(config=self.mConfigDevice)
        
        # save parameters on the disk
        self.defaultPinDefFile = "pinDef.json"
        
        self._widget.controlPanel.saveButton.clicked.connect(self.saveParams)
        self._widget.controlPanel.loadButton.clicked.connect(self.loadParams)
        self._widget.controlPanel.updateFirmwareDeviceButton.clicked.connect(self.updateFirmware)
        self._widget.applyChangesButton.clicked.connect(self.applyParams)
        
        self.isFirmwareUpdating = False
        
    def loadConfigFromDevice(self):
        return self._master.UC2ConfigManager.loadPinDefDevice() 

    def loadDefaultConfig(self):
        return self._master.UC2ConfigManager.loadDefaultConfig()

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

    def loadParams(self, config=None):
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
        self._widget.controlPanel.updateFirmwareDeviceButton.setEnabled(True)
        
    def removeFirmware(self, firmwarePath):
        return self.firmwareUpdater.removeFirmware()

    def setParamTree(self, state_general, state_pinDef):
        generalParams = self._widget.UC2ConfigParameterTree.p
        pinDefParams = self._widget.pinDefParameterTree.p

        if pinDefParams is not None:
            # create dict for pinDefration params
            pinDefparamnames = pinDefParams.childs[0].names
            for key in pinDefparamnames:
                try:
                    pinDefParams.childs[0].param(key).setValue(state_pinDef[key])
                except KeyError:
                    pass


    def applyParams(self):
        UC2Config_info_dict = self.getInfoDict(generalParams=self._widget.UC2ConfigParameterTree.p,
                                         pinDefParams=self._widget.pinDefParameterTree.p)
        #self.applyGeneral(UC2Config_info_dict["general"])
        self.mConfigOffline = UC2Config_info_dict["pinDef"]
        self.applypinDef(self.mConfigOffline)

    def applyGeneral(self, info_dict):
        self._master.UC2ConfigManager.setGeneral(info_dict)
        image = self._master.UC2ConfigManager.update(maskChange=True)
        self.updateDisplayImage(image)
        # self._logger.debug('Apply changes to general UC2Config mask parameters.')

    def applypinDef(self, info_dict):
        shared_items = self._master.UC2ConfigManager.setpinDef(info_dict)
        self._widget.controlPanel.updateFirmwareDeviceLabel.setText("Udated items: "+str(len(shared_items))+"/"+str(len(info_dict)))
        self._logger.debug('Apply changes to pinDef.')



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
