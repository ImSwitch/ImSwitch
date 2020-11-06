# -*- coding: utf-8 -*-
"""
Created on Sun Mar 22 10:40:53 2020

@author: _Xavi
"""
import os
import subprocess
import sys
import time

import numpy as np
from pyqtgraph.Qt import QtCore

import view.guitools as guitools
from controller.enums import RecMode
from .basecontrollers import WidgetController, LiveUpdatedController


class SettingsController(WidgetController):
    """ Linked to SettingsWidget."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.addROI()
        self.getParameters()
        self.setExposure()
        self.adjustFrame()

        # Connect SettingsWidget signals
        self._widget.ROI.sigRegionChangeFinished.connect(self.ROIchanged)

    def addROI(self):
        """ Adds the ROI to ImageWidget viewbox through the CommunicationChannel. """
        self._comm_channel.addItemTovb.emit(self._widget.ROI)

    def toggleROI(self, b):
        """ Show or hide ROI. """
        if b:
            self._widget.ROI.show()
        else:
            self._widget.ROI.hide()

    def getParameters(self):
        """ Take parameters from the camera Tree map. """
        self.model = self._master.cameraHelper.model
        self._widget.tree.p.param('Model').setValue(self.model)
        self.umxpx = self._widget.tree.p.param('Pixel size')
        framePar = self._widget.tree.p.param('Image frame')
        self.binPar = framePar.param('Binning')
        self.frameMode = framePar.param('Mode')
        self.x0par = framePar.param('X0')
        self.y0par = framePar.param('Y0')
        self.widthPar = framePar.param('Width')
        self.heightPar = framePar.param('Height')
        self.applyParam = framePar.param('Apply')
        self.newROIParam = framePar.param('New ROI')
        self.abortROIParam = framePar.param('Abort ROI')

        timingsPar = self._widget.tree.p.param('Timings')
        self.effFRPar = timingsPar.param('Internal frame rate')
        self.expPar = timingsPar.param('Set exposure time')
        self.readoutPar = timingsPar.param('Readout time')
        self.realExpPar = timingsPar.param('Real exposure time')
        self.frameInt = timingsPar.param('Internal frame interval')
        self.realExpPar.setOpts(decimals=5)

        acquisParam = self._widget.tree.p.param('Acquisition mode')
        self.trigsourceparam = acquisParam.param('Trigger source')

        self.applyParam.sigStateChanged.connect(self.adjustFrame)
        self.newROIParam.sigStateChanged.connect(self.updateFrame)
        self.abortROIParam.sigStateChanged.connect(self.abortROI)
        self.trigsourceparam.sigValueChanged.connect(self.changeTriggerSource)
        self.expPar.sigValueChanged.connect(self.setExposure)
        self.binPar.sigValueChanged.connect(self.setBinning)
        self.frameMode.sigValueChanged.connect(self.updateFrame)
        self.expPar.sigValueChanged.connect(self.setExposure)

    def adjustFrame(self):
        """ Crop camera and adjust frame. """
        binning = self.binPar.value()
        width = self.widthPar.value()
        height = self.heightPar.value()
        X0par = self.x0par.value()
        Y0par = self.y0par.value()

        # Round to closest "divisable by 4" value.
        hpos = binning * X0par
        vpos = binning * Y0par
        hsize = binning * width
        vsize = height

        hmodulus = 4
        vmodulus = 4
        vpos = int(vmodulus * np.ceil(vpos / vmodulus))
        hpos = int(hmodulus * np.ceil(hpos / hmodulus))
        vsize = int(vmodulus * np.ceil(vsize / vmodulus))
        hsize = int(hmodulus * np.ceil(hsize / hmodulus))

        self._master.cameraHelper.changeParameter(
            lambda: self._master.cameraHelper.cropOrca(vpos, hpos, hsize, hsize)
        )

        # Final shape values might differ from the user-specified one because of camera limitation x128
        width, height = self._master.cameraHelper.shapes
        self._comm_channel.adjustFrame.emit(width, height)
        self._widget.ROI.hide()
        frameStart = self._master.cameraHelper.frameStart
        self.x0par.setValue(frameStart[0])
        self.y0par.setValue(frameStart[1])
        self.widthPar.setValue(width)
        self.heightPar.setValue(height)
        self.updateTimings(*self._master.cameraHelper.getTimings())

    def ROIchanged(self):
        """ Update parameters according to ROI. """
        frameStart = self._master.cameraHelper.frameStart
        pos = self._widget.ROI.pos()
        size = self._widget.ROI.size()
        self.x0par.setValue(frameStart[0] + int(pos[0]))
        self.y0par.setValue(frameStart[1] + int(pos[1]))

        self.widthPar.setValue(size[0])  # [0] is Width
        self.heightPar.setValue(size[1])  # [1] is Height

    def abortROI(self):
        """ Cancel and reset parameters of the ROI. """
        self._widget.toggleROI(False)
        frameStart = self._master.cameraHelper.frameStart
        shapes = self._master.cameraHelper.shapes
        self.x0par.setValue(frameStart[0])
        self.y0par.setValue(frameStart[1])
        self.widthPar.setValue(shapes[0])
        self.heightPar.setValue(shapes[1])

    def changeTriggerSource(self):
        """ Change trigger (Internal or External). """
        self._master.cameraHelper.changeTriggerSource(self.trigsourceparam.value())

    def setTriggerParam(self, source):
        self.trigsourceparam.setValue(source)

    def updateTimings(self, realExpParValue, frameIntValue, readoutParValue, effFRParValue):
        """ Update the real exposure times from the camera. """
        self.realExpPar.setValue(realExpParValue)
        self.frameInt.setValue(frameIntValue)
        self.readoutPar.setValue(readoutParValue)
        self.effFRPar.setValue(effFRParValue)

    def setExposure(self):
        """ Update a new exposure time to the camera. """
        params = self._master.cameraHelper.setExposure(self.expPar.value())
        self.updateTimings(*params)

    def setBinning(self):
        """ Update a new binning to the camera. """
        self._master.cameraHelper.setBinning(self.binPar.value())

    def updateFrame(self, controller):
        """ Change the image frame size and position in the sensor. """
        if self.frameMode.value() == 'Custom':
            self.x0par.setWritable(True)
            self.y0par.setWritable(True)
            self.widthPar.setWritable(True)
            self.heightPar.setWritable(True)

            ROIsize = (64, 64)
            ROIcenter = self._comm_channel.getCenterROI()

            ROIpos = (ROIcenter[0] - 0.5 * ROIsize[0],
                      ROIcenter[1] - 0.5 * ROIsize[1])

            self._widget.ROI.setPos(ROIpos)
            self._widget.ROI.setSize(ROIsize)
            self._widget.ROI.show()
            self.ROIchanged()

        else:
            self.x0par.setWritable(False)
            self.y0par.setWritable(False)
            self.widthPar.setWritable(False)
            self.heightPar.setWritable(False)

            # Change this to config File.
            if self.frameMode.value() == 'Full chip':
                self.x0par.setValue(0)
                self.y0par.setValue(0)
                self.widthPar.setValue(2048)
                self.heightPar.setValue(2048)

                self.adjustFrame()

    def getCamAttrs(self):
        return {
            'Camera_pixel_size': self.umxpx.value(),
            'Camera_model': self.model,
            'Camera_binning': self.binPar.value(),
            'FOV_mode': self.frameMode.value(),
            'Camera_exposure_time': self.realExpPar.value(),
            'Camera_ROI': [self.x0par.value(), self.y0par.value(),
                           self.widthPar.value(), self.heightPar.value()]
        }


class ViewController(WidgetController):
    """ Linked to ViewWidget."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Connect ViewWidget signals
        self._widget.gridButton.clicked.connect(self.gridToggle)
        self._widget.crosshairButton.pressed.connect(self.crosshairToggle)
        self._widget.liveviewButton.clicked.connect(self.liveview)

    def liveview(self):
        """ Start liveview and activate camera acquisition. """
        self._widget.crosshairButton.setEnabled(True)
        self._widget.gridButton.setEnabled(True)
        if self._widget.liveviewButton.isChecked():
            self._master.cameraHelper.startAcquisition()
            self._master.cameraHelper.updateImageSignal.connect(self._comm_channel.updateImage)
        else:
            self._master.cameraHelper.stopAcquisition()

    def gridToggle(self):
        """ Connect with grid toggle from Image Widget through communication channel. """
        self._comm_channel.gridToggle.emit()

    def crosshairToggle(self):
        """ Connect with crosshair toggle from Image Widget through communication channel. """
        self._comm_channel.crosshairToggle.emit()

    def closeEvent(self):
        self._master.cameraHelper.stopAcquisition()


class ImageController(LiveUpdatedController):
    """ Linked to ImageWidget."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Connect CommunicationChannel signals
        self._comm_channel.updateImage.connect(self.update)
        self._comm_channel.acquisitionStopped.connect(self.acquisitionStopped)
        self._comm_channel.adjustFrame.connect(self.adjustFrame)
        self._comm_channel.gridToggle.connect(self.gridToggle)
        self._comm_channel.crosshairToggle.connect(self.crosshairToggle)
        self._comm_channel.addItemTovb.connect(self.addItemTovb)
        self._comm_channel.removeItemFromvb.connect(self.removeItemFromvb)

        # Connect ImageWidget signals
        self._widget.levelsButton.pressed.connect(self.autoLevels)

    def autoLevels(self, im=None):
        """ Set histogram levels automatically with current camera image."""
        if im is None:
            im = self._widget.img.image

        self._widget.hist.setLevels(*guitools.bestLimits(im))
        self._widget.hist.vb.setYRange(im.min(), im.max())

    def addItemTovb(self, item):
        """ Add item from communication channel to viewbox."""
        self._widget.vb.addItem(item)
        item.hide()

    def removeItemFromvb(self, item):
        """ Remove item from communication channel to viewbox."""
        self._widget.vb.removeItem(item)

    def update(self, im, init):
        """ Update new image in the viewbox. """
        if not init:
            self._widget.img.setOnlyRenderVisible(True, render=False)
            self._widget.levelsButton.setEnabled(True)
            self.autoLevels(im)

        self._widget.img.setImage(im, autoLevels=False, autoDownsample=False)

    def acquisitionStopped(self):
        """ Disable the onlyRenderVisible optimization for a smoother experience. """
        self._widget.img.setOnlyRenderVisible(False, render=True)

    def adjustFrame(self, width, height):
        """ Adjusts the viewbox to a new width and height. """
        self._widget.grid.update([width, height])
        self._widget.vb.setLimits(xMin=-0.5, xMax=width - 0.5, minXRange=4,
                                  yMin=-0.5, yMax=height - 0.5, minYRange=4)
        self._widget.vb.setAspectLocked()

    def getROIdata(self, image, roi):
        """ Returns the cropped image within the ROI. """
        return roi.getArrayRegion(image, self._widget.img)

    def getCenterROI(self):
        """ Returns center of viewbox to center a ROI. """
        return (int(self._widget.vb.viewRect().center().x()),
                int(self._widget.vb.viewRect().center().y()))

    def gridToggle(self):
        """ Shows or hides grid. """
        self._widget.grid.toggle()

    def crosshairToggle(self):
        """ Shows or hides crosshair. """
        self._widget.crosshair.toggle()


class RecorderController(WidgetController):
    """ Linked to RecordingWidget. """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.recMode = RecMode.NotRecording
        self.untilStop()

        # Connect CommunicationChannel signals
        self._comm_channel.endRecording.connect(self.endRecording)
        self._comm_channel.updateRecFrameNumber.connect(self.updateRecFrameNumber)
        self._comm_channel.updateRecTime.connect(self.updateRecTime)
        self._comm_channel.endScan.connect(self.scanDone)

        # Connect RecordingWidget signals
        self._widget.openFolderButton.clicked.connect(self.openFolder)
        self._widget.specifyfile.clicked.connect(self.specFile)
        self._widget.snapTIFFButton.clicked.connect(self.snap)
        self._widget.recButton.toggled.connect(self.toggleREC)
        self._widget.specifyFrames.clicked.connect(self.specFrames)
        self._widget.specifyTime.clicked.connect(self.specTime)
        self._widget.recScanOnceBtn.clicked.connect(self.recScanOnce)
        self._widget.recScanLapseBtn.clicked.connect(self.recScanLapse)
        self._widget.dimLapse.clicked.connect(self.dimLapse)
        self._widget.untilSTOPbtn.clicked.connect(self.untilStop)

    def isRecording(self):
        return self._widget.recButton.isChecked()

    def openFolder(self):
        """ Opens current folder in File Explorer. """
        try:
            if sys.platform == 'darwin':
                subprocess.check_call(['open', self._widget.folderEdit.text()])
            elif sys.platform == 'linux':
                subprocess.check_call(['xdg-open', self._widget.folderEdit.text()])
            elif sys.platform == 'win32':
                os.startfile(self._widget.folderEdit.text())

        except FileNotFoundError or subprocess.CalledProcessError:
            if sys.platform == 'darwin':
                subprocess.check_call(['open', self._widget.dataDir])
            elif sys.platform == 'linux':
                subprocess.check_call(['xdg-open', self._widget.dataDir])
            elif sys.platform == 'win32':
                os.startfile(self._widget.dataDir)

    def specFile(self):
        """ Enables the ability to type a specific filename for the data to . """
        if self._widget.specifyfile.checkState():
            self._widget.filenameEdit.setEnabled(True)
            self._widget.filenameEdit.setText('Filename')
        else:
            self._widget.filenameEdit.setEnabled(False)
            self._widget.filenameEdit.setText('Current time')

    def snap(self):
        """ Take a snap and save it to a .tiff file. """
        folder = self._widget.folderEdit.text()
        if not os.path.exists(folder):
            os.mkdir(folder)
        time.sleep(0.01)
        name = os.path.join(folder, self.getFileName()) + '_snap'
        savename = guitools.getUniqueName(name)
        attrs = self._comm_channel.getCamAttrs()
        self._master.recordingHelper.snap(savename, attrs)

    def toggleREC(self, checked):
        """ Start or end recording. """
        if checked:
            folder = self._widget.folderEdit.text()
            if not os.path.exists(folder):
                os.mkdir(folder)
            time.sleep(0.01)
            name = os.path.join(folder, self.getFileName()) + '_rec'
            self.savename = guitools.getUniqueName(name)
            self.attrs = self._comm_channel.getCamAttrs()
            scan = self._comm_channel.getScanAttrs()
            self.attrs.update(scan)
            if self.recMode == RecMode.SpecFrames:
                self._master.recordingHelper.startRecording(
                    self.recMode, self.savename, self.attrs,
                    frames=int(self._widget.numExpositionsEdit.text())
                )
            elif self.recMode == RecMode.SpecTime:
                self._master.recordingHelper.startRecording(
                    self.recMode, self.savename, self.attrs,
                    time=float(self._widget.timeToRec.text())
                )
            elif self.recMode == RecMode.ScanOnce:
                self._master.recordingHelper.startRecording(self.recMode, self.savename, self.attrs)
                time.sleep(0.1)
                self._comm_channel.prepareScan.emit()
            elif self.recMode == RecMode.ScanLapse:
                self.lapseTotal = int(self._widget.timeLapseEdit.text())
                self.lapseCurrent = 0
                self._master.recordingHelper.startRecording(self.recMode, self.savename, self.attrs)
                time.sleep(0.1)
                self._comm_channel.prepareScan.emit()
            elif self.recMode == RecMode.DimLapse:
                self.lapseTotal = int(self._widget.totalSlices.text())
                self.lapseCurrent = 0
                self._master.recordingHelper.startRecording(self.recMode, self.savename, self.attrs)
                time.sleep(0.3)
                self._comm_channel.prepareScan.emit()
            else:
                self._master.recordingHelper.startRecording(self.recMode, self.savename, self.attrs)
        else:
            self._master.recordingHelper.endRecording()

    def scanDone(self):
        if self._widget.recButton.isChecked():
            if self.recMode == RecMode.ScanOnce:
                self._widget.recButton.setChecked(False)
                self._master.recordingHelper.endRecording()
            elif self.recMode == RecMode.ScanLapse:
                if self.lapseCurrent < self.lapseTotal:
                    self.lapseCurrent += 1
                    self._master.recordingHelper.endRecording()
                    self._widget.currentLapse.setText(str(self.lapseCurrent) + ' / ')
                    self.timer = QtCore.QTimer(singleShot=True)
                    self.timer.timeout.connect(self.nextLapse)
                    self.timer.start(int(float(self._widget.freqEdit.text()) * 1000))
                else:
                    self._widget.recButton.setChecked(False)
                    self.lapseCurrent = 0
                    self._widget.currentLapse.setText(str(self.lapseCurrent) + ' / ')
                    self._master.recordingHelper.endRecording()
            elif self.recMode == RecMode.DimLapse:
                if self.lapseCurrent < self.lapseTotal:
                    self.lapseCurrent += 1
                    self._widget.currentSlice.setText(str(self.lapseCurrent) + ' / ')
                    self._master.recordingHelper.endRecording()
                    time.sleep(0.3)
                    self._comm_channel.moveZstage.emit(float(self._widget.stepSizeEdit.text()))
                    self.timer = QtCore.QTimer(singleShot=True)
                    self.timer.timeout.connect(self.nextLapse)
                    self.timer.start(1000)
                else:
                    self._widget.recButton.setChecked(False)
                    self.lapseCurrent = 0
                    self._comm_channel.moveZstage.emit(
                        -self.lapseTotal * float(self._widget.stepSizeEdit.text())
                    )
                    self._widget.currentSlice.setText(str(self.lapseCurrent) + ' / ')
                    self._master.recordingHelper.endRecording()

    def nextLapse(self):
        self._master.recordingHelper.startRecording(self.recMode,
                                                    self.savename + '_' + str(self.lapseCurrent),
                                                    self.attrs)
        time.sleep(0.3)
        self._comm_channel.prepareScan.emit()

    def endRecording(self):
        self._widget.recButton.setChecked(False)
        self._widget.currentFrame.setText('0 / ')

    def updateRecFrameNumber(self, f):
        self._widget.currentFrame.setText(str(f) + ' /')

    def updateRecTime(self, t):
        self._widget.currentTime.setText(str(t) + ' /')

    def specFrames(self):
        self._widget.numExpositionsEdit.setEnabled(True)
        self._widget.timeToRec.setEnabled(False)
        self._widget.timeLapseEdit.setEnabled(False)
        self._widget.totalSlices.setEnabled(False)
        self._widget.freqEdit.setEnabled(False)
        self._widget.stepSizeEdit.setEnabled(False)
        self.recMode = RecMode.SpecFrames

    def specTime(self):
        self._widget.numExpositionsEdit.setEnabled(False)
        self._widget.timeToRec.setEnabled(True)
        self._widget.timeLapseEdit.setEnabled(False)
        self._widget.totalSlices.setEnabled(False)
        self._widget.freqEdit.setEnabled(False)
        self._widget.stepSizeEdit.setEnabled(False)
        self.recMode = RecMode.SpecTime

    def recScanOnce(self):
        self._widget.numExpositionsEdit.setEnabled(False)
        self._widget.timeToRec.setEnabled(False)
        self._widget.timeLapseEdit.setEnabled(False)
        self._widget.totalSlices.setEnabled(False)
        self._widget.freqEdit.setEnabled(False)
        self._widget.stepSizeEdit.setEnabled(False)
        self.recMode = RecMode.ScanOnce

    def recScanLapse(self):
        self._widget.numExpositionsEdit.setEnabled(False)
        self._widget.timeToRec.setEnabled(False)
        self._widget.timeLapseEdit.setEnabled(True)
        self._widget.totalSlices.setEnabled(False)
        self._widget.freqEdit.setEnabled(True)
        self._widget.stepSizeEdit.setEnabled(False)
        self.recMode = RecMode.ScanLapse

    def dimLapse(self):
        self._widget.totalSlices.setEnabled(True)
        self._widget.numExpositionsEdit.setEnabled(False)
        self._widget.timeToRec.setEnabled(False)
        self._widget.timeLapseEdit.setEnabled(False)
        self._widget.freqEdit.setEnabled(False)
        self._widget.stepSizeEdit.setEnabled(True)
        self.recMode = RecMode.DimLapse

    def untilStop(self):
        self._widget.numExpositionsEdit.setEnabled(False)
        self._widget.timeToRec.setEnabled(False)
        self._widget.timeLapseEdit.setEnabled(False)
        self._widget.totalSlices.setEnabled(False)
        self._widget.freqEdit.setEnabled(False)
        self._widget.stepSizeEdit.setEnabled(False)
        self.recMode = RecMode.UntilStop

    def getFileName(self):
        """ Gets the filename of the data to save. """
        if self._widget.specifyfile.checkState():
            filename = self._widget.filenameEdit.text()

        else:
            filename = time.strftime('%Hh%Mm%Ss')

        return filename
