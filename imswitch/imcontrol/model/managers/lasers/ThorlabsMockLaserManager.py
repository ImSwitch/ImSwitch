import clr
import time
import sys
import inspect
#import os
from .LaserManager import LaserManager
from imswitch.imcommon.model import initLogger

# Ajouter le chemin vers les DLLs .NET de Thorlabs
dll_path = 'C:\\Program Files\\Thorlabs\\Kinesis'

# Charger les DLL nécessaires
clr.AddReference(f"{dll_path}\\Thorlabs.MotionControl.DeviceManagerCLI.dll")
clr.AddReference(f"{dll_path}\\Thorlabs.MotionControl.KCube.DCServoCLI.dll")

#clr.AddReference("C:\\Program Files\\Thorlabs\\Kinesis\\Thorlabs.MotionControl.GenericMotorCLI.dll")


# Ajouter les chemins complets vers les assemblées Thorlabs
from Thorlabs.MotionControl.DeviceManagerCLI import DeviceManagerCLI
from Thorlabs.MotionControl.KCube.DCServoCLI import KCubeDCServo

class ThorlabsMockLaserManager(LaserManager):
    """ LaserManager for analog-value NI-DAQ-controlled lasers.
    Manager properties:
    - "serial_no_rotator": serial number of the motorized rotation half waveplate use to adjust laser power
    - "conversion_factor": rotator conversion from ° to motor count
    - "velocity": speed of the rotator
    """

    def __init__(self, laserInfo, name, **lowLevelManagers):
        self.__logger = initLogger(self, tryInheritParent=True)
        super().__init__(laserInfo, name, isBinary=False, valueUnits='mW',
                         valueDecimals=0)  # Appel du constructeur de la classe de base
        
        # Initialize Thorlabs shutter
        self._motor_serial_no = laserInfo.managerProperties['serial_no_rotator']
        self._conversion_factor = float(laserInfo.managerProperties['conversion_factor'])
        self._velocity = laserInfo.managerProperties['velocity']
        self.shutter_device = None
        self.motor_device = None
      
        #Build device list
        try:
            DeviceManagerCLI.BuildDeviceList()

        except Exception as e:
            self.__logger.error(f"Failed to built device list: {e}")
        
        # Initialize the Thorlabs rotation mount
        try:  
            # Ouvrir la connexion aux dispositifs
            self.motor_device = KCubeDCServo.CreateKCubeDCServo(self._motor_serial_no)           
            # Se connecter au KDC101 via son numéro de série
            self.motor_device.Connect(self._motor_serial_no)
            if not self.motor_device.IsSettingsInitialized():
                self.motor_device.WaitForSettingsInitialized(5000)  # Timeout de 10 secondes

            # Activer le contrôle
            self.motor_device.StartPolling(250)  # 250ms polling rate
            #time.sleep(0.25)            
            self.motor_device.EnableDevice()
            time.sleep(0.5)  # Attendre que le dispositif soit activé
   
            # Référencer la position de la monture (home)
            self.motor_device.Home(60000)  # Timeout en millisecondes

        except Exception as e:
            self.__logger.error(f"Failed to initialize Thorlabs rotator: {e}")

    def setEnabled(self, enabled):
        pass

    def setValue(self, target_position_deg):
        if self.isBinary:
            return
        try:
            if self.motor_device:
                try:
                    #conversion_factor = 1919.14
                    target_position = int(target_position_deg * self._conversion_factor)
                    self.motor_device.MoveTo_DeviceUnit(target_position, 60000)
                    # Attendre que la monture atteigne la position cible
                    while self.motor_device.Status.IsMoving:
                        time.sleep(0.1)
                except Exception as e:
                    print(f"An error occurred: {e}")

            else:
                self.__logger.error("Rotator device is not initialized.")
        except:
            self.__logger.error(f"Error trying to position the rotator: {self._motor_serial_no}.")


    def close(self):
        #◙ Stop polling and clean clean up resources when done
        try:
            if self.motor_device:
                self.motor_device.StopPolling()
                self.motor_device.Disconnect()
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
