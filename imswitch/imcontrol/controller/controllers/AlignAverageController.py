import numpy as np

from .basecontrollers import LiveUpdatedController


class AlignAverageController(LiveUpdatedController):
    """ Linked to AlignWidgetAverage."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.addROI()

        # Connect CommunicationChannel signals
        self._commChannel.sigUpdateImage.connect(self.update)

        # Connect AlignWidgetAverage signals
        self._widget.sigShowROIToggled.connect(self.toggleROI)

    def update(self, im, init):
        """ Update with new detector frame. """
        if self.active:
            value = np.mean(
                self._commChannel.getROIdata(im, self._widget.getROIGraphicsItem())
            )
            self._widget.updateGraph(value)

    def addROI(self):
        """ Adds the ROI to ImageWidget viewbox through the CommunicationChannel. """
        self._commChannel.sigAddItemToVb.emit(self._widget.getROIGraphicsItem())

    def toggleROI(self, show):
        """ Show or hide ROI."""
        if show:
            ROIsize = (64, 64)
            ROIcenter = self._commChannel.getCenterROI()

            ROIpos = (ROIcenter[0] - 0.5 * ROIsize[0],
                      ROIcenter[1] - 0.5 * ROIsize[1])

            self._widget.showROI(ROIpos, ROIsize)
        else:
            self._widget.hideROI()

        self.active = show
        

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
