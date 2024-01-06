from imswitch.imcommon.model import initLogger
from .PositionerManager import PositionerManager
import time
import numpy as np
from imswitch.imcommon.model import APIExport, generateAPI, initLogger
import threading

MAX_ACCEL = 500000
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
        self.stepsizeA = positionerInfo.managerProperties.get('stepsizeA', 1)

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
        self.minA = positionerInfo.managerProperties.get('minA', -np.inf)
        self.maxA = positionerInfo.managerProperties.get('maxA', np.inf)

        # Calibrated backlash
        self.backlashX = positionerInfo.managerProperties.get('backlashX', 0)
        self.backlashY = positionerInfo.managerProperties.get('backlashY', 0)
        self.backlashZ = positionerInfo.managerProperties.get('backlashZ', 0)
        self.backlashA = positionerInfo.managerProperties.get('backlashA', 0)



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

        self.homeEndposReleaseX = positionerInfo.managerProperties.get('homeEndposReleaseX', 1)
        self.homeEndposReleaseY = positionerInfo.managerProperties.get('homeEndposReleaseY', 1)
        self.homeEndposReleaseZ = positionerInfo.managerProperties.get('homeEndposReleaseZ', 1)

        self.homeOnStartX = positionerInfo.managerProperties.get('homeOnStartX', 0)
        self.homeOnStartY = positionerInfo.managerProperties.get('homeOnStartY', 0)
        self.homeOnStartZ = positionerInfo.managerProperties.get('homeOnStartZ', 0)


        self.homeXenabled = positionerInfo.managerProperties.get('homeXenabled', False)
        self.homeYenabled = positionerInfo.managerProperties.get('homeYenabled', False)
        self.homeZenabled = positionerInfo.managerProperties.get('homeZenabled', False)

        self.limitXenabled = positionerInfo.managerProperties.get('limitXenabled', False)
        self.limitYenabled = positionerInfo.managerProperties.get('limitYenabled', False)
        self.limitZenabled = positionerInfo.managerProperties.get('limitZenabled', False)

        # Axis order
        self.axisOrder = positionerInfo.managerProperties.get('axisOrder', [0, 1, 2, 3])

        # CoreXY geometry(cont'd)
        self.isCoreXY = positionerInfo.managerProperties.get('isCoreXY', False)

        # Enable motors
        self.is_enabled = positionerInfo.managerProperties.get('isEnable', True)
        self.enableauto = positionerInfo.managerProperties.get('enableauto', True)
        self.enalbeMotors(enable=self.is_enabled, enableauto=self.enableauto)

        # Dual Axis if we have A and Z to drive the motor
        self.isDualAxis = positionerInfo.managerProperties.get("isDualaxis", False)
        if self.isDualAxis:
            self.stepsizeA = self.stepsizeZ
            self.backlashA = self.backlashZ

        # Acceleration
        self.acceleration = {"X": MAX_ACCEL, "Y": MAX_ACCEL, "Z": MAX_ACCEL, "A": MAX_ACCEL}

        # Set axis order
        self.setAxisOrder(order=self.axisOrder)

        # Set IsCoreXY
        self._motor.setIsCoreXY(isCoreXY=self.isCoreXY)

        # Setup motors
        self.setupMotor(self.minX, self.maxX, self.stepsizeX, self.backlashX, "X")
        self.setupMotor(self.minY, self.maxY, self.stepsizeY, self.backlashY, "Y")
        self.setupMotor(self.minZ, self.maxZ, self.stepsizeZ, self.backlashZ, "Z")
        self.setupMotor(self.minA, self.maxA, self.stepsizeA, self.backlashA, "A")

        # optional: hom on startup:
        if self.homeOnStartX: self.home_x()
        if self.homeOnStartY: self.home_y()
        if self.homeOnStartZ: self.home_z()

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
        #FIXME: for i, iaxis in enumerate(("A","X","Y","Z")):
        #    self._position[iaxis] = self._motor._position[i]
        if isEnable is None:
            isEnable = self.is_enabled
        if speed is None:
            if axis == "X": speed = self.speed["X"]
            if axis == "Y": speed = self.speed["Y"]
            if axis == "Z": speed = self.speed["Z"]
            if axis == "A": speed = self.speed["A"]
            if axis == "XY": speed = (self.speed["X"], self.speed["Y"])
            if axis == "XYZ": speed = (self.speed["X"], self.speed["Y"], self.speed["Z"])
        if acceleration is None:
            if axis == "X": acceleration = self.acceleration["X"]
            if axis == "Y": acceleration = self.acceleration["Y"]
            if axis == "Z": acceleration = self.acceleration["Z"]
            if axis == "A": acceleration = self.acceleration["A"]
            if axis == "XY": acceleration = (self.acceleration["X"], self.acceleration["Y"])
            if axis == "XYZ": acceleration = (self.acceleration["X"], self.acceleration["Y"], self.acceleration["Z"])
        if axis == 'X' and speed >0:
            # don't move to negative positions
            if self.limitXenabled and is_absolute and value < 0: return
            elif self.limitXenabled and not is_absolute and self._position[axis] + value < 0: return
            self._motor.move_x(value, speed, acceleration=acceleration, is_absolute=is_absolute, is_enabled=isEnable, is_blocking=is_blocking, timeout=timeout)
            if not is_absolute: self._position[axis] = self._position[axis] + value
            else: self._position[axis] = value
        elif axis == 'Y' and speed >0:
            # don't move to negative positions
            if self.limitYenabled and is_absolute and value < 0: return
            elif self.limitYenabled and not is_absolute and self._position[axis] + value < 0: return
            self._motor.move_y(value, speed, acceleration=acceleration, is_absolute=is_absolute, is_enabled=isEnable, is_blocking=is_blocking, timeout=timeout)
            if not is_absolute: self._position[axis] = self._position[axis] + value
            else: self._position[axis] = value
        elif axis == 'Z' and speed >0:
            # don't move to negative positions
            if self.limitZenabled and is_absolute and value < 0: return
            elif self.limitZenabled and not is_absolute and self._position[axis] + value < 0: return
            self._motor.move_z(value, speed, acceleration=acceleration, is_absolute=is_absolute, is_enabled=isEnable, is_blocking=is_blocking, is_dualaxis=self.isDualAxis, timeout=timeout)
            if not is_absolute: self._position[axis] = self._position[axis] + value
            else: self._position[axis] = value
        elif axis == 'A' and speed >0:
            # don't move to negative positions
            #if is_absolute and value < 0: return
            #elif not is_absolute and self._position[axis] + value < 0: return
            self._motor.move_a(value, speed, acceleration=acceleration, is_absolute=is_absolute, is_enabled=isEnable, is_blocking=is_blocking, timeout=timeout)
            if not is_absolute: self._position[axis] = self._position[axis] + value
            else: self._position[axis] = value
        elif axis == 'XY':
            # don't move to negative positions
            if is_absolute and (value[0] < 0 or value[1] < 0): return
            elif not is_absolute and (self._position["X"] + value[0] < 0 or self._position["Y"] + value[1] < 0): return
            self._motor.move_xy(value, speed, acceleration=acceleration, is_absolute=is_absolute, is_enabled=isEnable, is_blocking=is_blocking, timeout=timeout)
            for i, iaxis in enumerate(("X", "Y")):
                if not is_absolute:
                    self._position[iaxis] = self._position[iaxis] + value[i]
                else:
                    self._position[iaxis] = value[i]
        elif axis == 'XYZ':
            self._motor.move_xyz(value, speed, acceleration=acceleration, is_absolute=is_absolute, is_enabled=isEnable, is_blocking=is_blocking, timeout=timeout)
            for i, iaxis in enumerate(("X", "Y", "Z")):
                if not is_absolute: self._position[iaxis] = self._position[iaxis] + value[i]
                else: self._position[iaxis] = value[i]
        else:
            self.__logger.error('Wrong axis, has to be "X" "Y" or "Z".')


    def measure(self, sensorID=0, NAvg=100):
        return self._motor.read_sensor(sensorID=sensorID, NAvg=NAvg)

    def setupPIDcontroller(self, PIDactive=1, Kp=100, Ki=10, Kd=1, target=500, PID_updaterate=200):
        return self._motor.set_pidcontroller(PIDactive=PIDactive, Kp=Kp, Ki=Ki, Kd=Kd, target=target,
                                             PID_updaterate=PID_updaterate)
 
    def moveForeverByAxis(self, speed=0, axis="X", is_stop=False):
        speed=(0, 0, 0, 0)
        if axis == "X":
            speed[1]=speed
        elif axis == "Y":
            speed[2]=speed
        elif axis == "Z":
            speed[3]=speed
        elif axis == "A":
            speed[0]=speed
        self.moveForever(speed=speed, is_stop=is_stop)
     
    def moveForever(self, speed=(0, 0, 0, 0), is_stop=False):
        self._motor.move_forever(speed=speed, is_stop=is_stop)

    def setEnabled(self, is_enabled):
        self.is_enabled = is_enabled

    def setSpeed(self, speed, axis=None):
        # TODO: Map that to the JSON!
        if type(speed) == int and axis == None:
            self._speed["X"] = speed
            self._speed["Y"] = speed
            self._speed["Z"] = speed
            self._speed["A"] = speed
        else:
            self._speed[axis] = speed

    def setPosition(self, value, axis):
        # print(f"setPosition - Axis: {axis} -> New Value: {value}")
        self._position[axis] = value

    def setPositionOnDevice(self, value, axis):
        self.setPosition(value, axis)
        self._motor.set_position(axis, value)

    def closeEvent(self):
        pass

    def getPosition(self):
        # load position from device
        # t,x,y,z
        try:
            allPositions = 1.*self._motor.get_position()
        except Exception as e:
            self.__logger.error(e)
            allPositions = [0.,0.,0.,0.]
        allPositionsDict={"X": allPositions[1], "Y": allPositions[2], "Z": allPositions[3], "A": allPositions[0]}

        return allPositionsDict

    def forceStop(self, axis):
        if axis=="X":
            self.stop_x()
        elif axis=="Y":
            self.stop_y()
        elif axis=="Z":
            self.stop_z()
        elif axis=="A":
            self.stop_a()
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

    def stop_a(self):
        self._motor.stop(axis = "A")

    def stopAll(self):
        self._motor.stop()

    def doHome(self, axis, isBlocking=False):
        if axis == "X" and self.homeXenabled:
            self.home_x(isBlocking)
        if axis == "Y" and self.homeYenabled:
            self.home_y(isBlocking)
        if axis == "Z" and self.homeZenabled:
            self.home_z(isBlocking)

    def home_x(self, isBlocking=False):
        self._homeModule.home_x(speed=self.homeSpeedX, direction=self.homeDirectionX, endstoppolarity=self.homeEndstoppolarityX, endposrelease=self.homeEndposReleaseX, isBlocking=isBlocking)
        self.setPosition(axis="X", value=0)

    def home_y(self,isBlocking=False):
        self._homeModule.home_y(speed=self.homeSpeedY, direction=self.homeDirectionY, endstoppolarity=self.homeEndstoppolarityY, endposrelease=self.homeEndposReleaseY, isBlocking=isBlocking)
        self.setPosition(axis="Y", value=0)

    def home_z(self,isBlocking=False):
        self._homeModule.home_z(speed=self.homeSpeedZ, direction=self.homeDirectionZ, endstoppolarity=self.homeEndstoppolarityZ, endposrelease=self.homeEndposReleaseZ, isBlocking=isBlocking)
        self.setPosition(axis="Z", value=0)

    def home_xyz(self):
        if self.homeXenabled and self.homeYenabled and self.homeZenabled:
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
