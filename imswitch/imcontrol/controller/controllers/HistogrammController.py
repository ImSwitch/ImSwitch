import numpy as np

try:
    import NanoImagingPack as nip
    isNIP = True
except:
    isNIP = False


from imswitch.imcommon.framework import Signal, Thread, Worker, Mutex
from imswitch.imcontrol.view import guitools
from imswitch.imcommon.model import initLogger
from ..basecontrollers import LiveUpdatedController


class HistogrammController(LiveUpdatedController):
    """ Linked to HistogrammWidget."""

    sigImageReceived = Signal()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.updateRate = 10
        self.it = 0
        
        # Connect CommunicationChannel signals
        self._commChannel.sigUpdateImage.connect(self.update)

    def update(self, detectorName, im, init, isCurrentDetector):
        """ Update with new detector frame. """


        # compute histogramm and show
        hist, bins = np.histogram(im[:], bins=50)
        width = 0.7 * (bins[1] - bins[0])
        center = (bins[:-1] + bins[1:]) / 2

        # display the curve
        self._widget.histogrammPlotCurve.setData(center,hist)




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
