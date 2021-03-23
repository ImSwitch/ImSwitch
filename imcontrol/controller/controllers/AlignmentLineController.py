from .basecontrollers import ImConWidgetController


class AlignmentLineController(ImConWidgetController):
    """ Linked to AlignmentLineWidget."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.addLine()

        # Connect AlignmentLineWidget signals
        self._widget.sigAlignmentLineMakeClicked.connect(self.updateLine)
        self._widget.sigAlignmentCheckToggled.connect(self.show)

    def addLine(self):
        """ Adds alignmentLine to ImageWidget viewbox through the CommunicationChannel. """
        self._commChannel.sigAddItemToVb.emit(self._widget.alignmentLine)

    def updateLine(self):
        """ Updates line with new parameters. """
        self._widget.setLineAngle(self._widget.getAngleInput())

    def show(self, enabled):
        """ Shows or hides line. """
        self._widget.setLineVisibility(enabled)
    

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
