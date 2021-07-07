import traceback
from abc import abstractmethod
from dataclasses import dataclass
from typing import Any, Callable, List

import numpy as np
from imswitch.imcommon.framework import Signal, SignalInterface


@dataclass
class DetectorAction:
    group: str
    func: Callable[[], Any]


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
    """ Abstract class for a manager for controlling detectors. Intended to be
    extended for each type of detector. """

    sigImageUpdated = Signal(np.ndarray, bool)

    @abstractmethod
    def __init__(self, detectorInfo, name, fullShape, supportedBinnings, model, *,
                 parameters=None, actions=None, croppable=True):
        super().__init__()

        self._detectorInfo = detectorInfo

        self._frameStart = (0, 0)
        self._shape = fullShape

        self.__name = name
        self.__model = model
        self.__parameters = parameters if parameters is not None else {}
        self.__actions = actions if actions is not None else {}
        self.__croppable = croppable

        self.__fullShape = fullShape
        self.__supportedBinnings = supportedBinnings
        self.__image = np.array([])

        self.__forAcquisition = detectorInfo.forAcquisition
        self.__forFocusLock = detectorInfo.forFocusLock
        if not detectorInfo.forAcquisition and not detectorInfo.forFocusLock:
            raise ValueError('At least one of forAcquisition and forFocusLock must be set in'
                             ' DetectorInfo.')

        self.setBinning(supportedBinnings[0])

    def updateLatestFrame(self, init):
        try:
            self.__image = self.getLatestFrame()
        except Exception:
            print(traceback.format_exc())
        else:
            self.sigImageUpdated.emit(self.__image, init)

    def setParameter(self, name, value):
        """Sets a parameter value and returns the updated list of parameters.
        If the parameter doesn't exist, i.e. the parameters field doesn't
        contain a key with the specified parameter name, an error will be
        raised."""

        if name not in self.__parameters:
            raise AttributeError(f'Non-existent parameter "{name}" specified')

        self.__parameters[name].value = value
        return self.parameters

    @property
    def name(self):
        """ Detector name (same as in detector setup info). """
        return self.__name

    @property
    def model(self):
        """ Detector model name. """
        return self.__model

    @property
    def binning(self):
        """ Current binning. """
        return self._binning

    @property
    def supportedBinnings(self):
        """ Supported binnings as a list. """
        return self.__supportedBinnings

    @property
    def frameStart(self):
        """ Position of the top left corner of the current frame as a tuple
        (width, height). """
        return self._frameStart

    @property
    def shape(self):
        """ Current frame size as a tuple (width, height). """
        return self._shape

    @property
    def fullShape(self):
        """ Full image size as a tuple (width, height). """
        return self.__fullShape

    @property
    def image(self):
        return self.__image

    @property
    def parameters(self):
        """ Dictionary { str: DetectorParameter } of available parameters. """
        return self.__parameters

    @property
    def actions(self):
        """ Dictionary { str: DetectorAction } of available actions. """
        return self.__actions

    @property
    def croppable(self):
        """ Whether the detector supports frame cropping. """
        return self.__croppable

    @property
    def forAcquisition(self):
        """ Whether the detector is used for acquisition. """
        return self.__forAcquisition

    @property
    def forFocusLock(self):
        """ Whether the detector is used for focus lock. """
        return self.__forFocusLock

    @property
    @abstractmethod
    def pixelSizeUm(self):
        """The pixel size in micrometers."""
        pass

    @abstractmethod
    def setBinning(self, binning):
        if binning not in self.__supportedBinnings:
            raise ValueError(f'Specified binning value "{binning}" not supported by the detector')

        self._binning = binning

    @abstractmethod
    def crop(self, hpos, vpos, hsize, vsize):
        """Method to crop the frame read out by the detector."""
        pass

    @abstractmethod
    def getLatestFrame(self):
        """Returns the frame that represents what the detector currently is
        capturing. The returned object is a numpy array of shape
        (height, width)."""
        pass

    @abstractmethod
    def getChunk(self):
        """Returns the frames captured by the detector since getChunk was last
        called, or since the buffers were last flushed (whichever happened
        last). The returned object is a numpy array of shape
        (numFrames, height, width)."""
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

    def finalize(self):
        """ Close/cleanup detector. """
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
