from imswitch.imcommon.model import initLogger
from .PositionerManager import PositionerManager
import time
import numpy as np

PHYS_FACTOR = 1
gTIMEOUT = 10


class ESP32StageManager(PositionerManager):

    def __init__(self, positionerInfo, name, **lowLevelManagers):
        super().__init__(positionerInfo, name, initialPosition={
            axis: 0 for axis in positionerInfo.axes
        })
        self._rs232manager = lowLevelManagers['rs232sManager'][
            positionerInfo.managerProperties['rs232device']
        ]
        self.__logger = initLogger(self, instanceName=name)

        # calibrated stepsize in steps/µm
        if positionerInfo.managerProperties.get('stepsizeX') is not None:
            self.stepsizeX = positionerInfo.managerProperties['stepsizeX']
        else:
            self.stepsizeX = 1

        # calibrated stepsize
        if positionerInfo.managerProperties.get('stepsizeY') is not None:
            self.stepsizeY = positionerInfo.managerProperties['stepsizeY']
        else:
            self.stepsizeY = 1

        # calibrated stepsize
        if positionerInfo.managerProperties.get('stepsizeZ') is not None:
            self.stepsizeZ = positionerInfo.managerProperties['stepsizeZ']
        else:
            self.stepsizeZ = 1

        # calibrated stepsize
        if positionerInfo.managerProperties.get('stepsizeT') is not None:
            self.stepsizeT = positionerInfo.managerProperties['stepsizeT']
        else:
            self.stepsizeT = 1

            # miniumum/maximum steps in X
        if positionerInfo.managerProperties.get('minX') is not None:
            self.minX = positionerInfo.managerProperties['minX']
        else:
            self.minX = -np.inf
        if positionerInfo.managerProperties.get('maxX') is not None:
            self.maxX = positionerInfo.managerProperties['maxX']
        else:
            self.maxX = np.inf

        # minimum/maximum steps in Y
        if positionerInfo.managerProperties.get('minY') is not None:
            self.minY = positionerInfo.managerProperties['minY']
        else:
            self.minY = -np.inf
        if positionerInfo.managerProperties.get('maxY') is not None:
            self.maxY = positionerInfo.managerProperties['maxY']
        else:
            self.maxY = np.inf
        # minimum/maximum steps in Z
        if positionerInfo.managerProperties.get('minZ') is not None:
            self.minZ = positionerInfo.managerProperties['minZ']
        else:
            self.minZ = -np.inf
        if positionerInfo.managerProperties.get('maxZ') is not None:
            self.maxZ = positionerInfo.managerProperties['maxZ']
        else:
            self.maxZ = np.inf
            # minimum/maximum steps in T
        if positionerInfo.managerProperties.get('minT') is not None:
            self.minT = positionerInfo.managerProperties['minT']
        else:
            self.minT = -np.inf
        if positionerInfo.managerProperties.get('maxT') is not None:
            self.maxT = positionerInfo.managerProperties['maxT']
        else:
            self.maxT = np.inf

            # calibrated backlash
        if positionerInfo.managerProperties.get('backlashX') is not None:
            self.backlashX = positionerInfo.managerProperties['backlashX']
        else:
            self.backlashX = 1

        # calibrated backlash
        if positionerInfo.managerProperties.get('backlashY') is not None:
            self.backlashY = positionerInfo.managerProperties['backlashY']
        else:
            self.backlashY = 1

        # calibrated backlash
        if positionerInfo.managerProperties.get('backlashZ') is not None:
            self.backlashZ = positionerInfo.managerProperties['backlashZ']
        else:
            self.backlashZ = 1

        # calibrated backlash
        if positionerInfo.managerProperties.get('backlashT') is not None:
            self.backlashT = positionerInfo.managerProperties['backlashT']
        else:
            self.backlashT = 1

        # setup homing coordinates and speed
        if positionerInfo.managerProperties.get('homeSpeedX') is not None:
            self.homeSpeedX = positionerInfo.managerProperties['homeSpeedX']
        else:
            self.homeSpeedX = 15000
        if positionerInfo.managerProperties.get('homeDirectionX') is not None:
            self.homeDirectionX = positionerInfo.managerProperties['homeDirectionX']
        else:
            self.homeDirectionX = -1

        if positionerInfo.managerProperties.get('homeSpeedY') is not None:
            self.homeSpeedY = positionerInfo.managerProperties['homeSpeedY']
        else:
            self.homeSpeedY = 15000
        if positionerInfo.managerProperties.get('homeDirectionY') is not None:
            self.homeDirectionY = positionerInfo.managerProperties['homeDirectionY']
        else:
            self.homeDirectionY = -1

        if positionerInfo.managerProperties.get('homeSpeedZ') is not None:
            self.homeSpeedZ = positionerInfo.managerProperties['homeSpeedZ']
        else:
            self.homeSpeedZ = 15000
        if positionerInfo.managerProperties.get('homeDirectionZ') is not None:
            self.homeDirectionZ = positionerInfo.managerProperties['homeDirectionZ']
        else:
            self.homeDirectionZ = -1

        # grab motor object
        self._motor = self._rs232manager._esp32.motor
        self._homeModule = self._rs232manager._esp32.home

        # setup motors
        self.setupMotor(self.minX, self.maxX, self.stepsizeX, self.backlashX, "X")
        self.setupMotor(self.minY, self.maxY, self.stepsizeY, self.backlashY, "Y")
        self.setupMotor(self.minZ, self.maxZ, self.stepsizeZ, self.backlashZ, "Z")
        self.setupMotor(self.minT, self.maxT, self.stepsizeT, self.backlashT, "T")

        self.is_enabled = False

        # get bootup position and write to GUI
        self._position = self.getPosition()
        # force setting the position
        self.setPosition(self._position['X'], "X")
        self.setPosition(self._position['Y'], "X")
        self.setPosition(self._position['Z'], "Z")

    def setupMotor(self, minPos, maxPos, stepSize, backlash, axis):
        self._motor.setup_motor(axis=axis, minPos=minPos, maxPos=maxPos, stepSize=stepSize, backlash=backlash)

    def move(self, value=0, axis="X", is_absolute=False, is_blocking=True, speed=None, timeout=gTIMEOUT):
        if speed is None:
            if axis == "X": speed = self.speed["X"]
            if axis == "Y": speed = self.speed["Y"]
            if axis == "Z": speed = self.speed["Z"]
            if axis == "XY": speed = (self.speed["X"], self.speed["Y"])
            if axis == "XYZ": speed = (self.speed["X"], self.speed["Y"], self.speed["Z"])
        if axis == 'X':
            self._motor.move_x(value, speed, is_absolute=is_absolute, is_enabled=self.is_enabled,
                               is_blocking=is_blocking, timeout=timeout)
            if not is_absolute:
                self._position[axis] = self._position[axis] + value
            else:
                self._position[axis] = value
        elif axis == 'Y':
            self._motor.move_y(value, speed, is_absolute=is_absolute, is_enabled=self.is_enabled,
                               is_blocking=is_blocking, timeout=timeout)
            if not is_absolute:
                self._position[axis] = self._position[axis] + value
            else:
                self._position[axis] = value
        elif axis == 'Z':
            self._motor.move_z(value, speed, is_absolute=is_absolute, is_enabled=self.is_enabled,
                               is_blocking=is_blocking, timeout=timeout)
            if not is_absolute:
                self._position[axis] = self._position[axis] + value
            else:
                self._position[axis] = value
        elif axis == 'XY':
            self._motor.move_xy(value, speed, is_absolute=is_absolute, is_enabled=self.is_enabled,
                                is_blocking=is_blocking, timeout=timeout)
            for i, iaxis in enumerate(("X", "Y")):
                if not is_absolute:
                    self._position[iaxis] = self._position[iaxis] + value[i]
                else:
                    self._position[iaxis] = value[i]
        elif axis == 'XYZ':
            self._motor.move_xyz(value, speed, is_absolute=is_absolute, is_enabled=self.is_enabled,
                                 is_blocking=is_blocking, timeout=timeout)
            for i, iaxis in enumerate(("X", "Y")):
                if not is_absolute:
                    self._position[iaxis] = self._position[iaxis] + value[i]
                else:
                    self._position[iaxis] = value[i]
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
        else:
            self._speed[axis] = speed

    def setPosition(self, value, axis):
        if value: value += 1  # TODO: Firmware weirdness
        self._motor.set_position(axis=axis, position=value)
        self._position[axis] = value

    def closeEvent(self):
        pass

    def getPosition(self):
        try:
            allPositions = self._motor.get_position()
        except:
            allPositions = [0, 0, 0, 0]

        return {"X": allPositions[1], "Y": allPositions[2], "Z": allPositions[3], "A": allPositions[0]}
    #
    def get_position(self):
        pos = self.getPosition()
        return pos["X"], pos["Y"], pos["Z"]

    def forceStop(self, axis):
        if axis == "X":
            self.stop_x()
        elif axis == "Y":
            self.stop_y()
        elif axis == "Z":
            self.stop_z()
        else:
            self.stopAll()

    def stop_x(self):
        self._motor.stop(axis="X")

    def stop_y(self):
        self._motor.stop(axis="Y")

    def stop_z(self):
        self._motor.stop(axis="Z")

    def stopAll(self):
        self._motor.stop()

    def doHome(self, axis):
        if axis == "X":
            self.home_x()
        if axis == "Y":
            self.home_y()
        if axis == "Z":
            self.home_z()

    def home_x(self):
        self._homeModule.home_x(speed=self.homeSpeedX, direction=self.homeDirectionX)
        self._position["X"] = 0

    def home_y(self):
        self._homeModule.home_y(speed=self.homeSpeedY, direction=self.homeDirectionY)
        self._position["Y"] = 0

    def home_z(self):
        self._homeModule.home_z(speed=self.homeSpeedZ, direction=self.homeDirectionZ)
        self._position["Z"] = 0

    def home_xyz(self):
        self._motor.home_xyz()
        self._position["X"] = 0
        self._position["Y"] = 0
        self._position["Z"] = 0

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