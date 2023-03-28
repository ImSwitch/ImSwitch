from typing import Dict, List

from imswitch.imcommon.model import APIExport
from ..basecontrollers import ImConWidgetController
from imswitch.imcommon.model import initLogger


class StateSelectorController(ImConWidgetController):
    """ Linked to StateSelectorWidget."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.settingAttr = False

        self.__logger = initLogger(self, tryInheritParent=True)

        # Set up state selectors
        for ssName, ssManager in self._master.stateSelectorManager:
            self._widget.addStateSelector(ssName)

        # Connect StateSelectorWidget signals
        self._widget.sigItemChanged.connect(self.changeState)

    def changeState(self, state, stateSelectorName):
        self.move(stateSelectorName, state)

    def move(self, stateSelectorName, state):
        """ Moves positioner by dist micrometers in the specified axis. """
        self._master.stateSelectorManager[stateSelectorName].move(state)

_attrCategory = 'StateSelector'
_positionAttr = 'State'


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
