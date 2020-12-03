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

import configfileutils
import view.guitools as guitools
from controller.helpers.RecordingHelper import RecMode
from .basecontrollers import WidgetController, LiveUpdatedController


class SettingsController(WidgetController):
    """ Linked to SettingsWidget."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._widget.initControls(self._setupInfo.rois)

        self.nonCameraHelpersParamValues = {
            camera: {
                'Camera_pixel_size': 0.1
            } for camera in self._setupInfo.cameras
        }

        self.addROI()
        self.initParameters()
        self.updateParamsFromCamera()
        self.setBinning()
        self.setExposure()
        self.changeTriggerSource()
        self.adjustFrame()
        self.updateFrame()
        self.updateFrameActionButtons()

        # Connect CommunicationChannel signals
        self._commChannel.cameraSwitched.connect(self.cameraSwitched)

        # Connect SettingsWidget signals
        self._widget.ROI.sigRegionChangeFinished.connect(self.ROIchanged)

    def addROI(self):
        """ Adds the ROI to ImageWidget viewbox through the CommunicationChannel. """
        self._commChannel.addItemTovb.emit(self._widget.ROI)

    def toggleROI(self, b):
        """ Show or hide ROI. """
        if b:
            self._widget.ROI.show()
        else:
            self._widget.ROI.hide()

    def initParameters(self):
        """ Take parameters from the camera Tree map. """
        self.modelPar = self._widget.tree.p.param('Model')
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
        self.saveModeParam = framePar.param('Save mode')
        self.deleteModeParam = framePar.param('Delete mode')
        self.allCamerasFrameParam = framePar.param('Update all cameras')

        timingsPar = self._widget.tree.p.param('Timings')
        self.effFRPar = timingsPar.param('Internal frame rate')
        self.expPar = timingsPar.param('Set exposure time')
        self.readoutPar = timingsPar.param('Readout time')
        self.realExpPar = timingsPar.param('Real exposure time')
        self.frameInt = timingsPar.param('Internal frame interval')
        self.realExpPar.setOpts(decimals=5)

        acquisParam = self._widget.tree.p.param('Acquisition mode')
        self.trigsourceparam = acquisParam.param('Trigger source')

        self.applyParam.sigActivated.connect(self.adjustFrame)
        self.newROIParam.sigActivated.connect(self.updateFrame)
        self.abortROIParam.sigActivated.connect(self.abortROI)
        self.saveModeParam.sigActivated.connect(self.saveMode)
        self.deleteModeParam.sigActivated.connect(self.deleteMode)
        self.allCamerasFrameParam.sigValueChanged.connect(self.adjustFrame)
        self.trigsourceparam.sigValueChanged.connect(self.changeTriggerSource)
        self.expPar.sigValueChanged.connect(self.setExposure)
        self.binPar.sigValueChanged.connect(self.setBinning)
        self.frameMode.sigValueChanged.connect(self.updateFrame)
        self.expPar.sigValueChanged.connect(self.setExposure)

    def adjustFrame(self, *, camera=None):
        """ Crop camera and adjust frame. """

        if camera is None:
            self.getCameraHelperFrameExecFunc()(lambda c: self.adjustFrame(camera=c))
            return

        binning = self.binPar.value()
        width = self.widthPar.value()
        height = self.heightPar.value()
        X0par = self.x0par.value()
        Y0par = self.y0par.value()

        # Round to closest "divisable by 4" value.
        hpos = binning * Y0par
        vpos = binning * X0par
        hsize = binning * height
        vsize = binning * width

        hmodulus = 4
        vmodulus = 4
        vpos = int(vmodulus * np.ceil(vpos / vmodulus))
        hpos = int(hmodulus * np.ceil(hpos / hmodulus))
        vsize = int(vmodulus * np.ceil(vsize / vmodulus))
        hsize = int(hmodulus * np.ceil(hsize / hmodulus))

        camera.crop(hpos, vpos, hsize, vsize)

        # Final shape values might differ from the user-specified one because of camera limitation x128
        width, height = camera.shape
        self._commChannel.adjustFrame.emit(width, height)
        self._widget.ROI.hide()

        if camera == self._master.cameraHelper.getCurrentCameraName():
            self.updateParamsFromCamera()

    def ROIchanged(self):
        """ Update parameters according to ROI. """
        frameStart = self._master.cameraHelper.execOnCurrent(lambda c: c.frameStart)
        pos = self._widget.ROI.pos()
        size = self._widget.ROI.size()

        self.x0par.setValue(frameStart[0] + int(pos[0]))
        self.y0par.setValue(frameStart[1] + int(pos[1]))
        self.widthPar.setValue(size[0])  # [0] is Width
        self.heightPar.setValue(size[1])  # [1] is Height

    def updateFrameActionButtons(self):
        """ Shows the frame-related buttons appropriate for the current frame
        mode, and hides the others. """

        self.applyParam.hide()
        self.newROIParam.hide()
        self.abortROIParam.hide()
        self.saveModeParam.hide()
        self.deleteModeParam.hide()

        if self.frameMode.value() == 'Custom':
            self.applyParam.show()
            self.newROIParam.show()
            self.abortROIParam.show()
            self.saveModeParam.show()
        elif self.frameMode.value() != 'Full chip':
            self.deleteModeParam.show()

    def abortROI(self):
        """ Cancel and reset parameters of the ROI. """
        self.toggleROI(False)
        frameStart = self._master.cameraHelper.execOnCurrent(lambda c: c.frameStart)
        shapes = self._master.cameraHelper.execOnCurrent(lambda c: c.shape)
        self.x0par.setValue(frameStart[0])
        self.y0par.setValue(frameStart[1])
        self.widthPar.setValue(shapes[0])
        self.heightPar.setValue(shapes[1])

    def saveMode(self):
        """ Save the current frame mode parameters to the mode list. """

        x0, y0, width, height = (self.x0par.value(), self.y0par.value(),
                                 self.widthPar.value(), self.heightPar.value())

        name = guitools.askForTextInput(
            self._widget,
            'Add frame mode',
            f'Enter a name for this mode:\n(X0: {x0}; Y0: {y0}; Width: {width}; Height: {height})')

        if not name:  # No name provided
            return

        add = True
        alreadyExists = False
        if name in self._setupInfo.rois:
            alreadyExists = True
            add = guitools.askYesNoQuestion(
                self._widget,
                'Frame mode already exists',
                f'A frame mode with the name "{name}" already exists. Do you want to overwrite it"?'
            )

        if add:
            if not alreadyExists:
                # Add in GUI
                newModeItems = self.frameMode.opts['limits'].copy()
                newModeItems.insert(len(newModeItems) - 1, name)
                self.frameMode.setLimits(newModeItems)

            # Add to setup info
            self._setupInfo.setROI(name, x0, y0, width, height)
            configfileutils.saveSetupInfo(self._setupInfo)

    def deleteMode(self):
        """ Delete the current frame mode from the mode list (if it's a saved
        custom ROI). """

        modeToDelete = self.frameMode.value()

        confirmationResult = guitools.askYesNoQuestion(
            self._widget,
            'Delete frame mode?',
            f'Are you sure you want to delete the mode "{modeToDelete}"?'
        )

        if confirmationResult:
            # Remove in GUI
            newModeItems = self.frameMode.opts['limits'].copy()
            newModeItems = [value for value in newModeItems if value != modeToDelete]
            self.frameMode.setLimits(newModeItems)

            # Remove from setup info
            self._setupInfo.removeROI(modeToDelete)
            configfileutils.saveSetupInfo(self._setupInfo)

    def setBinning(self):
        """ Update a new binning to the camera. """
        self.getCameraHelperFrameExecFunc()(
            lambda c: c.setBinning(self.binPar.value())
        )

    def changeTriggerSource(self):
        """ Change trigger (Internal or External). """
        # TODO: Figure out if it should be changed which cameras this executes on,
        #       or if the param perhaps should be moved somewhere else in the UI
        self._master.cameraHelper.execOnAll(
            lambda c: c.changeTriggerSource(self.trigsourceparam.value())
        )

    def setExposure(self):
        """ Update a new exposure time to the camera. """
        self._master.cameraHelper.execOnCurrent(
            lambda c: c.setExposure(self.expPar.value())
        )
        self.updateParamsFromCamera()

    def updateParamsFromCamera(self):
        """ Update the real exposure times from the camera. """

        currentCamera = self._master.cameraHelper.getCurrentCamera()
        currentNonCameraHelperParamValues = self.nonCameraHelpersParamValues[currentCamera.name]

        # Timings
        realExpParValue, frameIntValue, readoutParValue, effFRParValue = currentCamera.getTimings()
        self.expPar.setValue(realExpParValue)
        self.realExpPar.setValue(realExpParValue)
        self.frameInt.setValue(frameIntValue)
        self.readoutPar.setValue(readoutParValue)
        self.effFRPar.setValue(effFRParValue)

        # Frame
        self.binPar.setValue(currentCamera.binning)
        frameStart = currentCamera.frameStart
        shape = currentCamera.shape
        fullShape = currentCamera.fullShape
        self.x0par.setValue(frameStart[0])
        self.y0par.setValue(frameStart[1])
        self.widthPar.setValue(shape[0])
        self.widthPar.setLimits((1, fullShape[0]))
        self.heightPar.setValue(shape[1])
        self.heightPar.setLimits((1, fullShape[1]))

        # Model
        self.modelPar.setValue(currentCamera.model)

        # Pixel size
        self.umxpx.setValue(currentNonCameraHelperParamValues['Camera_pixel_size'])

    def updateFrame(self, _=None):
        """ Change the image frame size and position in the sensor. """

        customFrame = self.frameMode.value() == 'Custom'
        
        self.x0par.setWritable(customFrame)
        self.y0par.setWritable(customFrame)
        self.widthPar.setWritable(customFrame)
        self.heightPar.setWritable(customFrame)
        # Call .show() to prevent alignment issues
        self.x0par.show()
        self.y0par.show()
        self.widthPar.show()
        self.heightPar.show()

        if customFrame:
            ROIsize = (64, 64)
            ROIcenter = self._commChannel.getCenterROI()

            ROIpos = (ROIcenter[0] - 0.5 * ROIsize[0],
                      ROIcenter[1] - 0.5 * ROIsize[1])

            self._widget.ROI.setPos(ROIpos)
            self._widget.ROI.setSize(ROIsize)
            self._widget.ROI.show()
            self.ROIchanged()

        else:
            if self.frameMode.value() == 'Full chip':
                fullChipShape = self._master.cameraHelper.execOnCurrent(lambda c: c.fullShape)
                self.x0par.setValue(0)
                self.y0par.setValue(0)
                self.widthPar.setValue(fullChipShape[0])
                self.heightPar.setValue(fullChipShape[1])
            else:
                roiInfo = self._setupInfo.rois[self.frameMode.value()]
                self.x0par.setValue(roiInfo.x)
                self.y0par.setValue(roiInfo.y)
                self.widthPar.setValue(roiInfo.w)
                self.heightPar.setValue(roiInfo.h)

            self.adjustFrame()

        self.updateFrameActionButtons()

    def cameraSwitched(self, _, oldCameraName):
        """ Called when the user switches to another camera. """
        self.saveNonCameraHelperParamValues(oldCameraName)
        self.updateParamsFromCamera()
        self._master.cameraHelper.execOnCurrent(
            lambda c: self.adjustFrame(camera=c)
        )

    def saveNonCameraHelperParamValues(self, cameraName):
        """ Saves current param values that are not linked to CameraHelper. """
        self.nonCameraHelpersParamValues[cameraName]['Camera_pixel_size'] = self.umxpx.value()

    def getCamAttrs(self):
        self.saveNonCameraHelperParamValues(self._master.cameraHelper.getCurrentCameraName())

        return self._master.cameraHelper.execOnAll(
            lambda c: {
                **{
                    'Camera_model': c.model,
                    'Camera_binning': c.binning,
                    'Camera_exposure_time': c.getTimings()[0],
                    'Camera_ROI': [*c.frameStart, *c.shape]
                },
                **self.nonCameraHelpersParamValues[c.name]}
        )

    def getCameraHelperFrameExecFunc(self):
        """ Returns the camera helper exec function that should be used for
        frame-related changes. """
        cameraHelper = self._master.cameraHelper
        return (cameraHelper.execOnAll if self.allCamerasFrameParam.value()
                else cameraHelper.execOnCurrent)


class ViewController(WidgetController):
    """ Linked to ViewWidget."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._widget.initControls(self._master.cameraHelper.execOnAll(lambda c: c.model))

        # Connect ViewWidget signals
        self._widget.gridButton.clicked.connect(self.gridToggle)
        self._widget.crosshairButton.clicked.connect(self.crosshairToggle)
        self._widget.liveviewButton.clicked.connect(self.liveview)
        self._widget.cameraList.currentIndexChanged.connect(self.cameraSwitch)
        self._widget.nextCameraButton.clicked.connect(self.cameraNext)

    def liveview(self):
        """ Start liveview and activate camera acquisition. """
        self._widget.crosshairButton.setEnabled(True)
        self._widget.gridButton.setEnabled(True)
        if self._widget.liveviewButton.isChecked():
            self._master.cameraHelper.startAcquisition()
            self._master.cameraHelper.updateImageSignal.connect(self._commChannel.updateImage)
        else:
            self._master.cameraHelper.stopAcquisition()

    def gridToggle(self):
        """ Connect with grid toggle from Image Widget through communication channel. """
        self._commChannel.gridToggle.emit()

    def crosshairToggle(self):
        """ Connect with crosshair toggle from Image Widget through communication channel. """
        self._commChannel.crosshairToggle.emit()

    def cameraSwitch(self, listIndex):
        """ Changes the current camera to the selected camera. """
        cameraName = self._widget.cameraList.itemData(listIndex)
        self._master.cameraHelper.setCurrentCamera(cameraName)

    def cameraNext(self):
        """ Changes the current camera to the next camera. """
        self._widget.cameraList.setCurrentIndex(
            (self._widget.cameraList.currentIndex() + 1) % self._widget.cameraList.count()
        )

    def closeEvent(self):
        self._master.cameraHelper.stopAcquisition()


class ImageController(LiveUpdatedController):
    """ Linked to ImageWidget."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._lastWidth, self._lastHeight = self._master.cameraHelper.execOnCurrent(
            lambda c: c.shape
        )
        self._savedLevels = {}

        # Connect CommunicationChannel signals
        self._commChannel.updateImage.connect(self.update)
        self._commChannel.acquisitionStopped.connect(self.acquisitionStopped)
        self._commChannel.adjustFrame.connect(self.adjustFrame)
        self._commChannel.gridToggle.connect(self.gridToggle)
        self._commChannel.crosshairToggle.connect(self.crosshairToggle)
        self._commChannel.addItemTovb.connect(self.addItemTovb)
        self._commChannel.removeItemFromvb.connect(self.removeItemFromvb)
        self._commChannel.cameraSwitched.connect(self.restoreSavedLevels)

        # Connect ImageWidget signals
        self._widget.levelsButton.pressed.connect(self.autoLevels)
        self._widget.vb.sigResized.connect(lambda: self.adjustFrame(self._lastWidth, self._lastHeight))
        self._widget.hist.sigLevelsChanged.connect(self.updateSavedLevels)

    def autoLevels(self, im=None):
        """ Set histogram levels automatically with current camera image."""
        if im is None:
            im = self._widget.img.image

        self._widget.hist.setLevels(*guitools.bestLevels(im))
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

        if not init:
            self.adjustFrame(self._lastWidth, self._lastHeight)

    def acquisitionStopped(self):
        """ Disable the onlyRenderVisible optimization for a smoother experience. """
        self._widget.img.setOnlyRenderVisible(False, render=True)

    def adjustFrame(self, width, height):
        """ Adjusts the viewbox to a new width and height. """
        self._widget.grid.update([width, height])
        guitools.setBestImageLimits(self._widget.vb, width, height)
        self._widget.img.render()

        self._lastWidth = width
        self._lastHeight = height

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

    def updateSavedLevels(self):
        cameraName = self._master.cameraHelper.getCurrentCameraName()
        self._savedLevels[cameraName] = self._widget.hist.getLevels()

    def restoreSavedLevels(self, newCameraName):
        """ Updates image levels from saved levels for camera that is switched to. """
        if newCameraName in self._savedLevels:
            self._widget.hist.setLevels(*self._savedLevels[newCameraName])


class RecorderController(WidgetController):
    """ Linked to RecordingWidget. """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._widget.initControls(self._master.cameraHelper.execOnAll(lambda c: c.model))

        self.lapseCurrent = 0
        self.lapseTotal = 0
        self.untilStop()

        # Connect CommunicationChannel signals
        self._commChannel.endRecording.connect(self.endRecording)
        self._commChannel.updateRecFrameNumber.connect(self.updateRecFrameNumber)
        self._commChannel.updateRecTime.connect(self.updateRecTime)
        self._commChannel.endScan.connect(self.scanDone)

        # Connect RecordingWidget signals
        self._widget.cameraList.currentIndexChanged.connect(self.setCamerasToCapture)
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
        cameraNames = self.getCamerasToCapture()
        folder = self._widget.folderEdit.text()
        if not os.path.exists(folder):
            os.mkdir(folder)
        time.sleep(0.01)
        name = os.path.join(folder, self.getFileName()) + '_snap'
        savename = guitools.getUniqueName(name)
        attrs = self._commChannel.getCamAttrs()
        self._master.recordingHelper.snap(cameraNames, savename, attrs)

    def toggleREC(self, checked):
        """ Start or end recording. """
        if checked:
            # self._widget.cameraList.setEnabled(False)

            folder = self._widget.folderEdit.text()
            if not os.path.exists(folder):
                os.mkdir(folder)
            time.sleep(0.01)
            name = os.path.join(folder, self.getFileName()) + '_rec'
            self.savename = guitools.getUniqueName(name)

            self.camerasBeingCaptured = self.getCamerasToCapture()
            self.attrs = self._commChannel.getCamAttrs()
            scan = self._commChannel.getScanAttrs()
            self.attrs.update(scan)

            recordingArgs = self.camerasBeingCaptured, self.recMode, self.savename, self.attrs

            if self.recMode == RecMode.SpecFrames:
                self._master.recordingHelper.startRecording(
                    *recordingArgs, frames=int(self._widget.numExpositionsEdit.text())
                )
            elif self.recMode == RecMode.SpecTime:
                self._master.recordingHelper.startRecording(
                    *recordingArgs, time=float(self._widget.timeToRec.text())
                )
            elif self.recMode == RecMode.ScanOnce:
                self._master.recordingHelper.startRecording(*recordingArgs)
                time.sleep(0.1)
                self._commChannel.prepareScan.emit()
            elif self.recMode == RecMode.ScanLapse:
                self.lapseTotal = int(self._widget.timeLapseEdit.text())
                self.lapseCurrent = 0
                self.nextLapse()
            elif self.recMode == RecMode.DimLapse:
                self.lapseTotal = int(self._widget.totalSlices.text())
                self.lapseCurrent = 0
                self.nextLapse()
            else:
                self._master.recordingHelper.startRecording(*recordingArgs)
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
                    self._commChannel.moveZstage.emit(float(self._widget.stepSizeEdit.text()))
                    self.timer = QtCore.QTimer(singleShot=True)
                    self.timer.timeout.connect(self.nextLapse)
                    self.timer.start(1000)
                else:
                    self._widget.recButton.setChecked(False)
                    self.lapseCurrent = 0
                    self._commChannel.moveZstage.emit(
                        -self.lapseTotal * float(self._widget.stepSizeEdit.text())
                    )
                    self._widget.currentSlice.setText(str(self.lapseCurrent) + ' / ')
                    self._master.recordingHelper.endRecording()

    def nextLapse(self):
        fileName = self.savename + "_" + str(self.lapseCurrent).zfill(len(str(self.lapseTotal)))
        self._master.recordingHelper.startRecording(
            self.camerasBeingCaptured, self.recMode, fileName, self.attrs
        )

        time.sleep(0.3)
        self._commChannel.prepareScan.emit()

    def endRecording(self):
        self._widget.recButton.setChecked(False)
        # self._widget.cameraList.setEnabled(True)
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

    def setCamerasToCapture(self):
        cameraListData = self._widget.cameraList.itemData(self._widget.cameraList.currentIndex())
        if cameraListData == -2:  # All cameras
            # When recording all cameras, the SpecFrames mode isn't supported
            if self.recMode == RecMode.SpecFrames:
                self._widget.untilSTOPbtn.setChecked(True)
            self._widget.specifyFrames.setEnabled(False)
        else:
            self._widget.specifyFrames.setEnabled(True)

    def getCamerasToCapture(self):
        """ Returns a list of which cameras the user has selected to be captured. """
        cameraListData = self._widget.cameraList.itemData(self._widget.cameraList.currentIndex())
        if cameraListData == -1:  # Current camera at start
            return [self._master.cameraHelper.getCurrentCameraName()]
        elif cameraListData == -2:  # All cameras
            return list(self._setupInfo.cameras.keys())
        else:  # A specific camera
            return [cameraListData]

    def getFileName(self):
        """ Gets the filename of the data to save. """
        if self._widget.specifyfile.checkState():
            filename = self._widget.filenameEdit.text()

        else:
            filename = time.strftime('%Hh%Mm%Ss')

        return filename
