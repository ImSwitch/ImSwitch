from qtpy import QtCore, QtWidgets


class BetterSlider(QtWidgets.QSlider):
    """ BetterSlider is a QSlider that allows disabling the slider's reactions
    to the mouse scroll wheel. """

    def __init__(self, *args, allowScrollChanges=True, **kwargs):
        super().__init__(*args, **kwargs)
        self._allowScrollChanges = allowScrollChanges
        self.installEventFilter(self)

    def eventFilter(self, source, event):
        if not self._allowScrollChanges and source is self and event.type() == QtCore.QEvent.Wheel:
            return True  # Don't change value

        return False


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
