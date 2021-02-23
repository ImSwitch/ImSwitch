import numpy as np

from imcommon.framework import Signal, Thread, Worker, Mutex
from .basecontrollers import LiveUpdatedController
from imcontrol.view import guitools as guitools


class FFTController(LiveUpdatedController):
    """ Linked to FFTWidget."""

    sigImageReceived = Signal()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.updateRate = 10
        self.it = 0
        self.init = False
        self.show = False

        # Prepare image computation worker
        self.imageComputationWorker = self.FFTImageComputationWorker()
        self.imageComputationWorker.fftImageComputed.connect(self.displayImage)
        self.imageComputationThread = Thread()
        self.imageComputationWorker.moveToThread(self.imageComputationThread)
        self.sigImageReceived.connect(self.imageComputationWorker.computeFFTImage)
        self.imageComputationThread.start()

        # Connect CommunicationChannel signals
        self._commChannel.imageUpdated.connect(self.update)

        # Connect FFTWidget signals
        self._widget.sigShowToggled.connect(self.showFFT)
        self._widget.sigChangePosClicked.connect(self.changePos)
        self._widget.sigPosChanged.connect(self.changePos)
        self._widget.sigUpdateRateChanged.connect(self.changeRate)
        self._widget.sigResized.connect(self.adjustFrame)

        self.changeRate(self._widget.getUpdateRate())
        self.showFFT(self._widget.getShowChecked())

    def showFFT(self, enabled):
        """ Show or hide FFT. """
        self.active = enabled
        self.init = False
        self._widget.img.setOnlyRenderVisible(enabled, render=False)

    def update(self, detectorName, im, init, isCurrentDetector):
        """ Update with new detector frame. """
        if not isCurrentDetector:
            return

        if self.active and (self.it == self.updateRate):
            self.it = 0
            self.imageComputationWorker.prepareForNewImage(im)
            self.sigImageReceived.emit()
        elif self.active and (not (self.it == self.updateRate)):
            self.it += 1

    def displayImage(self, im):
        """ Displays the image in the view. """
        shapeChanged = self._widget.img.image is None or im.shape != self._widget.img.image.shape
        self._widget.img.setImage(im, autoLevels=False)

        if shapeChanged or not self.init:
            self.adjustFrame()
            self._widget.hist.setLevels(*guitools.bestLevels(im))
            self._widget.hist.vb.autoRange()
            self.init = True

    def adjustFrame(self):
        width, height = self._widget.img.width(), self._widget.img.height()
        if width is None or height is None:
            return

        guitools.setBestImageLimits(self._widget.vb, width, height)

    def changeRate(self, updateRate):
        """ Change update rate. """
        self.updateRate = updateRate
        self.it = 0

    def changePos(self, pos):
        """ Change positions of lines.  """
        if (pos == self.show) or pos == 0:
            self._widget.vline.hide()
            self._widget.hline.hide()
            self._widget.rvline.hide()
            self._widget.lvline.hide()
            self._widget.uhline.hide()
            self._widget.dhline.hide()
            self.show = 0
        else:
            self.show = pos
            pos = float(1 / pos)
            imgWidth = self._widget.img.width()
            imgHeight = self._widget.img.height()
            # self._widget.vb.setAspectLocked()
            # self._widget.vb.setLimits(xMin=-0.5, xMax=imgWidth, minXRange=4,
            #                           yMin=-0.5, yMax=imgHeight, minYRange=4)
            self._widget.vline.setValue(0.5 * imgWidth)
            self._widget.hline.setAngle(0)
            self._widget.hline.setValue(0.5 * imgHeight)
            self._widget.rvline.setValue((0.5 + pos) * imgWidth)
            self._widget.lvline.setValue((0.5 - pos) * imgWidth)
            self._widget.dhline.setAngle(0)
            self._widget.dhline.setValue((0.5 - pos) * imgHeight)
            self._widget.uhline.setAngle(0)
            self._widget.uhline.setValue((0.5 + pos) * imgHeight)
            self._widget.vline.show()
            self._widget.hline.show()
            self._widget.rvline.show()
            self._widget.lvline.show()
            self._widget.uhline.show()
            self._widget.dhline.show()

    class FFTImageComputationWorker(Worker):
        fftImageComputed = Signal(np.ndarray)

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
                self.fftImageComputed.emit(fftImage)
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