from imswitch.imcommon.model import initLogger
from .PositionerManager import PositionerManager
import time
import numpy as np
from imswitch.imcommon.model import APIExport, generateAPI, initLogger
import threading


PHYS_FACTOR = 1
gTIMEOUT = 100
class ESP32StageManager(PositionerManager):
    def __init__(self, positionerInfo, name, **lowLevelManagers):
        super().__init__(positionerInfo, name, initialPosition={axis: 0 for axis in positionerInfo.axes})
        self._rs232manager = lowLevelManagers['rs232sManager'][positionerInfo.managerProperties['rs232device']]
        self.__logger = initLogger(self, instanceName=name)

        # Grab motor object
        self._motor = self._rs232manager._esp32.motor
        self._homeModule = self._rs232manager._esp32.home

        # Calibrated stepsizes in steps/µm
        self.stepsizeX = positionerInfo.managerProperties.get('stepsizeX', 1)
        self.stepsizeY = positionerInfo.managerProperties.get('stepsizeY', 1)
        self.stepsizeZ = positionerInfo.managerProperties.get('stepsizeZ', 1)
        self.stepsizeT = positionerInfo.managerProperties.get('stepsizeT', 1)

        # Minimum/maximum steps in X
        self.minX = positionerInfo.managerProperties.get('minX', -np.inf)
        self.maxX = positionerInfo.managerProperties.get('maxX', np.inf)

        # Minimum/maximum steps in Y
        self.minY = positionerInfo.managerProperties.get('minY', -np.inf)
        self.maxY = positionerInfo.managerProperties.get('maxY', np.inf)

        # Minimum/maximum steps in Z
        self.minZ = positionerInfo.managerProperties.get('minZ', -np.inf)
        self.maxZ = positionerInfo.managerProperties.get('maxZ', np.inf)

        # Minimum/maximum steps in T
        self.minT = positionerInfo.managerProperties.get('minT', -np.inf)
        self.maxT = positionerInfo.managerProperties.get('maxT', np.inf)

        # Calibrated backlash
        self.backlashX = positionerInfo.managerProperties.get('backlashX', 1)
        self.backlashY = positionerInfo.managerProperties.get('backlashY', 1)
        self.backlashZ = positionerInfo.managerProperties.get('backlashZ', 1)
        self.backlashT = positionerInfo.managerProperties.get('backlashT', 1)

        # Setup homing coordinates and speed
        self.homeSpeedX = positionerInfo.managerProperties.get('homeSpeedX', 15000)
        self.homeDirectionX = positionerInfo.managerProperties.get('homeDirectionX', -1)
        self.homeSpeedY = positionerInfo.managerProperties.get('homeSpeedY', 15000)
        self.homeDirectionY = positionerInfo.managerProperties.get('homeDirectionY', -1)
        self.homeSpeedZ = positionerInfo.managerProperties.get('homeSpeedZ', 15000)
        self.homeDirectionZ = positionerInfo.managerProperties.get('homeDirectionZ', -1)

        # Setup homing endstop polarities
        self.homeEndstoppolarityX = positionerInfo.managerProperties.get('homeEndstoppolarityX', 1)
        self.homeEndstoppolarityY = positionerInfo.managerProperties.get('homeEndstoppolarityY', 1)
        self.homeEndstoppolarityZ = positionerInfo.managerProperties.get('homeEndstoppolarityZ', 1)

        # Axis order
        self.axisOrder = positionerInfo.managerProperties.get('axisOrder', [0, 1, 2, 3])

        # CoreXY geometry(cont'd)
        self.isCoreXY = positionerInfo.managerProperties.get('isCoreXY', False)

        # Enable motors
        self.is_enabled = positionerInfo.managerProperties.get('isEnable', True)
        self.enableauto = positionerInfo.managerProperties.get('enableauto', True)
        self.enalbeMotors(enable=self.is_enabled, enableauto=self.enableauto)

        # Acceleration
        self.acceleration = {"X": 40000, "Y": 40000, "Z": 40000, "T": 40000}

        # Set axis order
        self.setAxisOrder(order=self.axisOrder)

        # Set IsCoreXY
        self._motor.setIsCoreXY(isCoreXY=self.isCoreXY)

        # Setup motors
        self.setupMotor(self.minX, self.maxX, self.stepsizeX, self.backlashX, "X")
        self.setupMotor(self.minY, self.maxY, self.stepsizeY, self.backlashY, "Y")
        self.setupMotor(self.minZ, self.maxZ, self.stepsizeZ, self.backlashZ, "Z")
        self.setupMotor(self.minT, self.maxT, self.stepsizeT, self.backlashT, "T")

        # get bootup position and write to GUI
        self._position = self.getPosition()

    def setAxisOrder(self, order=[0,1,2,3]):
        self._motor.setMotorAxisOrder(order=order)

    def enalbeMotors(self, enable=None, enableauto=None):
        """
        enable - Enable Motors (i.e. switch on/off power to motors)
        enableauto - Enable automatic motor power off after motors are not used for a while; will be turned on automatically
        """
        self._motor.set_motor_enable(enable=enable, enableauto=enableauto)

    def setupMotor(self, minPos, maxPos, stepSize, backlash, axis):
        self._motor.setup_motor(axis=axis, minPos=minPos, maxPos=maxPos, stepSize=stepSize, backlash=backlash)

    def move(self, value=0, axis="X", is_absolute=False, is_blocking=True, acceleration=None, speed=None, isEnable=None, timeout=gTIMEOUT):
        if isEnable is None:
            isEnable = self.is_enabled
        if speed is None:
            if axis == "X": speed = self.speed["X"]
            if axis == "Y": speed = self.speed["Y"]
            if axis == "Z": speed = self.speed["Z"]
            if axis == "T": speed = self.speed["T"]
            if axis == "XY": speed = (self.speed["X"], self.speed["Y"])
            if axis == "XYZ": speed = (self.speed["X"], self.speed["Y"], self.speed["Z"])
        if acceleration is None:
            if axis == "X": acceleration = self.acceleration["X"]
            if axis == "Y": acceleration = self.acceleration["Y"]
            if axis == "Z": acceleration = self.acceleration["Z"]
            if axis == "T": acceleration = self.acceleration["T"]
            if axis == "XY": acceleration = (self.acceleration["X"], self.acceleration["Y"])
            if axis == "XYZ": acceleration = (self.acceleration["X"], self.acceleration["Y"], self.acceleration["Z"])

        if axis == 'X':
            self._motor.move_x(value, speed, acceleration=acceleration, is_absolute=is_absolute, is_enabled=isEnable, is_blocking=is_blocking, timeout=timeout)
            if not is_absolute: self._position[axis] = self._position[axis] + value
            else: self._position[axis] = value
        elif axis == 'Y':
            self._motor.move_y(value, speed, acceleration=acceleration, is_absolute=is_absolute, is_enabled=isEnable, is_blocking=is_blocking, timeout=timeout)
            if not is_absolute: self._position[axis] = self._position[axis] + value
            else: self._position[axis] = value
        elif axis == 'Z':
            self._motor.move_z(value, speed, acceleration=acceleration, is_absolute=is_absolute, is_enabled=isEnable, is_blocking=is_blocking, timeout=timeout)
            if not is_absolute: self._position[axis] = self._position[axis] + value
            else: self._position[axis] = value
        elif axis == 'T':
            self._motor.move_t(value, speed, acceleration=acceleration, is_absolute=is_absolute, is_enabled=isEnable, is_blocking=is_blocking, timeout=timeout)
            if not is_absolute: self._position[axis] = self._position[axis] + value
            else: self._position[axis] = value
        elif axis == 'XY':
            self._motor.move_xy(value, speed, acceleration=acceleration, is_absolute=is_absolute, is_enabled=isEnable, is_blocking=is_blocking, timeout=timeout)
            for i, iaxis in enumerate(("X", "Y")):
                if not is_absolute:
                    self._position[iaxis] = self._position[iaxis] + value[i]
                else:
                    self._position[iaxis] = value[i]
        elif axis == 'XYZ':
            self._motor.move_xyz(value, speed, acceleration=acceleration, is_absolute=is_absolute, is_enabled=isEnable, is_blocking=is_blocking, timeout=timeout)
            for i, iaxis in enumerate(("X", "Y")):
                if not is_absolute: self._position[iaxis] = self._position[iaxis] + value[i]
                else: self._position[iaxis] = value[i]
        else:
            print('Wrong axis, has to be "X" "Y" or "Z".')

    def measure(self, sensorID=0, NAvg=100):
        return self._motor.read_sensor(sensorID=sensorID, NAvg=NAvg)

    def setupPIDcontroller(self, PIDactive=1, Kp=100, Ki=10, Kd=1, target=500, PID_updaterate=200):
        return self._motor.set_pidcontroller(PIDactive=PIDactive, Kp=Kp, Ki=Ki, Kd=Kd, target=target,
                                             PID_updaterate=PID_updaterate)

    def moveForever(self, speed=(0, 0, 0), is_stop=False):
        self._motor.move_forever(speed=speed, is_stop=is_stop)

    def setEnabled(self, is_enabled):
        self.is_enabled = is_enabled

    def setSpeed(self, speed, axis=None):
        # TODO: Map that to the JSON!
        if type(speed) == int and axis == None:
            self._speed["X"] = speed
            self._speed["Y"] = speed
            self._speed["Z"] = speed
            self._speed["T"] = speed
        else:
            self._speed[axis] = speed

    def setPosition(self, value, axis):
        # print(f"setPosition - Axis: {axis} -> New Value: {value}")
        self._position[axis] = value

    def closeEvent(self):
        pass

    def getPosition(self):
        # load position from device
        # t,x,y,z
        try:
            allPositions = self._motor.get_position()
        except:
            allPositions = [0,0,0,0]
        allPositionsDict={"X": allPositions[1], "Y": allPositions[2], "Z": allPositions[3], "T": allPositions[0]}
        for iPosAxis, iPosVal in allPositionsDict.items():
            self.setPosition(iPosVal,iPosAxis)
        return allPositionsDict

    def forceStop(self, axis):
        if axis=="X":
            self.stop_x()
        elif axis=="Y":
            self.stop_y()
        elif axis=="Z":
            self.stop_z()
        elif axis=="T":
            self.stop_t()
        else:
            self.stopAll()

    def get_abs(self, axis):
        return self._position[axis]

    def stop_x(self):
        self._motor.stop(axis = "X")

    def stop_y(self):
        self._motor.stop(axis = "Y")

    def stop_z(self):
        self._motor.stop(axis = "Z")

    def stop_t(self):
        self._motor.stop(axis = "T")

    def stopAll(self):
        self._motor.stop()

    def doHome(self, axis, isBlocking=False):
        if axis == "X":
            self.home_x(isBlocking)
        if axis == "Y":
            self.home_y(isBlocking)
        if axis == "Z":
            self.home_z(isBlocking)

    def home_x(self, isBlocking):
        self._homeModule.home_x(speed=self.homeSpeedX, direction=self.homeDirectionX, endstoppolarity=self.homeEndstoppolarityX, isBlocking=isBlocking)
        self.setPosition(axis="X", value=0)

    def home_y(self,isBlocking):
        self._homeModule.home_y(speed=self.homeSpeedY, direction=self.homeDirectionY, endstoppolarity=self.homeEndstoppolarityY, isBlocking=isBlocking)
        self.setPosition(axis="Y", value=0)

    def home_z(self,isBlocking):
        self._homeModule.home_z(speed=self.homeSpeedZ, direction=self.homeDirectionZ, endstoppolarity=self.homeEndstoppolarityZ, isBlocking=isBlocking)
        self.setPosition(axis="Z", value=0)

    def home_xyz(self):
        self._motor.home_xyz()
        [self.setPosition(axis=axis, value=0) for axis in ["X","Y","Z"]]


# Copyright (C) 2020, 2021 The imswitch developers
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
