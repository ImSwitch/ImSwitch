import time

import numpy as np
from time import perf_counter
import scipy.ndimage as ndi
from scipy.ndimage.filters import laplace

from imswitch.imcommon.framework import Thread, Timer
from imswitch.imcommon.model import initLogger, APIExport
from ..basecontrollers import ImConWidgetController

# global axis for Z-positioning - should be Z
gAxis = "Z" 
T_DEBOUNCE = .2
class AutofocusController(ImConWidgetController):
    """Linked to AutofocusWidget."""

    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__logger = initLogger(self)

        if self._setupInfo.autofocus is None:
            return

        self.camera = self._setupInfo.autofocus.camera
        self.positioner = self._setupInfo.autofocus.positioner
        #self._master.detectorsManager[self.camera].crop(*self.cropFrame)

        # Connect AutofocusWidget buttons
        self._widget.focusButton.clicked.connect(self.focusButton)

        self._master.detectorsManager[self.camera].startAcquisition()
        self.__processDataThread = ProcessDataThread(self)
        self._commChannel.sigAutoFocus.connect(self.autoFocus)

    def __del__(self):
        self.__processDataThread.quit()
        self.__processDataThread.wait()
        if hasattr(super(), '__del__'):
            super().__del__()

    def focusButton(self):
        rangez = float(self._widget.zStepRangeEdit.text())
        resolutionz = float(self._widget.zStepSizeEdit.text())
        self._widget.focusButton.setText('Stop')
        self.autoFocus(rangez,resolutionz)
        self._widget.focusButton.setText('Autofocus')

    @APIExport(runOnUIThread=True)
    # Update focus lock
    def autoFocus(self, rangez=100, resolutionz=10):

        '''
        The stage moves from -rangez...+rangez with a resolution of resolutionz
        For every stage-position a camera frame is captured and a contrast curve is determined

        '''
        # determine optimal focus position by stepping through all z-positions and cacluate the focus metric
        self.focusPointSignal = self.__processDataThread.update(rangez,resolutionz)

class ProcessDataThread(Thread):
    def __init__(self, controller, *args, **kwargs):
        self._controller = controller
        super().__init__(*args, **kwargs)

    def grabCameraFrame(self):
        detectorManager = self._controller._master.detectorsManager[self._controller.camera]
        self.latestimg = detectorManager.getLatestFrame()
        return self.latestimg

    def update(self, rangez, resolutionz):

        allfocusvals = []
        allfocuspositions = []

        
        # 0 move focus to initial position
        self._controller._master.positionersManager[self._controller.positioner].move(-rangez, axis=gAxis)
        img = self.grabCameraFrame()     # grab dummy frame?
        # store data
        Nz = int(2*rangez//resolutionz)
        allfocusvals = np.zeros(Nz)
        allfocuspositions  = np.zeros(Nz)
        allfocusimages = []

        # 1 compute focus for every z position
        for iz in range(Nz):

            # 0 Move stage to the predefined position - remember: stage moves in relative coordinates
            self._controller._master.positionersManager[self._controller.positioner].move(resolutionz, axis=gAxis)
            time.sleep(T_DEBOUNCE)
            positionz = iz*resolutionz
            self._controller._logger.debug(f'Moving focus to {positionz}')

            # 1 Grab camera frame
            self._controller._logger.debug("Grabbing Frame")
            img = self.grabCameraFrame()
            allfocusimages.append(img)

            # 2 Gaussian filter the image, to remove noise
            self._controller._logger.debug("Processing Frame")
            #img_norm = img-np.min(img)
            #img_norm = img_norm/np.mean(img_norm)
            imagearraygf = ndi.filters.gaussian_filter(img, 3)

            # 3 compute focus metric
            focusquality = np.mean(ndi.filters.laplace(imagearraygf))
            allfocusvals[iz]=focusquality
            allfocuspositions[iz] = positionz

        # display the curve
        self._controller._widget.focusPlotCurve.setData(allfocuspositions,allfocusvals)

        # 4 find maximum focus value and move stage to this position
        allfocusvals=np.array(allfocusvals)
        zindex=np.where(np.max(allfocusvals)==allfocusvals)[0]
        bestzpos = allfocuspositions[np.squeeze(zindex)]

         # 5 move focus back to initial position (reduce backlash)
        self._controller._master.positionersManager[self._controller.positioner].move(-Nz*resolutionz, axis=gAxis)

        # 6 Move stage to the position with max focus value
        self._controller._logger.debug(f'Moving focus to {zindex*resolutionz}')
        self._controller._master.positionersManager[self._controller.positioner].move(zindex*resolutionz, axis=gAxis)


        # DEBUG
        allfocusimages=np.array(allfocusimages)
        np.save('allfocusimages.npy', allfocusimages)
        import tifffile as tif
        tif.imsave("llfocusimages.tif", allfocusimages)
        np.save('allfocuspositions.npy', allfocuspositions)
        np.save('allfocusvals.npy', allfocusvals)

        return bestzpos

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
