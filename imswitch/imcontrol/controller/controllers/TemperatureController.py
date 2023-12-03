import numpy as np
import time
import threading
import collections

from imswitch.imcommon.framework import Signal, Thread, Worker, Mutex, Timer
from imswitch.imcontrol.view import guitools
from ..basecontrollers import ImConWidgetController

from PyQt5.QtCore import QThread, pyqtSignal, QObject

from imswitch.imcommon.model import APIExport, dirtools, initLogger

class TemperatureWorker(QObject):
    temperatureUpdated = pyqtSignal(float)
    plotDataUpdated = pyqtSignal(np.ndarray, np.ndarray)

    def __init__(self, parent, tMeasure):
        super().__init__()
        self.parent = parent
        self.temperatureController = self.parent.temperatureController
        self.tMeasure = tMeasure
        self.is_running = True
        self.startTime = time.time()
        self.nBuffer = self.parent
        self.currPoint = self.parent.currPoint
        
    def run(self):
        while self.is_running:
            temperatureValue = self.temperatureController.get_temperature()
            self.temperatureUpdated.emit(temperatureValue)

            # Update plot data
            self.updatePlotData(temperatureValue)

            time.sleep(self.tMeasure)

    def updatePlotData(self, temperatureValue):
        # Assuming you have a method to update your set point data
        self.updateSetPointData(temperatureValue)

        # Now emit the updated data
        # Assuming self.timeData and self.setPointData are the arrays storing the time and set point data
        self.plotDataUpdated.emit(self.timeData, self.setPointData)

    def updateSetPointData(self, temperatureValue):
        # Your logic to update the setPointData and timeData
        currentTime = time.time() - self.startTime
        if self.currPoint < self.nBuffer:
            self.setPointData[self.currPoint,0] = temperatureValue
            self.setPointData[self.currPoint,1] = self.controlTarget
            self.timeData[self.currPoint] = currentTime
        else:
            # Shift the data to make room for new entries
            self.setPointData[:-1] = self.setPointData[1:]
            self.setPointData[-1] = [temperatureValue, self.controlTarget]
            self.timeData[:-1] = self.timeData[1:]
            self.timeData[-1] = currentTime
        self.currPoint += 1

    def stop(self):
        self.is_running = False

class TemperatureController(ImConWidgetController):
    """ Linked to TemperatureWidget."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._logger = initLogger(self, tryInheritParent=False)

        # Parameters for monitoring the pressure
        self.tMeasure  = 1 # sampling rate of measure pressure
        self.is_measure = True
        self.temperatureValue  = 0
        self.nBuffer = 1000
        self.currPoint = 0
        self.setPointData = np.zeros((self.nBuffer,2))
        self.timeData = np.zeros(self.nBuffer)


        # settings for the controller
        self.controlTarget = 37

        # Hard-coded PID values..
        self.Kp = 100
        self.Ki = 0.1
        self.Kd = .5
        self.PIDenabled = False

        # get hold on the Temperature Controller
        try:
            self.temperatureController = self._master.rs232sManager["ESP32"]._esp32.temperature
        except:
            return
        # Connect TemperatureWidget signals
        self._widget.sigPIDToggled.connect(self.setPID)
        self._widget.sigsliderTemperatureValueChanged.connect(self.valueTemperatureValueChanged)
        self.setPID(self._widget.getPIDChecked())

        # Worker and Thread setup
        self.worker = TemperatureWorker(self, self.tMeasure)
        self.measurementThread = QThread()

        self.worker.moveToThread(self.measurementThread)
        self.worker.temperatureUpdated.connect(self._widget.updateTemperature)
        # Connect other signals like self.worker.plotDataUpdated to the appropriate slots

        self.measurementThread.started.connect(self.worker.run)
        self.measurementThread.start()
        

    def valueTemperatureValueChanged(self, value):
        """ Change setpoint for the temperature. """
        self.controlTarget = value

        # retrieve PID values
        self.Kp, self.Ki, self.Kd = self._widget.getPIDValues()
        
        # get temperature value from GUI
        self.controlTarget = self._widget.getTemperatureValue()
        
        # we actually set the target value with this slider
        self._widget.updateTargetTemperatureValue(self.controlTarget)
        self.set_temperature(active=self.PIDenabled,
                                Kp=self.Kp, Ki=self.Ki, Kd=self.Kd, target=self.controlTarget)
        
    def valueRotationSpeedChanged(self, value):
        """ Change magnitude. """
        self.speedRotation = int(value)
        self._widget.updateRotationSpeed(self.speedPump)
        self.tRoundtripRotation = self.stepsPerRotation/(0.001+self.speedRotation) # in s
        self.positioner.moveForever(speed=(self.speedPump,self.speedRotation,0),is_stop=False)

    def __del__(self):
        self.is_measure=False
        self.worker.stop()
        self.measurementThread.quit()
        self.measurementThread.wait()
        if hasattr(super(), '__del__'):
            super().__del__()

    def setPID(self, enabled):
        """ Show or hide Temperature. """
        self.PIDenabled = enabled
        # retrieve PID values
        self.Kp, self.Ki, self.Kd = self._widget.getPIDValues()
        
        # get temperature value from GUI
        self.controlTarget = float(self._widget.getTemperatureValue())

        self.set_temperature(active=self.PIDenabled,
                                Kp=self.Kp, Ki=self.Ki, Kd=self.Kd, target=self.controlTarget)
        
    @APIExport(runOnUIThread=False)
    def set_temperature(self, active, Kp=None, Ki=None, Kd=None, target=None):
        """ Set the temperature. """
        if Kp is not None:
            self.Kp = Kp
        if Ki is not None:
            self.Ki = Ki
        if Kd is not None:
            self.Kd = Kd
        if target is not None:
            self.controlTarget = target

        self.temperatureController.set_temperature(active=active
            , Kp=self.Kp, Ki=self.Ki, Kd=self.Kd, target=self.controlTarget)

    def updateSetPointData(self):
        if self.currPoint < self.nBuffer:
            self.setPointData[self.currPoint,0] = self.temperatureValue
            self.setPointData[self.currPoint,1] = self.controlTarget

            self.timeData[self.currPoint] = time.time() - self.startTime
        else:
            self.setPointData[:-1,0] = self.setPointData[1:,0]
            self.setPointData[-1,0] = self.temperatureValue
            self.setPointData[:-1,1] = self.setPointData[1:,1]
            self.setPointData[-1,1] = self.controlTarget
            self.timeData[:-1] = self.timeData[1:]
            self.timeData[-1] = time.time() - self.startTime
        self.currPoint += 1

    @APIExport(runOnUIThread=False)
    def getTemperature(self):
        """ Get the temperature. """
        return self.temperatureController.get_temperature()
    
    def updateMeasurements(self):
        while self.is_measure:
            self.temperatureValue  = self.getTemperature()
            self._widget.updateTemperature(self.temperatureValue)
            # update plot
            self.updateSetPointData()
            if self.currPoint < self.nBuffer:
                self._widget.temperaturePlotCurve.setData(self.timeData[1:self.currPoint],
                                                    self.setPointData[1:self.currPoint,0])
            else:
                self._widget.temperaturePlotCurve.setData(self.timeData, self.setPointData[:,0])
            time.sleep(self.tMeasure)



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
