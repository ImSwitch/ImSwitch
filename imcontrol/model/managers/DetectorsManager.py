from time import sleep

import numpy as np

from imcommon.framework import Mutex, Signal, SignalInterface, Thread, Timer, Worker
from .MultiManager import MultiManager


class DetectorsManager(MultiManager, SignalInterface):
    """ DetectorsManager is an interface for dealing with DetectorManagers. """

    sigAcquisitionStarted = Signal()
    sigAcquisitionStopped = Signal()
    sigDetectorSwitched = Signal(str, str)  # (newDetectorName, oldDetectorName)
    sigImageUpdated = Signal(np.ndarray, bool)  # (image, init)

    def __init__(self, detectorInfos, updatePeriod, **kwargs):
        MultiManager.__init__(self, detectorInfos, 'detectors', **kwargs)
        SignalInterface.__init__(self)

        self._activeAcqHandles = []
        self._activeAcqLVHandles = []
        self._activeAcqsMutex = Mutex()

        self._currentDetectorName = None
        for detectorName, detectorInfo in detectorInfos.items():
            # Connect signals
            self._subManagers[detectorName].sigImageUpdated.connect(
                lambda image, init, detectorName=detectorName: self.sigImageUpdated.emit(
                    image, init
                ) if detectorName == self._currentDetectorName else None
            )

            # Set as default if first detector
            if self._currentDetectorName is None:
                self._currentDetectorName = detectorName

        # A timer will collect the new frame and update it through the communication channel
        self._lvWorker = LVWorker(self, updatePeriod)
        self._thread = Thread()
        self._lvWorker.moveToThread(self._thread)
        self._thread.started.connect(self._lvWorker.run)

    def hasDetectors(self):
        """ Returns whether this manager manages any detectors. """
        return self._currentDetectorName is not None

    def getAllDetectorNames(self):
        return list(self._subManagers.keys())

    def getCurrentDetectorName(self):
        if not self.hasDetectors():
            raise NoDetectorsError

        return self._currentDetectorName

    def getCurrentDetector(self):
        if not self.hasDetectors():
            raise NoDetectorsError

        return self._subManagers[self._currentDetectorName]

    def setCurrentDetector(self, detectorName):
        self._validateManagedDeviceName(detectorName)

        oldDetectorName = self._currentDetectorName
        self._currentDetectorName = detectorName
        self.sigDetectorSwitched.emit(detectorName, oldDetectorName)

        if self._thread.isRunning():
            self.execOnCurrent(lambda c: c.updateLatestFrame(True))

    def execOnCurrent(self, func):
        """ Executes a function on the current detector and returns the result. """
        if not self.hasDetectors():
            raise NoDetectorsError

        return self.execOn(self._currentDetectorName, func)

    def startAcquisition(self, liveView=False):
        self._activeAcqsMutex.lock()
        try:
            # Generate handle that will be used to stop acquisition
            handle = np.random.randint(2**31)

            # Add to handle list and set enable acquisition/LV flags if not already enabled
            if not liveView:
                self._activeAcqHandles.append(handle)
                enableLV = False
            else:
                self._activeAcqLVHandles.append(handle)
                enableLV = len(self._activeAcqLVHandles) == 1
            enableAcq = len(self._activeAcqHandles) + len(self._activeAcqLVHandles) == 1
        finally:
            self._activeAcqsMutex.unlock()

        # Do actual enabling
        if enableAcq:
            self.execOnAll(lambda c: c.startAcquisition())
            self.sigAcquisitionStarted.emit()
        if enableLV:
            sleep(0.3)
            self._thread.start()

        return handle

    def stopAcquisition(self, handle, liveView=False):
        self._activeAcqsMutex.lock()
        try:
            # Remove from handle list and set disable acquisition/LV flags if not already disabled
            if not liveView:
                if handle not in self._activeAcqHandles:
                    raise ValueError('Invalid or already used handle')

                self._activeAcqHandles.remove(handle)
                disableLV = False
            else:
                if handle not in self._activeAcqLVHandles:
                    raise ValueError('Invalid or already used handle')

                self._activeAcqLVHandles.remove(handle)
                disableLV = len(self._activeAcqLVHandles) < 1
            disableAcq = len(self._activeAcqHandles) < 1 and len(self._activeAcqLVHandles) < 1
        finally:
            self._activeAcqsMutex.unlock()

        # Do actual disabling
        if disableLV:
            self._thread.quit()
            self._thread.wait()
        if disableAcq:
            self.execOnAll(lambda c: c.stopAcquisition())
            self.sigAcquisitionStopped.emit()


class LVWorker(Worker):
    def __init__(self, detectorsManager, updatePeriod):
        super().__init__()
        self._detectorsManager = detectorsManager
        self._updatePeriod = updatePeriod

    def run(self):
        self._detectorsManager.execOnAll(lambda c: c.updateLatestFrame(False))
        self.vtimer = Timer()
        self.vtimer.timeout.connect(
            lambda: self._detectorsManager.execOnAll(lambda c: c.updateLatestFrame(True))
        )
        self.vtimer.start(self._updatePeriod)


class NoDetectorsError(RuntimeError):
    """ Error raised when a function related to the current detector is called
    if the DetectorsManager doesn't manage any detectors (i.e. the manager is
    initialized without any detectors). """
    pass


# Copyright (C) 2020, 2021 TestaLab
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

