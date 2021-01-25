# -*- coding: utf-8 -*-
"""
Created on Sun Mar 22 10:40:53 2020

@author: _Xavi
"""
import os
import subprocess
import sys
import time
from dataclasses import dataclass
from typing import Any

import numpy as np
from imcommon.framework import Timer

import imcontrol.view.guitools as guitools
from imcontrol.controller import configfileutils
from imcontrol.model.managers.RecordingManager import RecMode
from .basecontrollers import ImConWidgetController, LiveUpdatedController


@dataclass
class SettingsControllerParams:
    model: Any
    binning: Any
    frameMode: Any
    x0: Any
    y0: Any
    width: Any
    height: Any
    applyROI: Any
    newROI: Any
    abortROI: Any
    saveMode: Any
    deleteMode: Any
    allDetectorsFrame: Any


class SettingsController(ImConWidgetController):
    """ Linked to SettingsWidget."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.allParams = {}

        if not self._master.detectorsManager.hasDetectors():
            return

        self._widget.initControls(
            self._setupInfo.rois,
            self._master.detectorsManager.execOnAll(
                lambda c: (c.parameters, c.supportedBinnings)
            )
        )

        self.addROI()
        self.initParameters()
        execOnAll = self._master.detectorsManager.execOnAll
        execOnAll(lambda c: (self.updateParamsFromDetector(detector=c)))
        execOnAll(lambda c: (self.adjustFrame(detector=c)))
        execOnAll(lambda c: (self.updateFrame(detector=c)))
        execOnAll(lambda c: (self.updateFrameActionButtons(detector=c)))

        # Connect CommunicationChannel signals
        self._commChannel.detectorSwitched.connect(self.detectorSwitched)

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
        """ Take parameters from the detector Tree map. """
        for detectorName in self._master.detectorsManager.getAllDetectorNames():
            detectorTree = self._widget.trees[detectorName]
            framePar = detectorTree.p.param('Image frame')
            self.allParams[detectorName] = SettingsControllerParams(
                model=detectorTree.p.param('Model'),
                binning=framePar.param('Binning'),
                frameMode=framePar.param('Mode'),
                x0=framePar.param('X0'),
                y0=framePar.param('Y0'),
                width=framePar.param('Width'),
                height=framePar.param('Height'),
                applyROI=framePar.param('Apply'),
                newROI=framePar.param('New ROI'),
                abortROI=framePar.param('Abort ROI'),
                saveMode=framePar.param('Save mode'),
                deleteMode=framePar.param('Delete mode'),
                allDetectorsFrame=framePar.param('Update all detectors')
            )

            params = self.allParams[detectorName]
            params.binning.sigValueChanged.connect(self.setBinning)
            params.frameMode.sigValueChanged.connect(self.updateFrame)
            params.applyROI.sigActivated.connect(self.adjustFrame)
            params.newROI.sigActivated.connect(self.updateFrame)
            params.abortROI.sigActivated.connect(self.abortROI)
            params.saveMode.sigActivated.connect(self.saveMode)
            params.deleteMode.sigActivated.connect(self.deleteMode)

            syncFrameParamsWithoutUpdates = lambda: self.syncFrameParams(False, False)
            params.x0.sigValueChanged.connect(syncFrameParamsWithoutUpdates)
            params.y0.sigValueChanged.connect(syncFrameParamsWithoutUpdates)
            params.width.sigValueChanged.connect(syncFrameParamsWithoutUpdates)
            params.height.sigValueChanged.connect(syncFrameParamsWithoutUpdates)
            params.allDetectorsFrame.sigValueChanged.connect(self.syncFrameParams)

        detectorsParameters = self._master.detectorsManager.execOnAll(lambda c: c.parameters)
        for detectorName, detectorParameters in detectorsParameters.items():
            for parameterName, parameter in detectorParameters.items():
                paramInWidget = self._widget.trees[detectorName].p.param(parameter.group).param(parameterName)
                paramInWidget.sigValueChanged.connect(
                    lambda _, value, detectorName=detectorName, parameterName=parameterName:
                        self.setDetectorParameter(detectorName, parameterName, value)
                )

    def adjustFrame(self, *, detector=None):
        """ Crop detector and adjust frame. """

        if detector is None:
            self.getDetectorManagerFrameExecFunc()(lambda c: self.adjustFrame(detector=c))
            return

        # Adjust frame
        params = self.allParams[detector.name]
        binning = int(params.binning.value())
        width = params.width.value()
        height = params.height.value()
        x0 = params.x0.value()
        y0 = params.y0.value()

        # Round to closest "divisable by 4" value.
        hpos = binning * x0
        vpos = binning * y0
        hsize = binning * height
        vsize = binning * width

        hmodulus = 4
        vmodulus = 4
        vpos = int(vmodulus * np.ceil(vpos / vmodulus))
        hpos = int(hmodulus * np.ceil(hpos / hmodulus))
        vsize = int(vmodulus * np.ceil(vsize / vmodulus))
        hsize = int(hmodulus * np.ceil(hsize / hmodulus))

        detector.crop(hpos, vpos, hsize, vsize)

        # Final shape values might differ from the user-specified one because of detector limitation x128
        width, height = detector.shape
        if detector.name == self._master.detectorsManager.getCurrentDetectorName():
            self._commChannel.adjustFrame.emit(width, height)
            self._widget.ROI.hide()

        self.updateParamsFromDetector(detector=detector)

    def ROIchanged(self):
        """ Update parameters according to ROI. """
        frameStart = self._master.detectorsManager.execOnCurrent(lambda c: c.frameStart)
        pos = self._widget.ROI.pos()
        size = self._widget.ROI.size()

        currentParams = self.getCurrentParams()
        currentParams.x0.setValue(frameStart[0] + int(pos[0]))
        currentParams.y0.setValue(frameStart[1] + int(pos[1]))
        currentParams.width.setValue(size[0])  # [0] is Width
        currentParams.height.setValue(size[1])  # [1] is Height

    def updateFrameActionButtons(self, *, detector=None):
        """ Shows the frame-related buttons appropriate for the current frame
        mode, and hides the others. """

        if detector is None:
            self.getDetectorManagerFrameExecFunc()(lambda c: self.updateFrameActionButtons(detector=c))
            return

        params = self.allParams[detector.name]

        params.applyROI.hide()
        params.newROI.hide()
        params.abortROI.hide()
        params.saveMode.hide()
        params.deleteMode.hide()

        if params.frameMode.value() == 'Custom':
            params.applyROI.show()
            params.newROI.show()
            params.abortROI.show()
            params.saveMode.show()
        elif params.frameMode.value() != 'Full chip':
            params.deleteMode.show()

    def abortROI(self):
        """ Cancel and reset parameters of the ROI. """
        self.toggleROI(False)
        frameStart = self._master.detectorsManager.execOnCurrent(lambda c: c.frameStart)
        shapes = self._master.detectorsManager.execOnCurrent(lambda c: c.shape)

        currentParams = self.getCurrentParams()
        currentParams.x0.setValue(frameStart[0])
        currentParams.y0.setValue(frameStart[1])
        currentParams.width.setValue(shapes[0])
        currentParams.height.setValue(shapes[1])

    def saveMode(self):
        """ Save the current frame mode parameters to the mode list. """

        currentParams = self.getCurrentParams()
        x0, y0, width, height = (currentParams.x0.value(), currentParams.y0.value(),
                                 currentParams.width.value(), currentParams.height.value())

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
            # Add in GUI
            if not alreadyExists:
                for params in self.allParams.values():
                    newModeItems = params.frameMode.opts['limits'].copy()
                    newModeItems.insert(len(newModeItems) - 1, name)
                    params.frameMode.setLimits(newModeItems)

            # Set in setup info
            self._setupInfo.setROI(name, x0, y0, width, height)
            configfileutils.saveSetupInfo(self._setupInfo)

    def deleteMode(self):
        """ Delete the current frame mode from the mode list (if it's a saved
        custom ROI). """

        currentParams = self.getCurrentParams()
        modeToDelete = currentParams.frameMode.value()

        confirmationResult = guitools.askYesNoQuestion(
            self._widget,
            'Delete frame mode?',
            f'Are you sure you want to delete the mode "{modeToDelete}"?'
        )

        if confirmationResult:
            # Remove in GUI
            for params in self.allParams.values():
                newModeItems = params.frameMode.opts['limits'].copy()
                newModeItems = [value for value in newModeItems if value != modeToDelete]
                params.frameMode.setLimits(newModeItems)

            # Remove from setup info
            self._setupInfo.removeROI(modeToDelete)
            configfileutils.saveSetupInfo(self._setupInfo)

    def setBinning(self):
        """ Update a new binning to the detector. """
        self.getDetectorManagerFrameExecFunc()(
            lambda c: c.setBinning(int(self.allParams[c.name].binning.value()))
        )

    def setDetectorParameter(self, detectorName, parameterName, value):
        """ Update a new exposure time to the detector. """

        if parameterName in ['Trigger source'] and self.getCurrentParams().allDetectorsFrame.value():
            # Special case for certain parameters that will follow the "update all detectors" option
            execFunc = self._master.detectorsManager.execOnAll
        else:
            execFunc = lambda f: self._master.detectorsManager.execOn(detectorName, f)

        execFunc(
            lambda c: (c.setParameter(parameterName, value) and
                       self.updateParamsFromDetector(detector=c))
        )

    def updateParamsFromDetector(self, *, detector):
        """ Update the parameter values from the detector. """

        params = self.allParams[detector.name]

        # Detector parameters
        for parameterName, parameter in detector.parameters.items():
            paramInWidget = self._widget.trees[detector.name].p.param(parameter.group).param(parameterName)
            paramInWidget.setValue(parameter.value)

        # Frame
        params.binning.setValue(detector.binning)
        frameStart = detector.frameStart
        shape = detector.shape
        fullShape = detector.fullShape
        params.x0.setValue(frameStart[0])
        params.y0.setValue(frameStart[1])
        params.width.setValue(shape[0])
        params.width.setLimits((1, fullShape[0]))
        params.height.setValue(shape[1])
        params.height.setLimits((1, fullShape[1]))

        # Model
        params.model.setValue(detector.model)

    def updateFrame(self, *, detector=None):
        """ Change the image frame size and position in the sensor. """

        if detector is None:
            self.getDetectorManagerFrameExecFunc()(lambda c: self.updateFrame(detector=c))
            return

        params = self.allParams[detector.name]
        frameMode = self.getCurrentParams().frameMode.value()
        customFrame = frameMode == 'Custom'

        params.x0.setWritable(customFrame)
        params.y0.setWritable(customFrame)
        params.width.setWritable(customFrame)
        params.height.setWritable(customFrame)
        # Call .show() to prevent view alignment issues
        params.x0.show()
        params.y0.show()
        params.width.show()
        params.height.show()

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
            if frameMode == 'Full chip':
                fullChipShape = detector.fullShape
                params.x0.setValue(0)
                params.y0.setValue(0)
                params.width.setValue(fullChipShape[0])
                params.height.setValue(fullChipShape[1])
            else:
                roiInfo = self._setupInfo.rois[frameMode]
                params.x0.setValue(roiInfo.x)
                params.y0.setValue(roiInfo.y)
                params.width.setValue(roiInfo.w)
                params.height.setValue(roiInfo.h)

            self.adjustFrame(detector=detector)

        self.syncFrameParams(doAdjustFrame=False)

    def detectorSwitched(self, newDetectorName, _):
        """ Called when the user switches to another detector. """
        self._widget.setDisplayedDetector(newDetectorName)
        newDetectorShape = self._master.detectorsManager[newDetectorName].shape
        self._commChannel.adjustFrame.emit(*newDetectorShape)

    def getCamAttrs(self):
        return self._master.detectorsManager.execOnAll(
            lambda c: {
                **{
                    'Detector:Pixel size': c.pixelSize,
                    'Detector:Model': c.model,
                    'Detector:Binning': c.binning,
                    'Detector:ROI': [*c.frameStart, *c.shape]
                },
                **{f'DetectorParam:{k}': v.value for k, v in c.parameters.items()}
            }
        )

    def syncFrameParams(self, doAdjustFrame=True, doUpdateFrameActionButtons=True):
        currentParams = self.getCurrentParams()
        shouldSync = currentParams.allDetectorsFrame.value()

        for params in self.allParams.values():
            params.allDetectorsFrame.setValue(shouldSync)
            if shouldSync:
                params.frameMode.setValue(currentParams.frameMode.value())
                params.x0.setValue(currentParams.x0.value())
                params.y0.setValue(currentParams.y0.value())
                params.width.setValue(currentParams.width.value())
                params.height.setValue(currentParams.height.value())

        if shouldSync and doAdjustFrame:
            self.adjustFrame()

        if doUpdateFrameActionButtons:
            self.updateFrameActionButtons()

    def getCurrentParams(self):
        return self.allParams[self._master.detectorsManager.getCurrentDetectorName()]

    def getDetectorManagerFrameExecFunc(self):
        """ Returns the detector manager exec function that should be used for
        frame-related changes. """
        currentParams = self.getCurrentParams()
        detectorsManager = self._master.detectorsManager
        return (detectorsManager.execOnAll if currentParams.allDetectorsFrame.value()
                else detectorsManager.execOnCurrent)


class ViewController(ImConWidgetController):
    """ Linked to ViewWidget."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._widget.initControls(self._master.detectorsManager.execOnAll(lambda c: c.model))

        # Connect ViewWidget signals
        self._widget.gridButton.clicked.connect(self.gridToggle)
        self._widget.crosshairButton.clicked.connect(self.crosshairToggle)
        self._widget.liveviewButton.clicked.connect(self.liveview)
        self._widget.detectorList.currentIndexChanged.connect(self.detectorSwitch)
        self._widget.nextDetectorButton.clicked.connect(self.detectorNext)

    def liveview(self):
        """ Start liveview and activate detector acquisition. """
        self._widget.crosshairButton.setEnabled(True)
        self._widget.gridButton.setEnabled(True)
        if self._widget.liveviewButton.isChecked():
            self._master.detectorsManager.startAcquisition()
        else:
            self._master.detectorsManager.stopAcquisition()

    def gridToggle(self):
        """ Connect with grid toggle from Image Widget through communication channel. """
        self._commChannel.gridToggle.emit()

    def crosshairToggle(self):
        """ Connect with crosshair toggle from Image Widget through communication channel. """
        self._commChannel.crosshairToggle.emit()

    def detectorSwitch(self, listIndex):
        """ Changes the current detector to the selected detector. """
        detectorName = self._widget.detectorList.itemData(listIndex)
        self._master.detectorsManager.setCurrentDetector(detectorName)

    def detectorNext(self):
        """ Changes the current detector to the next detector. """
        self._widget.detectorList.setCurrentIndex(
            (self._widget.detectorList.currentIndex() + 1) % self._widget.detectorList.count()
        )

    def closeEvent(self):
        self._master.detectorsManager.stopAcquisition()


class ImageController(LiveUpdatedController):
    """ Linked to ImageWidget."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if not self._master.detectorsManager.hasDetectors():
            return

        self._lastWidth, self._lastHeight = self._master.detectorsManager.execOnCurrent(
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
        self._commChannel.detectorSwitched.connect(self.restoreSavedLevels)

        # Connect ImageWidget signals
        self._widget.levelsButton.pressed.connect(self.autoLevels)
        self._widget.vb.sigResized.connect(lambda: self.adjustFrame(self._lastWidth, self._lastHeight))
        self._widget.hist.sigLevelsChanged.connect(self.updateSavedLevels)

    def autoLevels(self, im=None):
        """ Set histogram levels automatically with current detector image."""
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
        detectorName = self._master.detectorsManager.getCurrentDetectorName()
        self._savedLevels[detectorName] = self._widget.hist.getLevels()

    def restoreSavedLevels(self, newDetectorName):
        """ Updates image levels from saved levels for detector that is switched to. """
        if newDetectorName in self._savedLevels:
            self._widget.hist.setLevels(*self._savedLevels[newDetectorName])


class RecorderController(ImConWidgetController):
    """ Linked to RecordingWidget. """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._widget.initControls(self._master.detectorsManager.execOnAll(lambda c: c.model))

        self.lapseCurrent = 0
        self.lapseTotal = 0

        imreconstructRegistered = self._moduleCommChannel.isModuleRegistered('imreconstruct')
        self._widget.keepInMemoryCheckbox.setVisible(imreconstructRegistered)
        if not imreconstructRegistered:
            self._widget.keepInMemoryCheckbox.setChecked(False)

        self.untilStop()

        # Connect CommunicationChannel signals
        self._commChannel.endRecording.connect(self.endRecording)
        self._commChannel.updateRecFrameNum.connect(self.updateRecFrameNum)
        self._commChannel.updateRecTime.connect(self.updateRecTime)
        self._commChannel.endScan.connect(self.scanDone)

        # Connect RecordingWidget signals
        self._widget.detectorList.currentIndexChanged.connect(self.setDetectorsToCapture)
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
        detectorNames = self.getDetectorsToCapture()
        folder = self._widget.folderEdit.text()
        if not os.path.exists(folder):
            os.mkdir(folder)
        time.sleep(0.01)
        name = os.path.join(folder, self.getFileName()) + '_snap'
        savename = guitools.getUniqueName(name)
        attrs = self._commChannel.getCamAttrs()
        self._master.recordingManager.snap(detectorNames, savename, attrs)

    def toggleREC(self, checked):
        """ Start or end recording. """
        if checked:
            # self._widget.detectorList.setEnabled(False)

            folder = self._widget.folderEdit.text()
            if not os.path.exists(folder):
                os.mkdir(folder)
            time.sleep(0.01)
            name = os.path.join(folder, self.getFileName()) + '_rec'
            self.savename = guitools.getUniqueName(name)
            self.keepInMemory = self._widget.keepInMemoryCheckbox.isChecked()

            self.detectorsBeingCaptured = self.getDetectorsToCapture()
            self.attrs = self._commChannel.getCamAttrs()
            for attrDict in self.attrs.values():
                attrDict.update(self._commChannel.getScanStageAttrs())
                attrDict.update(self._commChannel.getScanTTLAttrs())

            recordingArgs = (self.detectorsBeingCaptured, self.recMode, self.savename,
                             self.keepInMemory, self.attrs)

            if self.recMode == RecMode.SpecFrames:
                self._master.recordingManager.startRecording(
                    *recordingArgs, recFrames=int(self._widget.numExpositionsEdit.text())
                )
            elif self.recMode == RecMode.SpecTime:
                self._master.recordingManager.startRecording(
                    *recordingArgs, recTime=float(self._widget.timeToRec.text())
                )
            elif self.recMode == RecMode.ScanOnce:
                self._master.recordingManager.startRecording(*recordingArgs)
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
                self._master.recordingManager.startRecording(*recordingArgs)
        else:
            self._master.recordingManager.endRecording()

    def scanDone(self):
        if self._widget.recButton.isChecked():
            if self.recMode == RecMode.ScanOnce:
                self._widget.recButton.setChecked(False)
                self._master.recordingManager.endRecording()
            elif self.recMode == RecMode.ScanLapse:
                self.lapseCurrent += 1
                if self.lapseCurrent < self.lapseTotal:
                    self._master.recordingManager.endRecording(emitSignal=False)
                    self._widget.currentLapse.setText(str(self.lapseCurrent) + ' / ')
                    self.timer = Timer(singleShot=True)
                    self.timer.timeout.connect(self.nextLapse)
                    self.timer.start(int(float(self._widget.freqEdit.text()) * 1000))
                else:
                    self._widget.recButton.setChecked(False)
                    self.lapseCurrent = 0
                    self._widget.currentLapse.setText(str(self.lapseCurrent) + ' / ')
                    self._master.recordingManager.endRecording()
            elif self.recMode == RecMode.DimLapse:
                self.lapseCurrent += 1
                if self.lapseCurrent < self.lapseTotal:
                    self._widget.currentSlice.setText(str(self.lapseCurrent) + ' / ')
                    self._master.recordingManager.endRecording(emitSignal=False)
                    time.sleep(0.3)
                    self._commChannel.moveZstage.emit(float(self._widget.stepSizeEdit.text()))
                    self.timer = Timer(singleShot=True)
                    self.timer.timeout.connect(self.nextLapse)
                    self.timer.start(1000)
                else:
                    self._widget.recButton.setChecked(False)
                    self.lapseCurrent = 0
                    self._commChannel.moveZstage.emit(
                        -self.lapseTotal * float(self._widget.stepSizeEdit.text())
                    )
                    self._widget.currentSlice.setText(str(self.lapseCurrent) + ' / ')
                    self._master.recordingManager.endRecording()

    def nextLapse(self):
        fileName = self.savename + "_" + str(self.lapseCurrent).zfill(len(str(self.lapseTotal)))
        self._master.recordingManager.startRecording(
            self.detectorsBeingCaptured, self.recMode, fileName, self.attrs
        )

        time.sleep(0.3)
        self._commChannel.prepareScan.emit()

    def endRecording(self):
        self._widget.recButton.setChecked(False)
        # self._widget.detectorList.setEnabled(True)
        self._widget.currentFrame.setText('0 / ')

    def updateRecFrameNum(self, f):
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

    def setDetectorsToCapture(self):
        detectorListData = self._widget.detectorList.itemData(self._widget.detectorList.currentIndex())
        if detectorListData == -2:  # All detectors
            # When recording all detectors, the SpecFrames mode isn't supported
            if self.recMode == RecMode.SpecFrames:
                self._widget.untilSTOPbtn.setChecked(True)
            self._widget.specifyFrames.setEnabled(False)
        else:
            self._widget.specifyFrames.setEnabled(True)

    def getDetectorsToCapture(self):
        """ Returns a list of which detectors the user has selected to be captured. """
        detectorListData = self._widget.detectorList.itemData(self._widget.detectorList.currentIndex())
        if detectorListData == -1:  # Current detector at start
            return [self._master.detectorsManager.getCurrentDetectorName()]
        elif detectorListData == -2:  # All detectors
            return list(self._setupInfo.detectors.keys())
        else:  # A specific detector
            return [detectorListData]

    def getFileName(self):
        """ Gets the filename of the data to save. """
        if self._widget.specifyfile.checkState():
            filename = self._widget.filenameEdit.text()

        else:
            filename = time.strftime('%Hh%Mm%Ss')

        return filename
