from time import sleep

import numpy as np

from framework import Signal, SignalInterface, Thread, Timer, Worker
from .MultiManager import MultiManager


class DetectorsManager(MultiManager, SignalInterface):
    """ DetectorsManager is an interface for dealing with DetectorManagers. """

    acquisitionStarted = Signal()
    acquisitionStopped = Signal()
    detectorSwitched = Signal(list, list)  # (newDetectorNames, oldDetectorNames)
    imageUpdated = Signal(str, np.ndarray, bool)  # (detectorName, image, init)

    def __init__(self, detectorInfos, updatePeriod, **kwargs):
        MultiManager.__init__(self, detectorInfos, 'detectors', **kwargs)
        SignalInterface.__init__(self)

        self._currentDetectorNames = None
        for detectorName, detectorInfo in detectorInfos.items():
            # Connect signals
            self._subManagers[detectorName].imageUpdated.connect(
                lambda image, init, detectorName=detectorName: self.imageUpdated.emit(
                    detectorName, image, init
                ) if detectorName in self._currentDetectorNames else None
            )

            # Set as default if first detector
            if self._currentDetectorNames is None:
                self._currentDetectorNames = list(detectorInfos.keys())

        # A timer will collect the new frame and update it through the communication channel
        self._lvWorker = LVWorker(self, updatePeriod)
        self._thread = Thread()
        self._lvWorker.moveToThread(self._thread)
        self._thread.started.connect(self._lvWorker.run)

    def hasDetectors(self):
        """ Returns whether this manager manages any detectors. """
        return self._currentDetectorNames is not None

    def getAllDetectorNames(self):
        return list(self._subManagers.keys())

    def getCurrentDetectorNames(self):
        if not self.hasDetectors():
            raise NoDetectorsError

        return self._currentDetectorNames

    def setCurrentDetectors(self, detectorNames):
        for detectorName in detectorNames:
            self._validateManagedDeviceName(detectorName)

        oldDetectorNames = self._currentDetectorNames
        self._currentDetectorNames = detectorNames
        self.detectorSwitched.emit(detectorNames, oldDetectorNames)

        if self._thread.isRunning():
            self.execOnCurrent(lambda c: c.updateLatestFrame(True))

    def execOnCurrent(self, func):
        """ Executes a function on the current detector and returns the result. """
        if not self.hasDetectors():
            raise NoDetectorsError

        return {managedDeviceName: func(subManager)
                for managedDeviceName, subManager in self._subManagers.items()
                if managedDeviceName in self._currentDetectorNames}

    def startAcquisition(self):
        self.execOnAll(lambda c: c.startAcquisition())
        self.acquisitionStarted.emit()
        sleep(0.3)
        self._thread.start()

    def stopAcquisition(self):
        self._thread.quit()
        self._thread.wait()
        self.execOnAll(lambda c: c.stopAcquisition())
        self.acquisitionStopped.emit()


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
