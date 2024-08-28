import clr
import time
import os
from .LaserManager import LaserManager
from imswitch.imcommon.model import initLogger

# Ajouter les chemins complets vers les assemblées Thorlabs
clr.AddReference("C:\\Program Files\\Thorlabs\\Kinesis\\Thorlabs.MotionControl.DeviceManagerCLI.dll")
clr.AddReference("C:\\Program Files\\Thorlabs\\Kinesis\\Thorlabs.MotionControl.GenericMotorCLI.dll")
clr.AddReference("C:\\Program Files\\Thorlabs\\Kinesis\\Thorlabs.MotionControl.KCube.SolenoidCLI.dll")
clr.AddReference("C:\\Program Files\\Thorlabs\\Kinesis\\Thorlabs.MotionControl.KCube.DCServoCLI.dll")

from Thorlabs.MotionControl.DeviceManagerCLI import DeviceManagerCLI
from Thorlabs.MotionControl.GenericMotorCLI import GenericMotorCLI
from Thorlabs.MotionControl.KCube.SolenoidCLI import KCubeSolenoid, SolenoidStatus
from Thorlabs.MotionControl.KCube.DCServoCLI import KCubeDCServo

class ThorlabsMockLaserManager(LaserManager):
    """ LaserManager for analog-value NI-DAQ-controlled lasers.
    Manager properties:
    - "serial_no_shutter": serial number of the Thorlabs shutter
    - "serial_no_rotator": serial number of the motorized rotation half waveplate use to adjust laser power
    """

    def __init__(self, laserInfo, name, **lowLevelManagers):
        self.__logger = initLogger(self, tryInheritParent=True)
        super().__init__(laserInfo, name, isBinary=False, valueUnits='mW',
                         valueDecimals=0)  # Appel du constructeur de la classe de base
        
        # Initialize Thorlabs shutter
        self._shutter_serial_no = laserInfo.managerProperties['serial_no_shutter']
        self._motor_serial_no = laserInfo.managerProperties['serial_no_rotator']
        self.shutter_device = None
        self.motor_device = None
      
        #Build device list
        try:
            DeviceManagerCLI.BuildDeviceList()

        except Exception as e:
            self.__logger.error(f"Failed to built device list: {e}")
  
        # Initialize the shutter thorlabs Kinesis
        try:       
            self.shutter_device = KCubeSolenoid.CreateKCubeSolenoid(self._shutter_serial_no)
            # Ouvrir la connexion aux dispositifs
            self.shutter_device.Connect(self._shutter_serial_no)
            # Se connecter au KDC101 via son numéro de série
            
            if not self.shutter_device.IsSettingsInitialized():
                self.shutter_device.WaitForSettingsInitialized(10000)  # Timeout de 10 secondes
                assert self.shutter_device.IsSettingsInitialized() is True
            
            self.shutter_device.StartPolling(250)  # 250ms polling rate
            time.sleep(0.25)
            self.shutter_device.EnableDevice()
            time.sleep(0.5)  # Attendre que le dispositif soit activé
          
            self.shutter_device.SetOperatingMode(SolenoidStatus.OperatingModes.Manual)
            #self.__logger.info(f"Shutter {self._shutter_serial_no} initialized successfully.")

        except Exception as e:
            self.__logger.error(f"Failed to initialize Thorlabs shutter: {e}")
        
        # Initialize the Thorlabs rotation mount
        try:  
            self.motor_device = KCubeDCServo.CreateKCubeDCServo(self._motor_serial_no)
            # Ouvrir la connexion aux dispositifs
            self.motor_device.Connect(self._motor_serial_no)
            # Se connecter au KDC101 via son numéro de série
            if not self.motor_device.IsSettingsInitialized():
                self.motor_device.WaitForSettingsInitialized(10000)  # Timeout de 10 secondes
                assert self.motor_device.IsSettingsInitialized() is True

            self.motor_device.StartPolling(250)  # 250ms polling rate
            time.sleep(0.25)            
            self.motor_device.EnableDevice()
            time.sleep(0.5)  # Attendre que le dispositif soit activé
          
            #self.shutter_device.SetOperatingMode(SolenoidStatus.OperatingModes.Manual)
            self.__logger.info(f"Rotator {self._motor_serial_no} initialized successfully.")

            # Référencer la position de la monture (home)
            self.motor_device.Home(60000)  # Timeout en ms
            print(dir(self.motor_device))

            self.motor_device.MoveTo(10, 60000)
            self.motor_device.MoveTo_DeviceUnit(10, 60000)
            #print(self.motor_device.GetMoveAbsolutePosition())

            #RequestMoveAbsolutePosition
            #SetMoveAbsolutePosition

            #while self.motor_device.Status.IsHoming:
            #    time.sleep(0.1)

            #self.shutter_device.EnableDevice()
            #time.sleep(0.5)  # Attendre que le dispositif soit activé

        except Exception as e:
            self.__logger.error(f"Failed to initialize Thorlabs rotator: {e}")

    def setEnabled(self, enabled):
        try:
            if self.shutter_device:
                if enabled:
                    self.shutter_device.SetOperatingState(SolenoidStatus.OperatingStates.Active)  # Ouvrir l'obturateur
                    self.__logger.info("Shutter enabled.")
                else:
                    self.shutter_device.SetOperatingState(SolenoidStatus.OperatingStates.Inactive)  # Fermer l'obturateur
                    self.__logger.info("Shutter disabled.")
            else:
                self.__logger.error("Shutter device is not initialized.")
        except Exception as e:
            self.__logger.error(f"Error trying to enable/disable shutter: {e}")

    def setValue(self, target_position):
        if self.isBinary:
            return
        try:
            if self.motor_device:
                #print(self.motor_device.Status.IsError)
                self.motor_device.MoveTo(target_position, 60000)
                #self.motor_device.MoveTo(target_position, 60000)
                # Attendre que la monture atteigne la position cible
                while self.motor_device.Status.IsMoving:
                    time.sleep(0.1)
                self.__logger.info(f"Rotator moved to position {target_position}.")
            else:
                self.__logger.error("Rotator device is not initialized.")
            #self._nidaqManager.setAnalog(target=self.name, voltage=voltage,
            # min_val=self.valueRangeMin, max_val=self.valueRangeMax            )
        except:
            self.__logger.error(f"Error trying to position the rotator: {self._motor_serial_no}.")
    
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
        #◙ Stop polling and clean clean up resources when done
        try:
            if self.shutter_device:
                self.shutter_device.StopPolling()
                self.shutter_device.Disconnect()
                self.__logger.info("Shutter device disconnected.")
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
