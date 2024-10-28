from imswitch.imcommon.framework import SignalInterface, Signal
from .MultiManager import MultiManager


class RotatorsManager(MultiManager, SignalInterface):
    """ RotatorsManager interface for dealing with RotatorManagers. It is
    a MultiManager for rotators. """

    sigRotatorPositionUpdated = Signal(str)

    def __init__(self, rotatorsInfo, **lowLevelManagers):
        MultiManager.__init__(self, rotatorsInfo, 'rotators', **lowLevelManagers)
        SignalInterface.__init__(self)

        if rotatorsInfo:
            for rotatorName, rotatorInfo in rotatorsInfo.items():
                # Connect signals
                self._subManagers[rotatorName].sigRotatorPositionUpdated.connect(
                    lambda: self.sigRotatorPositionUpdated.emit(rotatorName)
                )


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
