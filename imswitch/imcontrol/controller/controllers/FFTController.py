import numpy as np

from imswitch.imcommon.framework import Signal, Thread, Worker, Mutex
from imswitch.imcontrol.view import guitools
from ..basecontrollers import LiveUpdatedController


class FFTController(LiveUpdatedController):
    """ Linked to FFTWidget."""

    sigImageReceived = Signal()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.updateRate = 10
        self.it = 0
        self.init = False
        self.showPos = False

        # Prepare image computation worker
        self.imageComputationWorker = self.FFTImageComputationWorker()
        self.imageComputationWorker.sigFftImageComputed.connect(self.displayImage)
        self.imageComputationThread = Thread()
        self.imageComputationWorker.moveToThread(self.imageComputationThread)
        self.sigImageReceived.connect(self.imageComputationWorker.computeFFTImage)
        self.imageComputationThread.start()

        # Connect CommunicationChannel signals
        self._commChannel.sigUpdateImage.connect(self.update)

        # Connect FFTWidget signals
        self._widget.sigShowToggled.connect(self.setShowFFT)
        self._widget.sigPosToggled.connect(self.setShowPos)
        self._widget.sigPosChanged.connect(self.changePos)
        self._widget.sigUpdateRateChanged.connect(self.changeRate)
        self._widget.sigResized.connect(self.adjustFrame)

        self.changeRate(self._widget.getUpdateRate())
        self.setShowFFT(self._widget.getShowFFTChecked())
        self.setShowPos(self._widget.getShowPosChecked())

    def __del__(self):
        self.imageComputationThread.quit()
        self.imageComputationThread.wait()
        if hasattr(super(), '__del__'):
            super().__del__()

    def setShowFFT(self, enabled):
        """ Show or hide FFT. """
        self.active = enabled
        self.init = False

    def setShowPos(self, enabled):
        """ Show or hide lines. """
        self.showPos = enabled
        self.changePos(self._widget.getPos())

    def update(self, detectorName, im, init, scale, isCurrentDetector):
        """ Update with new detector frame. """
        if not isCurrentDetector or not self.active:
            return

        if self.it == self.updateRate:
            self.it = 0
            self.imageComputationWorker.prepareForNewImage(im)
            self.sigImageReceived.emit()
        else:
            self.it += 1

    def displayImage(self, im):
        """ Displays the image in the view. """
        prevIm = self._widget.getImage()
        shapeChanged = prevIm is None or im.shape != prevIm.shape
        self._widget.setImage(im)

        if shapeChanged or not self.init:
            self.adjustFrame()
            self._widget.setImageDisplayLevels(*guitools.bestLevels(im))
            self.init = True

    def adjustFrame(self):
        im = self._widget.getImage()
        if im is None:
            return

        self._widget.updateImageLimits(im.shape[1], im.shape[0])

    def changeRate(self, updateRate):
        """ Change update rate. """
        self.updateRate = updateRate
        self.it = 0

    def changePos(self, pos):
        """ Change positions of lines.  """
        if not self.showPos or pos == 0:
            self._widget.setPosLinesVisible(False)
        else:
            im = self._widget.getImage()
            if im is None:
                return

            pos = float(1 / pos)
            imgWidth = im.shape[1]
            imgHeight = im.shape[0]
            self._widget.updatePosLines(pos, imgWidth, imgHeight)
            self._widget.setPosLinesVisible(True)

    class FFTImageComputationWorker(Worker):
        sigFftImageComputed = Signal(np.ndarray)

        def __init__(self):
            super().__init__()
            self._numQueuedImages = 0
            self._numQueuedImagesMutex = Mutex()

        def computeFFTImage(self):
            """ Compute FFT of an image. """
            try:
                if self._numQueuedImages > 1:
                    return  # Skip this frame in order to catch up

                fftImage = np.fft.fftshift(np.log10(abs(np.fft.fft2(self._image))))
                self.sigFftImageComputed.emit(fftImage)
            finally:
                self._numQueuedImagesMutex.lock()
                self._numQueuedImages -= 1
                self._numQueuedImagesMutex.unlock()

        def prepareForNewImage(self, image):
            """ Must always be called before the worker receives a new image. """
            self._image = image
            self._numQueuedImagesMutex.lock()
            self._numQueuedImages += 1
            self._numQueuedImagesMutex.unlock()


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
