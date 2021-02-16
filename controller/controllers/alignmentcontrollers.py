# -*- coding: utf-8 -*-
"""
Created on Sun Mar 22 10:40:53 2020

@author: _Xavi
"""
import numpy as np
import pyqtgraph as pg

import view.guitools as guitools
from framework import Mutex, Signal, Thread, Worker
from .basecontrollers import WidgetController, LiveUpdatedController


class ULensesController(WidgetController):
    """ Linked to ULensesWidget. """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.addPlot()

        # Connect ULensesWidget signals
        self._widget.sigULensesClicked.connect(self.updateGrid)
        self._widget.sigUShowLensesChanged.connect(self.toggleULenses)

    def addPlot(self):
        """ Adds ulensesPlot to ImageWidget viewbox through the CommunicationChannel. """
        self._commChannel.addItemTovb.emit(self._widget.getPlotGraphicsItem())

    def updateGrid(self):
        """ Updates plot with new parameters. """
        x, y, px, up = self._widget.getParameters()
        size_x, size_y = self._master.detectorsManager.execOnCurrent(lambda c: c.shape)
        pattern_x = np.arange(x, size_x, up / px)
        pattern_y = np.arange(y, size_y, up / px)
        grid = np.array(np.meshgrid(pattern_x, pattern_y)).T.reshape(-1, 2)
        self._widget.setData(x=grid[:, 0], y=grid[:, 1])

    def toggleULenses(self, show):
        """ Shows or hides grid. """
        self._widget.ulensesPlot.setVisible(show)


class AlignXYController(LiveUpdatedController):
    """ Linked to AlignWidgetXY. """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.axis = 0
        self.addROI()

        # Connect CommunicationChannel signals
        self._commChannel.imageUpdated.connect(self.update)

        # Connect AlignWidgetXY signals
        self._widget.sigShowROIToggled.connect(self.toggleROI)
        self._widget.sigAxisChanged.connect(self.setAxis)

    def update(self, detectorName, im, init, isCurrentDetector):
        """ Update with new detector frame. """
        if isCurrentDetector and self.active:
            value = np.mean(
                self._commChannel.getROIdata(im, self._widget.getROIGraphicsItem()),
                self.axis
            )
            self._widget.updateGraph(value)

    def addROI(self):
        """ Adds the ROI to ImageWidget viewbox through the CommunicationChannel. """
        self._commChannel.addItemTovb.emit(self._widget.getROIGraphicsItem())

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
        self._widget.updateDisplayState(show)

    def setAxis(self, axis):
        """ Setter for the axis (X or Y). """
        self.axis = axis


class AlignAverageController(LiveUpdatedController):
    """ Linked to AlignWidgetAverage."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.addROI()

        # Connect CommunicationChannel signals
        self._commChannel.imageUpdated.connect(self.update)

        # Connect AlignWidgetAverage signals
        self._widget.sigShowROIToggled.connect(self.toggleROI)

    def update(self, detectorName, im, init, isCurrentDetector):
        """ Update with new detector frame. """
        if isCurrentDetector and self.active:
            value = np.mean(
                self._commChannel.getROIdata(im, self._widget.getROIGraphicsItem())
            )
            self._widget.updateGraph(value)

    def addROI(self):
        """ Adds the ROI to ImageWidget viewbox through the CommunicationChannel. """
        self._commChannel.addItemTovb.emit(self._widget.getROIGraphicsItem())

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
        self._widget.updateDisplayState(show)


class AlignmentLineController(WidgetController):
    """ Linked to AlignmentLineWidget."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.addLine()

        # Connect AlignmentLineWidget signals
        self._widget.sigAlignmentLineMakeClicked.connect(self.updateLine)
        self._widget.sigAlignmentCheckToggled.connect(self.show)

    def addLine(self):
        """ Adds alignmentLine to ImageWidget viewbox through the CommunicationChannel. """
        self._commChannel.addItemTovb.emit(self._widget.alignmentLine)

    def updateLine(self):
        """ Updates line with new parameters. """
        self._widget.setLineAngle(self._widget.getAngleInput())

    def show(self, enabled):
        """ Shows or hides line. """
        if enabled:
            self._widget.alignmentLine.show()
        else:
            self._widget.alignmentLine.hide()


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
