import clr
import os
from .LaserManager import LaserManager
from imswitch.imcommon.model import initLogger


# import sys
# import time

# Ajouter les chemins complets vers les assemblées Thorlabs
clr.AddReference("C:\\Program Files\\Thorlabs\\Kinesis\\Thorlabs.MotionControl.DeviceManagerCLI.dll")
#clr.AddReference("C:\\Program Files\\Thorlabs\\Kinesis\\Thorlabs.MotionControl.GenericMotorCLI.dll")
clr.AddReference("C:\\Program Files\\Thorlabs\\Kinesis\\Thorlabs.MotionControl.KCube.SolenoidCLI.dll")

from Thorlabs.MotionControl.DeviceManagerCLI import DeviceManagerCLI
#from Thorlabs.MotionControl.GenericMotorCLI import GenericMotorCLI
from Thorlabs.MotionControl.KCube.SolenoidCLI import KCubeSolenoid, SolenoidStatus
#from System import Decimal  # nécessaire pour les unités du monde réel

class ThorlabsMockLaserManager(LaserManager):
    """ LaserManager for analog-value NI-DAQ-controlled lasers.
    Manager properties: "serial_no"
    """

    def __init__(self, laserInfo, name, **lowLevelManagers):
        self.__logger = initLogger(self, tryInheritParent=True)
        super().__init__(laserInfo, name, isBinary=True, valueUnits='V', valueDecimals=2)  # Appel du constructeur de la classe de base
        # self.serial_no = "68800404"  # Remplacez cette ligne par le numéro de série de votre appareil
        # Initialize Thorlabs shutter
        self._shutter_serial_no = laserInfo.managerProperties['serial_no']
        self.device = None
        # Initialisation de l'API Thorlabs Kinesis
        try:
            DeviceManagerCLI.BuildDeviceList()

            # Liste des dispositifs connectés          
            self.device = KCubeSolenoid.CreateKCubeSolenoid(self._shutter_serial_no)
            self.device.Connect(self._shutter_serial_no)
            
            if not self.device.IsSettingsInitialized():
                self.device.WaitForSettingsInitialized(10000)  # Timeout de 10 secondes
                assert self.device.IsSettingsInitialized() is True
            
            self.device.StartPolling(250)  # 250ms polling rate
            #time.sleep(0.25)
            self.device.EnableDevice()
            #time.sleep(0.5)  # Attendre que le dispositif soit activé
          
            self.device.SetOperatingMode(SolenoidStatus.OperatingModes.Manual)
            self.__logger.info(f"Shutter {self._shutter_serial_no} initialized successfully.")

        except Exception as e:
            self.__logger.error(f"Failed to initialize Thorlabs shutter: {e}")
         
    def setEnabled(self, enabled):
        try:
            if self.device:
                if enabled:
                    self.device.SetOperatingState(SolenoidStatus.OperatingStates.Active)  # Ouvrir l'obturateur
                    self.__logger.info("Shutter enabled.")
                else:
                    self.device.SetOperatingState(SolenoidStatus.OperatingStates.Inactive)  # Fermer l'obturateur
                    self.__logger.info("Shutter disabled.")
            else:
                self.__logger.error("Shutter device is not initialized.")
        except Exception as e:
            self.__logger.error(f"Error trying to enable/disable shutter: {e}")

    def setValue(self, voltage):
        if self.isBinary:
            return
        try:
            self._nidaqManager.setAnalog(
                target=self.name, voltage=voltage,
                min_val=self.valueRangeMin, max_val=self.valueRangeMax
            )
        except:
            self.__logger.error("Error trying to set value to laser.")
    
    def setScanModeActive(self, active):
        try:
            if active:
                self.setEnabled(True)  # Fermer le shutter lorsqu'on entre en mode scan
                self.__logger.info("Scan mode activated, shutter closed.")
            else:
                self.setEnabled(False)  # Optionnel : ouvrir le shutter lorsque le mode scan est désactivé
                self.__logger.info("Scan mode deactivated, shutter opened.")
        except Exception as e:
            self.__logger.error(f"Error in setting scan mode active: {e}")


    def close(self):
        #◙ Clean up resources when done
        try:
            if self.device:
                self.device.StopPolling()
                self.device.Disconnect()
                self.__logger.info("Shutter device disconnected.")
        except Exception as e:
            self.__logger.error(f"Failed to close shutter device: {e}")


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
