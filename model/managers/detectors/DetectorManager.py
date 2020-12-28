from abc import abstractmethod
from dataclasses import dataclass
from typing import List, Any

import numpy as np
from framework import Signal, SignalInterface


@dataclass
class DetectorParameter:
    group: str
    value: Any
    editable: bool


@dataclass
class DetectorNumberParameter(DetectorParameter):
    value: float
    valueUnits: str


@dataclass
class DetectorListParameter(DetectorParameter):
    value: str
    options: List[str]


class DetectorManager(SignalInterface):
    imageUpdated = Signal(np.ndarray, bool)

    @abstractmethod
    def __init__(self, name, fullShape, supportedBinnings, model, parameters):
        super().__init__()

        self._name = name
        self._model = model
        self._parameters = parameters

        self._frameStart = (0, 0)
        self._shape = fullShape
        self._fullShape = fullShape
        self._supportedBinnings = supportedBinnings
        self._image = np.array([])

        self.setBinning(supportedBinnings[0])

    def updateLatestFrame(self, init):
        self._image = self.getLatestFrame()
        self.imageUpdated.emit(self._image, init)

    def setParameter(self, name, value):
        """Sets a parameter value and returns the updated list of parameters.
        If the parameter doesn't exist, i.e. the parameters field doesn't
        contain a key with the specified parameter name, an error will be
        raised."""

        if name not in self._parameters:
            raise AttributeError(f'Non-existent parameter "{name}" specified')

        self._parameters[name].value = value
        return self.parameters

    @property
    def name(self):
        return self._name

    @property
    def model(self):
        return self._model

    @property
    def binning(self):
        return self._binning

    @property
    def supportedBinnings(self):
        return self._supportedBinnings

    @property
    def frameStart(self):
        return self._frameStart

    @property
    def shape(self):
        return self._shape

    @property
    def fullShape(self):
        return self._fullShape

    @property
    def image(self):
        return self._image

    @property
    def parameters(self):
        return self._parameters

    @property
    @abstractmethod
    def pixelSize(self):
        pass

    @abstractmethod
    def setBinning(self, binning):
        if binning not in self._supportedBinnings:
            raise ValueError(f'Specified binning value "{binning}" not supported by the detector')

        self._binning = binning

    @abstractmethod
    def crop(self, hpos, vpos, hsize, vsize):
        """Method to crop the frame read out by the detector."""
        pass

    @abstractmethod
    def getLatestFrame(self):
        """Returns the frame that represents what the detector currently is
        capturing."""
        pass

    @abstractmethod
    def getChunk(self):
        """Returns the frames captured by the detector since getChunk was last
        called, or since the buffers were last flushed (whichever happened
        last)."""
        pass

    @abstractmethod
    def flushBuffers(self):
        """Flushes the detector buffers so that getChunk starts at the last
        frame captured at the time that this function was called."""
        pass

    @abstractmethod
    def startAcquisition(self):
        pass

    @abstractmethod
    def stopAcquisition(self):
        pass
