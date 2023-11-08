import importlib
from abc import ABC, abstractmethod

from imswitch.imcommon.model import pythontools, initLogger
from ..errors import InvalidChildClassError


class SignalDesigner(ABC):
    """Parent class for any type of SignalDesigner. Any child should define
    self._expected_parameters and its own make_signal method."""

    def __init__(self):
        self._logger = initLogger(self)

        self.lastSignal = None
        self.lastParameterDict = None
        self._expectedParameters = None

    @property
    def expectedParameters(self):
        if self._expectedParameters is None:
            raise ValueError('Value "%s" is not defined')
        else:
            return self._expectedParameters

    def isValidSignalDesigner(self):
        if self._expectedParameters is None:
            raise InvalidChildClassError('Child of SignalDesigner should define \
                                 "self.expected_parameters" in __init__.')
        else:
            return True

    def parameterCompatibility(self, parameterDict):
        """ Method to check the compatibility of parameter 'parameterDict'
        and the expected parameters of the object. """
        expected = set(self._expectedParameters)
        incoming = set([*parameterDict])

        return expected.issubset(incoming)

    @abstractmethod
    def make_signal(self, parameterDict, setupInfo):
        """ Method to be defined by child. Should return a dictionary with
        {'target': signal} pairs. """
        pass


class ScanDesigner(SignalDesigner, ABC):
    @abstractmethod
    def checkSignalComp(self, scanParameters, setupInfo, scanInfo):
        """ Check analog scanning signals so that they are inside the range of
        the acceptable scanner voltages."""
        pass

    def checkSignalLength(self, scanParameters, setupInfo):
        """ Check that the signal would not be too large (to be stored in
        the RAM and to be generated and run inside a reasonable time). """
        return True

    @abstractmethod
    def make_signal(self, parameterDict, setupInfo):
        """ Method to be defined by child. Should return a dictionary with
        {'target': signal} pairs. """
        pass


class TTLCycleDesigner(SignalDesigner, ABC):
    @property
    @abstractmethod
    def timeUnits(self):
        pass

    @abstractmethod
    def make_signal(self, parameterDict, setupInfo, scanInfoDict=None):
        """ Method to be defined by child. Should return a dictionary with
        {'target': signal} pairs. """
        pass


class SignalDesignerFactory:
    """Factory class for creating a SignalDesigner object. Factory checks
    that the new object is compatible with the parameters that will we
    be sent to its make_signal method."""

    def __new__(cls, designerName):
        currentPackage = '.'.join(__name__.split('.')[:-1])
        package = importlib.import_module(pythontools.joinModulePath(currentPackage, designerName))
        signalDesigner = getattr(package, designerName)()

        if signalDesigner.isValidSignalDesigner():
            return signalDesigner


# Copyright (C) 2020-2023 ImSwitch developers
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
