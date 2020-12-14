# -*- coding: utf-8 -*-
"""
Created on Sun Mar 22 10:40:53 2020

@author: _Xavi
"""
import numpy as np
from pyqtgraph.Qt import QtCore

import controller.presets as presets
from .basecontrollers import WidgetController


class PositionerController(WidgetController):
    """ Linked to PositionerWidget."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._widget.initControls(self._setupInfo.stagePiezzos)
        self.loadPreset(self._defaultPreset)

        self.stagePos = {}
        for stagePiezzoId in self._setupInfo.stagePiezzos.keys():
            self.stagePos[stagePiezzoId] = 0

        # Connect CommunicationChannel signals
        self._commChannel.moveZstage.connect(lambda step: self.move('Z', step))

        # Connect PositionerWidget signals
        for stagePiezzoId in self._setupInfo.stagePiezzos.keys():
            self._widget.pars['UpButton' + stagePiezzoId].pressed.connect(
                lambda stagePiezzoId=stagePiezzoId: self.move(
                    stagePiezzoId,
                    float(self._widget.pars['StepEdit' + stagePiezzoId].text())
                )
            )
            self._widget.pars['DownButton' + stagePiezzoId].pressed.connect(
                lambda stagePiezzoId=stagePiezzoId: self.move(
                    stagePiezzoId,
                    -float(self._widget.pars['StepEdit' + stagePiezzoId].text())
                )
            )

    def move(self, axis, dist):
        """ Moves the piezzos in x y or z (axis) by dist micrometers. """

        stagePiezzoInfo = self._setupInfo.stagePiezzos[axis]

        self.stagePos[axis] += dist
        self._master.nidaqHelper.setAnalog(target=axis,
                                           voltage=self.stagePos[axis] / stagePiezzoInfo.conversionFactor,
                                           min_val=stagePiezzoInfo.minVolt, max_val=stagePiezzoInfo.maxVolt)

        newText = "<strong>" + axis + " = {0:.2f} µm</strong>".format(self.stagePos[axis])
        self._widget.pars['Label' + axis].setText(newText)

    def getPos(self):
        return self.stagePos

    def loadPreset(self, preset):
        stagePiezzoInfos = self._setupInfo.stagePiezzos
        stagePiezzoPresets = preset.positioner.stagePiezzos

        for stagePiezzoId in stagePiezzoInfos.keys():
            stagePiezzoPreset = (
                stagePiezzoPresets[stagePiezzoId] if stagePiezzoId in stagePiezzoPresets
                else presets.PositionerPresetStagePiezzo()
            )
            self._widget.pars['StepEdit' + stagePiezzoId].setText(stagePiezzoPreset.stepSize)

    def closeEvent(self):
        for stagePiezzoId in self._setupInfo.stagePiezzos.keys():
            self._master.nidaqHelper.setAnalog(stagePiezzoId, 0)


class LaserController(WidgetController):
    """ Linked to LaserWidget."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._widget.initControls(self._setupInfo.lasers)
        self.loadPreset(self._defaultPreset)

        self.digMod = False
        self.aotfLasers = {}
        self.binaryLasers = set()
        for laserName, laserInfo in self._setupInfo.lasers.items():
            if laserInfo.isBinary():
                self.binaryLasers.add(laserName)
            elif laserInfo.isAotf():
                self.aotfLasers[laserName] = False

        # Connect LaserWidget signals
        for laserModule in self._widget.laserModules.values():
            if laserModule.laser not in self.binaryLasers:
                if laserModule.laser not in self.aotfLasers:
                    self.changeEdit(laserModule.laser)

                laserModule.slider.valueChanged[int].connect(lambda _, laser=laserModule.laser: self.changeSlider(laser))
                laserModule.setPointEdit.returnPressed.connect(lambda laser=laserModule.laser: self.changeEdit(laser))

            laserModule.enableButton.toggled.connect(lambda _, laser=laserModule.laser: self.toggleLaser(laser))

        for digModuleLaser in self._widget.digModule.powers.keys():
            self._widget.digModule.powers[digModuleLaser].textChanged.connect(
                lambda _, laser=digModuleLaser: self.updateDigitalPowers([laser])
            )

        self._widget.digModule.DigitalControlButton.clicked.connect(
            lambda: self.GlobalDigitalMod(list(self._widget.digModule.powers.keys()))
        )
        self._widget.digModule.updateDigPowersButton.clicked.connect(
            lambda: self.updateDigitalPowers(list(self._widget.digModule.powers.keys()))
        )

    def loadPreset(self, preset):
        laserInfos = self._setupInfo.lasers
        laserPresets = self._defaultPreset.laserControl.lasers

        for laserName in laserInfos.keys():
            laserPreset = (laserPresets[laserName] if laserName in laserPresets
                           else presets.LaserControlPresetLaser())

            self._widget.laserModules[laserName].setPointEdit.setText(laserPreset.value)
            self._widget.laserModules[laserName].slider.setValue(float(laserPreset.value))
            self._widget.digModule.powers[laserName].setText(laserPreset.value)

    def closeEvent(self):
        for laserName, laserInfo in self._setupInfo.lasers.items():
            if laserName in self.aotfLasers:
                self._master.laserHelper.changeVoltage(laserName, 0)
            else:
                self._master.laserHelper.changePower(laserName, 0, False)

            self._master.laserHelper.setEnabled(laserName, False)

    def toggleLaser(self, laserName):
        """ Enable or disable laser (on/off)."""
        enable = self._widget.laserModules[laserName].enableButton.isChecked()
        self._master.laserHelper.setEnabled(laserName, enable)

    def changeSlider(self, laserName):
        """ Change power with slider magnitude. """
        magnitude = self._widget.laserModules[laserName].slider.value()
        if laserName in self.aotfLasers.keys():
            if not self.aotfLasers[laserName]:
                self._master.laserHelper.changeVoltage(laserName, magnitude)
                self._widget.laserModules[laserName].setPointEdit.setText(str(magnitude))
        else:
            self._master.laserHelper.changePower(laserName, magnitude, self.digMod)
            self._widget.laserModules[laserName].setPointEdit.setText(str(magnitude))

    def changeEdit(self, laserName):
        """ Change power with edit magnitude. """
        magnitude = float(self._widget.laserModules[laserName].setPointEdit.text())
        if laserName in self.aotfLasers.keys():
            if not self.aotfLasers[laserName]:
                self._master.laserHelper.changeVoltage(laserName, magnitude)
                self._widget.laserModules[laserName].slider.setValue(magnitude)
        else:
            self._master.laserHelper.changePower(laserName, magnitude, self.digMod)
            self._widget.laserModules[laserName].slider.setValue(magnitude)

    def updateDigitalPowers(self, laserNames):
        """ Update the powers if the digital mod is on. """
        self.digMod = self._widget.digModule.DigitalControlButton.isChecked()
        if self.digMod:
            for laserName in laserNames:
                if laserName in self.aotfLasers.keys():
                    self._master.laserHelper.changeVoltage(
                        laserName=laserName,
                        voltage=float(self._widget.digModule.powers[laserName].text())
                    )
                else:
                    self._master.laserHelper.changePower(
                        laserName=laserName,
                        power=int(self._widget.digModule.powers[laserName].text()), dig=self.digMod
                    )

    def GlobalDigitalMod(self, laserNames):
        """ Start digital modulation. """
        self.digMod = self._widget.digModule.DigitalControlButton.isChecked()
        for laserName in laserNames:
            if laserName in self.aotfLasers.keys():
                self._master.laserHelper.changeVoltage(
                    laserName=laserName,
                    voltage=float(self._widget.digModule.powers[laserName].text())
                )
                self._widget.laserModules[laserName].enableButton.setChecked(False)
                self.aotfLasers[laserName] = self.digMod
                self._master.laserHelper.setEnabled(laserName, False)  # TODO: Correct?
            else:
                self._master.laserHelper.digitalMod(
                    laserName=laserName, digital=self.digMod,
                    power=int(self._widget.digModule.powers[laserName].text())
                )

            if not self.digMod:
                self.changeEdit(laserName)

    def setDigitalButton(self, b):
        self._widget.digModule.DigitalControlButton.setChecked(b)
        self.GlobalDigitalMod(
            [laser for laser in self._setupInfo.lasers.keys() if laser not in self.aotfLasers]
        )


class BeadController(WidgetController):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.running = False
        self.addROI()

        # Connect BeadRecWidget signals
        self._widget.roiButton.clicked.connect(self.toggleROI)
        self._widget.runButton.clicked.connect(self.run)

    def toggleROI(self):
        """ Show or hide ROI."""
        if self._widget.roiButton.isChecked() is False:
            self._widget.ROI.hide()
            self.active = False
            self._widget.roiButton.setText('Show ROI')
        else:
            ROIsize = (64, 64)
            ROIcenter = self._commChannel.getCenterROI()

            ROIpos = (ROIcenter[0] - 0.5 * ROIsize[0],
                      ROIcenter[1] - 0.5 * ROIsize[1])

            self._widget.ROI.setPos(ROIpos)
            self._widget.ROI.setSize(ROIsize)
            self._widget.ROI.show()
            self.active = True
            self._widget.roiButton.setText('Hide ROI')

    def addROI(self):
        """ Adds the ROI to ImageWidget viewbox through the CommunicationChannel. """
        self._commChannel.addItemTovb.emit(self._widget.ROI)

    def run(self):
        if not self.running:
            self.dims = np.array(self._commChannel.getDimsScan()).astype(int)
            self.running = True
            self.beadWorker = BeadWorker(self)
            self.beadWorker.newChunk.connect(self.update)
            self.thread = QtCore.QThread()
            self.beadWorker.moveToThread(self.thread)
            self.thread.started.connect(self.beadWorker.run)
            self._master.cameraHelper.execOnAll(lambda c: c.updateCameraIndices())
            self.thread.start()
        else:
            self.running = False
            self.thread.quit()
            self.thread.wait()

    def update(self):
        self._widget.img.setImage(np.resize(self.recIm, self.dims + 1), autoLevels=False)


class BeadWorker(QtCore.QObject):
    newChunk = QtCore.pyqtSignal()
    stop = QtCore.pyqtSignal()

    def __init__(self, controller, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__controller = controller

    def run(self):
        dims = np.array(self.__controller.dims)
        N = (dims[0] + 1) * (dims[1] + 1)
        self.__controller.recIm = np.zeros(N)
        i = 0

        while self.__controller.running:
            newImages, _ = self.__controller._master.cameraHelper.execOnCurrent(lambda c: c.getChunk())
            n = len(newImages)
            if n > 0:
                pos = self.__controller._widget.ROI.pos()
                size = self.__controller._widget.ROI.size()

                x0 = int(pos[0])
                y0 = int(pos[1])
                x1 = int(x0 + size[0])
                y1 = int(y0 + size[1])

                for j in range(0, n):
                    img = newImages[j]
                    img = img[x0:x1, y0:y1]
                    mean = np.mean(img)
                    self.__controller.recIm[i] = mean
                    i = i + 1
                    if i == N:
                        i = 0
                self.newChunk.emit()
