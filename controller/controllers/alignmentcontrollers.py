# -*- coding: utf-8 -*-
"""
Created on Sun Mar 22 10:40:53 2020

@author: _Xavi
"""
import numpy as np
import pyqtgraph as pg
from pyqtgraph.Qt import QtCore

import view.guitools as guitools
from .basecontrollers import WidgetController, LiveUpdatedController


class ULensesController(WidgetController):
    """ Linked to ULensesWidget. """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.addPlot()

        # Connect ULensesWidget signals
        self._widget.ulensesButton.clicked.connect(self.updateGrid)
        self._widget.ulensesCheck.stateChanged.connect(self.show)

    def addPlot(self):
        """ Adds ulensesPlot to ImageWidget viewbox through the CommunicationChannel. """
        self._comm_channel.addItemTovb.emit(self._widget.ulensesPlot)

    def updateGrid(self):
        """ Updates plot with new parameters. """
        self.getParameters()
        size_x, size_y = self._master.cameraHelper.shapes
        pattern_x = np.arange(self.x, size_x, self.up / self.px)
        pattern_y = np.arange(self.y, size_y, self.up / self.px)
        grid = np.array(np.meshgrid(pattern_x, pattern_y)).T.reshape(-1, 2)
        self._widget.ulensesPlot.setData(x=grid[:, 0], y=grid[:, 1],
                                         pen=pg.mkPen(None), brush='r', symbol='x')
        if self._widget.ulensesCheck.isChecked(): self._widget.show()

    def show(self):
        """ Shows or hides grid. """
        if self._widget.ulensesCheck.isChecked():
            self._widget.ulensesPlot.show()
        else:
            self._widget.ulensesPlot.hide()

    def getParameters(self):
        """ Update new parameters from graphical elements in the widget."""
        self.x = np.float(self._widget.xEdit.text())
        self.y = np.float(self._widget.yEdit.text())
        self.px = np.float(self._widget.pxEdit.text())
        self.up = np.float(self._widget.upEdit.text())


class AlignXYController(LiveUpdatedController):
    """ Linked to AlignWidgetXY. """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.axis = 0
        self.addROI()

        # Connect CommunicationChannel signals
        self._comm_channel.updateImage.connect(self.update)

        # Connect AlignWidgetXY signals
        self._widget.roiButton.clicked.connect(self.toggleROI)
        self._widget.XButton.clicked.connect(lambda: self.setAxis(0))
        self._widget.YButton.clicked.connect(lambda: self.setAxis(1))

    def update(self, im, init):
        """ Update with new camera frame. """
        if self.active:
            value = np.mean(
                self._comm_channel.getROIdata(im, self._widget.ROI),
                self.axis
            )
            self._widget.graph.updateGraph(value)

    def addROI(self):
        """ Adds the ROI to ImageWidget viewbox through the CommunicationChannel. """
        self._comm_channel.addItemTovb.emit(self._widget.ROI)

    def toggleROI(self):
        """ Show or hide ROI."""
        if self._widget.roiButton.isChecked() is False:
            self._widget.ROI.hide()
            self.active = False
            self._widget.roiButton.setText('Show ROI')
        else:
            ROIsize = (64, 64)
            ROIcenter = self._comm_channel.getCenterROI()

            ROIpos = (ROIcenter[0] - 0.5 * ROIsize[0],
                      ROIcenter[1] - 0.5 * ROIsize[1])

            self._widget.ROI.setPos(ROIpos)
            self._widget.ROI.setSize(ROIsize)
            self._widget.ROI.show()
            self.active = True
            self._widget.roiButton.setText('Hide ROI')

    def setAxis(self, axis):
        """ Setter for the axis (X or Y). """
        self.axis = axis


class AlignAverageController(LiveUpdatedController):
    """ Linked to AlignWidgetAverage."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.addROI()

        # Connect CommunicationChannel signals
        self._comm_channel.updateImage.connect(self.update)

        # Connect AlignWidgetAverage signals
        self._widget.roiButton.clicked.connect(self.toggleROI)

    def update(self, im, init):
        """ Update with new camera frame. """
        if self.active:
            value = np.mean(
                self._comm_channel.getROIdata(im, self._widget.ROI)
            )
            self._widget.graph.updateGraph(value)

    def addROI(self):
        """ Adds the ROI to ImageWidget viewbox through the CommunicationChannel. """
        self._comm_channel.addItemTovb.emit(self._widget.ROI)

    def toggleROI(self):
        """ Show or hide ROI."""
        if self._widget.roiButton.isChecked() is False:
            self._widget.ROI.hide()
            self.active = False
            self._widget.roiButton.setText('Show ROI')
        else:
            ROIsize = (64, 64)
            ROIcenter = self._comm_channel.getCenterROI()

            ROIpos = (ROIcenter[0] - 0.5 * ROIsize[0],
                      ROIcenter[1] - 0.5 * ROIsize[1])

            self._widget.ROI.setPos(ROIpos)
            self._widget.ROI.setSize(ROIsize)
            self._widget.ROI.show()
            self._widget.ROI.show()
            self.active = True
            self._widget.roiButton.setText('Hide ROI')


class AlignmentLineController(WidgetController):
    """ Linked to AlignmentLineWidget."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.addLine()

        # Connect AlignmentLineWidget signals
        self._widget.alignmentLineMakerButton.clicked.connect(self.updateLine)
        self._widget.alignmentCheck.stateChanged.connect(self.show)

    def addLine(self):
        """ Adds alignmentLine to ImageWidget viewbox through the CommunicationChannel. """
        self._comm_channel.addItemTovb.emit(self._widget.alignmentLine)

    def updateLine(self):
        """ Updates line with new parameters. """
        self._widget.angle = np.float(self._widget.angleEdit.text())
        self._widget.alignmentLine.setAngle(self._widget.angle)
        self.show()

    def show(self):
        """ Shows or hides line. """
        if self._widget.alignmentCheck.isChecked():
            self._widget.alignmentLine.show()
        else:
            self._widget.alignmentLine.hide()


class FFTController(LiveUpdatedController):
    """ Linked to FFTWidget."""

    imageReceived = QtCore.pyqtSignal(np.ndarray)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.updateRate = 10
        self.it = 0
        self.init = False
        self.show = False

        # Prepare image computation worker
        self.imageComputationWorker = self.FFTImageComputationWorker()
        self.imageComputationWorker.fftImageComputed.connect(self.displayImage)
        self.imageComputationThread = QtCore.QThread()
        self.imageComputationWorker.moveToThread(self.imageComputationThread)
        self.imageReceived.connect(self.imageComputationWorker.computeFFTImage)

        # Connect CommunicationChannel signals
        self._comm_channel.updateImage.connect(self.update)

        # Connect FFTWidget signals
        self._widget.showCheck.stateChanged.connect(self.showFFT)
        self._widget.changePosButton.clicked.connect(self.changePos)
        self._widget.linePos.textChanged.connect(self.changePos)
        self._widget.lineRate.textChanged.connect(self.changeRate)

        self.changeRate()
        self.showFFT()

    def showFFT(self):
        """ Show or hide FFT. """
        self.active = self._widget.showCheck.isChecked()
        self.init = False
        if self.active:
            self._widget.img.setOnlyRenderVisible(True, render=False)
            self.imageComputationThread.start()
        else:
            self.imageComputationThread.quit()
            self.imageComputationThread.wait()
            self._widget.img.setOnlyRenderVisible(False, render=True)

    def update(self, im, init):
        """ Update with new camera frame. """
        if self.active and (self.it == self.updateRate):
            self.it = 0
            self.imageComputationWorker.prepareForNewImage()
            self.imageReceived.emit(im)
        elif self.active and (not (self.it == self.updateRate)):
            self.it += 1

    def displayImage(self, im):
        """ Displays the image in the view. """
        self._widget.img.setImage(im, autoLevels=False)
        if not self.init:
            self._widget.vb.setAspectLocked()
            self._widget.vb.setLimits(xMin=-0.5, xMax=self._widget.img.width(), minXRange=4,
                                      yMin=-0.5, yMax=self._widget.img.height(), minYRange=4)
            self._widget.hist.setLevels(*guitools.bestLimits(im))
            self._widget.hist.vb.autoRange()
            self.init = True

    def changeRate(self):
        """ Change update rate. """
        self.updateRate = float(self._widget.lineRate.text())
        self.it = 0

    def changePos(self):
        """ Change positions of lines.  """
        pos = float(self._widget.linePos.text())
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
            self._widget.vb.setAspectLocked()
            self._widget.vb.setLimits(xMin=-0.5, xMax=imgWidth, minXRange=4,
                                      yMin=-0.5, yMax=imgHeight, minYRange=4)
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

    class FFTImageComputationWorker(QtCore.QObject):
        fftImageComputed = QtCore.pyqtSignal(np.ndarray)

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self._numQueuedImages = 0
            self._numQueuedImagesMutex = QtCore.QMutex()

        def computeFFTImage(self, image):
            """ Compute FFT of an image. """
            try:
                if self._numQueuedImages > 1:
                    return  # Skip this frame in order to catch up

                fftImage = np.fft.fftshift(np.log10(abs(np.fft.fft2(image))))
                self.fftImageComputed.emit(fftImage)
            finally:
                self._numQueuedImagesMutex.lock()
                self._numQueuedImages -= 1
                self._numQueuedImagesMutex.unlock()

        def prepareForNewImage(self):
            """ Must always be called before the worker receives a new image. """
            self._numQueuedImagesMutex.lock()
            self._numQueuedImages += 1
            self._numQueuedImagesMutex.unlock()
