import time

import numpy as np

from imswitch.imcommon.framework import Thread, Worker, Signal
from ..basecontrollers import ImConWidgetController
from skimage.transform import rescale
from tifffile import imsave

class BeadRecController(ImConWidgetController):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.running = False
        self.roiAdded = False
        self.newScan = False
        self.parametersChanged = False
        self.dims = None
        self.stepSizes = None

        self.beadWorker = BeadWorker(self)
        self.beadWorker.sigNewChunk.connect(self.update)
        self.thread = Thread()
        self.beadWorker.moveToThread(self.thread)
        self.thread.started.connect(self.beadWorker.run)

        # Connect BeadRecWidget signals
        self._widget.sigROIToggled.connect(self.roiToggled)
        self._widget.sigRunClicked.connect(self.run)
        self._widget.sigScaleClicked.connect(self.updateScaling)

        # Connect comm channel signals
        self._commChannel.sigScanStarted.connect(self.updateParameters)
        self._commChannel.sigScanStarted.connect(self.setNewScanStatus)

    def __del__(self):
        self.thread.quit()
        self.thread.wait()
        if hasattr(super(), '__del__'):
            super().__del__()

    def roiToggled(self, enabled):
        """ Show or hide ROI."""
        if enabled:
            self.addROI()

            ROIsize = (64, 64)
            ROIcenter = self._commChannel.getCenterViewbox()

            ROIpos = (ROIcenter[0] - 0.5 * ROIsize[0],
                      ROIcenter[1] - 0.5 * ROIsize[1])

            self._widget.showROI(ROIpos, ROIsize)
        else:
            self._widget.hideROI()

    def addROI(self):
        """ Adds the ROI to ImageWidget viewbox through the CommunicationChannel. """
        if not self.roiAdded:
            self._commChannel.sigAddItemToVb.emit(self._widget.getROIGraphicsItem())
            self.roiAdded = True

    def run(self):
        if not self.running:
            self.updateParameters()
            self.running = True
            self._master.detectorsManager.execOnAll(lambda c: c.flushBuffers())
            self.thread.start()
        else:
            self.running = False
            self.thread.quit()
            self.thread.wait()

    def setNewScanStatus(self):
        self.newScan = True

    def updateParameters(self):
        prior_dims = self.dims
        prior_stepSizes = self.stepSizes
        self.dims = np.array(self._commChannel.getDimsScan()).astype(int)
        self.stepSizes = np.array(self._commChannel.getScanStepSizes(),dtype=float)[self.dims!=0]
        self.dims = self.dims[self.dims != 0]
        if len(self.dims)>2:
            self.dims = self.dims[:2]
            self._logger.warning("Using only first 2 dimensions of 3d scan")
        
        if prior_dims is not None and prior_stepSizes is not None:
            if len(prior_dims) != len(self.dims) or (prior_dims != self.dims).any() or \
                len(prior_stepSizes) != len(self.stepSizes) or (prior_stepSizes != self.stepSizes).any():
                
                self.parametersChanged = True


    def updateScaling(self):
        if not self._commChannel.isScanRunning():
            self.update()

    def rescale(self,im):
        """
        Rescale imRec if not isotropic scan. Uses scikit rescale function, without interpolation.
        """
        px_y = self.stepSizes[1] # (y,x) in recIm, so inversed to the scan XY.
        px_x = self.stepSizes[0]
        if px_y - px_x == 0:
            return im
        scale_x = px_x / min(px_x, px_y)
        scale_y = px_y / min(px_x, px_y)
        rescaled_im = rescale(im, (scale_y, scale_x), anti_aliasing=False, mode='reflect', preserve_range=True)  
        # imsave(r"C:\Users\MonaLisa\Documents\rescaled.tiff",rescaled_im) #to debug scaling
        return rescaled_im
    
    def update(self):
        im_display = np.resize(self.recIm, (self.dims[1] + 1,self.dims[0] + 1))
        if self._widget.scaleButton.isChecked():
            im_display = self.rescale(im_display)
        self._widget.updateImage(im_display)


class BeadWorker(Worker):
    sigNewChunk = Signal()

    def __init__(self, controller):
        super().__init__()
        self.__controller = controller
    
    def init1DArray(self):
        dims = np.array(self.__controller.dims)
        N = (dims[0] + 1) * (dims[1] + 1)
        self.__controller.recIm = np.zeros(N)
        return N

    def run(self):
        N = self.init1DArray()
        i = 0

        while self.__controller.running:

            if self.__controller.newScan:
                self.__controller.newScan = False
                i = 0
            
            if self.__controller.parametersChanged:
                self.__controller.parametersChanged = False
                N = self.init1DArray()

            if self.__controller._commChannel.isScanRunning():
                newImages = self.__controller._master.detectorsManager.execOnCurrent(
                    lambda c: c.getChunk()
                )
                n = len(newImages)
                if n > 0:
                    roiItem = self.__controller._widget.getROIGraphicsItem()
                    x0, y0, x1, y1 = roiItem.bounds

                    for j in range(0, n):
                        img = newImages[j]
                        img = img[y0:y1, x0:x1]
                        mean = np.mean(img)
                        self.__controller.recIm[i] = mean
                        i = i + 1
                        if i == N:
                            i = 0
                    self.sigNewChunk.emit()

            time.sleep(0.0001)  # Prevents freezing


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
