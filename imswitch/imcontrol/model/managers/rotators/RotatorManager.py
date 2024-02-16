from abc import abstractmethod
from imswitch.imcommon.framework import Signal, SignalInterface

class RotatorManager(SignalInterface):
    """ Abstract base class for managers that control rotators. Each type of
    rotator corresponds to a manager derived from this class. """

    sigOptStepDone = Signal()

    @abstractmethod
    def __init__(self, rotatorInfo, name: str, *args, **kwargs):
        """
        Args:
            rotatorInfo: See setup file documentation.
            name: The unique name that the device is identified with in the
              setup file.
        """
        self._rotatorInfo = rotatorInfo
        self._position = 0
        self.__name = name

    @property
    def name(self) -> str:
        """ Unique rotator name, defined in the rotator's setup info. """
        return self.__name

    @property
    def position(self) -> float:
        """ The position. """
        return self._position

    @abstractmethod
    def move_rel(self, move_dist: float):
        """ Moves the rotator by the specified distance.
        Derived classes will update the position field manually;
        position updates can be monitored by implementing the
        sigOptStepDone signal in the derived class.
        """
        pass

    @abstractmethod
    def move_abs(self, move_pos: float):
        """ Adjusts the rotator to the specified position.
        Derived classes will update the position field manually;
        position updates can be monitored by implementing the
        sigOptStepDone signal in the derived class.
        """
        pass

    def finalize(self) -> None:
        """ Close/cleanup rotator. """
        pass


# Copyright (C) 2020-2022 ImSwitch developers
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
