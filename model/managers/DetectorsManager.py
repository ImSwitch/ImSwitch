import importlib
from time import sleep

import numpy as np

from framework import Signal, SignalInterface, Thread, Timer, Worker


class DetectorsManager(SignalInterface):
    """ DetectorsManager is an interface for dealing with DetectorManagers. """

    acquisitionStarted = Signal()
    acquisitionStopped = Signal()
    detectorSwitched = Signal(str, str)  # (newDetectorName, oldDetectorName)
    imageUpdated = Signal(np.ndarray, bool)  # (image, init)

    def __init__(self, detectorInfos, updatePeriod):
        super().__init__()

        self._detectorManagers = {}
        self._currentDetectorName = None
        for detectorName, detectorInfo in detectorInfos.items():
            # Create detector manager
            package = importlib.import_module('model.managers.detectors.' + detectorInfo.managerName)
            manager = getattr(package, detectorInfo.managerName)
            self._detectorManagers[detectorName] = manager(detectorInfo, detectorName)

            # Connect signals
            self._detectorManagers[detectorName].imageUpdated.connect(
                lambda image, init, detectorName=detectorName: self.imageUpdated.emit(
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
        return list(self._detectorManagers.keys())

    def getCurrentDetectorName(self):
        if not self.hasDetectors():
            raise NoDetectorsError

        return self._currentDetectorName

    def getCurrentDetector(self):
        if not self.hasDetectors():
            raise NoDetectorsError

        return self._detectorManagers[self._currentDetectorName]

    def setCurrentDetector(self, detectorName):
        if detectorName not in self._detectorManagers:
            raise NoSuchDetectorError(f'Detector "{detectorName}" does not exist or is not managed'
                                      f' by this DetectorsManager.')

        oldDetectorName = self._currentDetectorName
        self._currentDetectorName = detectorName
        self.detectorSwitched.emit(detectorName, oldDetectorName)
        if self._thread.isRunning():
            self.execOnCurrent(lambda c: c.updateLatestFrame(True))

    def execOn(self, detectorName, func):
        """ Executes a function on a specific detector and returns the result. """
        if detectorName not in self._detectorManagers:
            raise NoSuchDetectorError(f'Detector "{detectorName}" does not exist or is not managed'
                                      f' by this DetectorsManager.')

        return func(self._detectorManagers[detectorName])

    def execOnCurrent(self, func):
        """ Executes a function on the current detector and returns the result. """
        if not self.hasDetectors():
            raise NoDetectorsError

        return self.execOn(self._currentDetectorName, func)

    def execOnAll(self, func):
        """ Executes a function on all detectors and returns the results. """
        return {detectorName: func(detectorManager)
                for detectorName, detectorManager in self._detectorManagers.items()}

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


class NoSuchDetectorError(RuntimeError):
    """ Error raised when a function related to a detector is called if the
    detector is not managed by the DetectorsManager. """
    pass


class NoDetectorsError(RuntimeError):
    """ Error raised when a function related to the current detector is called
    if the DetectorsManager doesn't manage any detectors (i.e. the manager is
    initialized without any detectors). """
    pass
