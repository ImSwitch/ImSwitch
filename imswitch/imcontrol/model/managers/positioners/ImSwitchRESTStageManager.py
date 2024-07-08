from imswitch.imcommon.model import initLogger
from .PositionerManager import PositionerManager
import time
import numpy as np

MAX_ACCEL = 500000
PHYS_FACTOR = 1
gTIMEOUT = 100

from imswitch.imcommon.model import initLogger
from .PositionerManager import PositionerManager
import time
import numpy as np
from imswitch.imcommon.model import APIExport, generateAPI, initLogger
import threading

MAX_ACCEL = 500000
PHYS_FACTOR = 1
gTIMEOUT = 100

class ImSwitchREST(PositionerManager):
    def __init__(self, positionerInfo, name, **lowLevelManagers):
        super().__init__(positionerInfo, name, initialPosition={axis: 0 for axis in positionerInfo.axes})
        self._rs232manager = lowLevelManagers['rs232sManager'][positionerInfo.managerProperties['rs232device']]
        self._commChannel = lowLevelManagers['commChannel']
        self.__logger = initLogger(self, instanceName=name)
        self._imswitch_client = self._rs232manager._imswitch_client
        self.positioner_name = self._imswitch_client.positionersManager.getAllDeviceNames()[0]
        

    def move(self, value=0, axis="X", is_absolute=False, is_blocking=True, acceleration=None, speed=None, isEnable=None, timeout=gTIMEOUT):
        '''
        Move the stage to a specified position.
        '''
        if is_absolute:
            self._imswitch_client.positionersManager.movePositioner(self.positioner_name, axis, value, is_absolute=True, is_blocking=is_blocking)
            new_position = value
        else:
            new_position = self._position[axis]  + value
            self._imswitch_client.positionersManager.movePositioner(self.positioner_name, axis, value, is_absolute=True, is_blocking=is_blocking)
        self._position[axis] = value
        
    def moveForever(self, speed=(0, 0, 0, 0), is_stop=False):
        self._motor.move_forever(speed=speed, is_stop=is_stop)

    def setSpeed(self, speed, axis=None):
        self._imswitch_client.setPositionerSpeed(self.positioner_name, axis=axis, speed=speed)

    def setPosition(self, value, axis):
        pass #TODO: Not implemented yet

    def setPositionOnDevice(self, value, axis):
        pass #TODO: Not implemented yet

    def setPositionFromDevice(self, positionArray: np.array):
        ''' mostly used for he position callback 
        If new positions are coming from the device they will be updated in ImSwitch too'''
        for iAxis, axisName in enumerate(["A", "X", "Y", "Z"]):
            self.setPosition(positionArray[iAxis]*self.stepSizes[axisName], axisName)
        self._commChannel.sigUpdateMotorPosition.emit()
        
    def closeEvent(self):
        pass

    def getPosition(self):
        # load position from device
        # t,x,y,z
        try:
            allPositions = 1.*self._imswitch_client.positionersManager.getPositionerPositions()[self.positioner_name]
            return {"X": allPositions[1], "Y": allPositions[2], "Z": allPositions[3], "A": allPositions[0]}
        except Exception as e:
            self.__logger.error(e)
            return self._position

    def forceStop(self, axis):
        self._imswitch_client.positionersManager.stop(axis=axis)

    def get_abs(self, axis):
        return self._position[axis]

    def stop_x(self):
        self._imswitch_client.positionersManager.stop(axis="X")

    def stop_y(self):
        self._imswitch_client.positionersManager.stop(axis="Y")

    def stop_z(self):
        self._imswitch_client.positionersManager.stop(axis="Z")

    def stop_a(self):
        self._imswitch_client.positionersManager.stop(axis="A")

    def stopAll(self):
        for iAxis in ("X", "Y", "Z", "A"):
            self.forceStop(axis=iAxis)

    def doHome(self, axis, isBlocking=False):
        if axis == "X" and (self.homeXenabled or abs(self.homeStepsX)>0):
            self.home_x(isBlocking)
        if axis == "Y" and (self.homeYenabled or abs(self.homeStepsY)>0):
            self.home_y(isBlocking)
        if axis == "Z" and (self.homeZenabled or abs(self.homeStepsZ)>0):
            self.home_z(isBlocking)
        if axis == "A" and (self.homeAenabled or abs(self.homeStepsA)>0):
            self.home_a(isBlocking)

    def home_x(self, isBlocking=False):
        if abs(self.homeStepsX)>0:
            self.move(value=self.homeStepsX, speed=self.homeSpeedX, axis="X", is_absolute=False, is_blocking=True)
            self.move(value=-np.sign(self.homeStepsX)*np.abs(self.homeEndposReleaseX), speed=self.homeSpeedX, axis="X", is_absolute=False, is_blocking=True)
            self.setPosition(axis="X", value=0)
            self.setPositionOnDevice(value=0, axis="X")
        elif self.homeXenabled:
            self._imswitch_client.positionersManager.homeAxis(positioner_name=self.positioner_name, axis="X", is_blocking=isBlocking)
        else:
            self.__logger.info("No homing parameters set for X axis or not enabled in settings.")
            return
        self.setPosition(axis="X", value=0)

    def home_y(self,isBlocking=False):
        if abs(self.homeStepsY)>0:
            self.move(value=self.homeStepsY, speed=self.homeSpeedY, axis="Y", is_absolute=False, is_blocking=True)
            self.move(value=-np.sign(self.homeStepsY)*np.abs(self.homeEndposReleaseY), speed=self.homeSpeedY, axis="Y", is_absolute=False, is_blocking=True)
            self.setPosition(axis="Y", value=0)
            self.setPositionOnDevice(value=0, axis="Y")
        elif self.homeYenabled:
            self._imswitch_client.positionersManager.homeAxis(positioner_name=self.positioner_name, axis="Y", is_blocking=isBlocking)
        else:
            self.__logger.info("No homing parameters set for X axis or not enabled in settings.")
            return
        self.setPosition(axis="Y", value=0)

    def home_z(self,isBlocking=False):
        if abs(self.homeStepsZ)>0:            
            self.move(value=self.homeStepsZ, speed=self.homeSpeedZ, axis="Z", is_absolute=False, is_blocking=True)
            self.move(value=-np.sign(self.homeStepsZ)*np.abs(self.homeEndposReleaseZ), speed=self.homeSpeedZ, axis="Z", is_absolute=False, is_blocking=True)
            self.setPosition(axis="Z", value=0)
            self.setPositionOnDevice(value=0, axis="Z")
        elif self.homeZenabled:
            self._imswitch_client.positionersManager.homeAxis(positioner_name=self.positioner_name, axis="Z", is_blocking=isBlocking)
        else:
            self.__logger.info("No homing parameters set for X axis or not enabled in settings.")
            return
        self.setPosition(axis="Z", value=0)
        
    def home_a(self,isBlocking=False):
        if abs(self.homeStepsA)>0:
            self.move(value=self.homeStepsA, speed=self.homeSpeedA, axis="A", is_absolute=False, is_blocking=True)
            self.move(value=-np.sign(self.homeStepsA)*np.abs(self.homeEndposReleaseA), speed=self.homeSpeedA, axis="A", is_absolute=False, is_blocking=True)
            self.setPosition(axis="A", value=0)
            self.setPositionOnDevice(value=0, axis="A")
        elif self.homeAenabled:
            self._imswitch_client.positionersManager.homeAxis(positioner_name=self.positioner_name, axis="A", is_blocking=isBlocking)
        else:
            self.__logger.info("No homing parameters set for X axis or not enabled in settings.")
            return
        self.setPosition(axis="A", value=0)

    def home_xyz(self):
        if self.homeXenabled and self.homeYenabled and self.homeZenabled:
            for iAxis in ("X", "Y", "Z"):
                self._imswitch_client.positionersManager.homeAxis(positioner_name=self.positioner_name, axis=iAxis, is_blocking=1)
                self.setPosition(axis=iAxis, value=0)
