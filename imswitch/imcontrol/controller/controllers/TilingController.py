from ..basecontrollers import ImConWidgetController
from imswitch.imcommon.model import APIExport
import numpy as np


class TilingController(ImConWidgetController):
    """ Linked to WatcherWidget. """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._widget.sigSaveFocus.connect(self.saveFocus)
        self._image = []
        self._skipOrNot = None

    def saveFocus(self, bool):
        self._skipOrNot = bool
        self._commChannel.sigSaveFocus.emit()

    @APIExport()
    def setTileLabel(self, label) -> None:
        self._widget.setLabel(label)

    @APIExport()
    def getSkipOrNot(self) -> bool:
        return self._skipOrNot

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
