# -*- coding: utf-8 -*-
"""
Created on Sun Mar 22 10:40:53 2020

@author: _Xavi
"""
import numpy as np

import controller.presets as presets
from framework import Signal, Thread, Worker
from .basecontrollers import WidgetController


class PositionerController(WidgetController):
    """ Linked to PositionerWidget."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._widget.initControls(self._setupInfo.positioners)
        self.loadPreset(self._defaultPreset)

        # Connect CommunicationChannel signals
        self._commChannel.moveZstage.connect(lambda step: self.move('Z', step))

        # Connect PositionerWidget signals
        for positionerName in self._setupInfo.positioners.keys():
            self._widget.pars['UpButton' + positionerName].pressed.connect(
                lambda positionerName=positionerName: self.move(
                    positionerName,
                    float(self._widget.pars['StepEdit' + positionerName].text())
                )
            )
            self._widget.pars['DownButton' + positionerName].pressed.connect(
                lambda positionerName=positionerName: self.move(
                    positionerName,
                    -float(self._widget.pars['StepEdit' + positionerName].text())
                )
            )

    def move(self, axis, dist):
        """ Moves the piezzos in x y or z (axis) by dist micrometers. """
        newPos = self._master.positionersManager.execOn(axis, lambda p: p.move(dist))
        newText = "<strong>" + axis + " = {0:.2f} µm</strong>".format(newPos)
        self._widget.pars['Label' + axis].setText(newText)

    def getPos(self):
        return self._master.positionersManager.execOnAll(lambda p: p.position)

    def loadPreset(self, preset):
        positionerInfos = self._setupInfo.positioners
        positionerPresets = preset.positioner.positioners

        for positionerName in positionerInfos.keys():
            positionerPreset = (
                positionerPresets[positionerName] if positionerName in positionerPresets
                else presets.PositionerPresetPositioner()
            )
            self._widget.pars['StepEdit' + positionerName].setText(positionerPreset.stepSize)

    def closeEvent(self):
        self._master.positionersManager.execOnAll(lambda p: p.setPosition(0))


class LaserController(WidgetController):
    """ Linked to LaserWidget."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.loadPreset(self._defaultPreset)
        self._widget.initControls(self._master.lasersManager)

        self.aotfLasers = {}
        for laserName, laserManager in self._master.lasersManager:
            if not laserManager.isDigital:
                self.aotfLasers[laserName] = False

        # Connect LaserWidget signals
        for laserModule in self._widget.laserModules.values():
            if not self._master.lasersManager[laserModule.laser].isBinary:
                if self._master.lasersManager[laserModule.laser].isDigital:
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
        self._master.lasersManager.execOnAll(lambda l: l.setDigitalMod(False, 0))
        self._master.lasersManager.execOnAll(lambda l: l.setValue(0))

    def toggleLaser(self, laserName):
        """ Enable or disable laser (on/off)."""
        self._master.lasersManager[laserName].setEnabled(
            self._widget.laserModules[laserName].enableButton.isChecked()
        )

    def changeSlider(self, laserName):
        """ Change power with slider magnitude. """
        magnitude = self._widget.laserModules[laserName].slider.value()
        if laserName not in self.aotfLasers.keys() or not self.aotfLasers[laserName]:
            self._master.lasersManager[laserName].setValue(magnitude)
            self._widget.laserModules[laserName].setPointEdit.setText(str(magnitude))

    def changeEdit(self, laserName):
        """ Change power with edit magnitude. """
        magnitude = float(self._widget.laserModules[laserName].setPointEdit.text())
        if laserName not in self.aotfLasers.keys() or not self.aotfLasers[laserName]:
            self._master.lasersManager[laserName].setValue(magnitude)
            self._widget.laserModules[laserName].slider.setValue(magnitude)

    def updateDigitalPowers(self, laserNames):
        """ Update the powers if the digital mod is on. """
        if self._widget.digModule.DigitalControlButton.isChecked():
            for laserName in laserNames:
                self._master.lasersManager[laserName].setValue(
                    float(self._widget.digModule.powers[laserName].text())
                )

    def GlobalDigitalMod(self, laserNames):
        """ Start digital modulation. """
        digMod = self._widget.digModule.DigitalControlButton.isChecked()
        for laserName in laserNames:
            laserModule = self._widget.laserModules[laserName]
            laserManager = self._master.lasersManager[laserName]

            if laserManager.isBinary:
                continue

            value = float(self._widget.digModule.powers[laserName].text())
            if laserManager.isDigital:
                laserManager.setDigitalMod(digMod, value)
            else:
                laserManager.setValue(value)
                laserModule.enableButton.setChecked(False)
                laserModule.enableButton.setEnabled(not digMod)
                self.aotfLasers[laserName] = digMod
                laserManager.setEnabled(False)  # TODO: Correct?

            laserModule.setPointEdit.setEnabled(not digMod)
            laserModule.slider.setEnabled(not digMod)

            if not digMod:
                self.changeEdit(laserName)

    def setDigitalButton(self, b):
        self._widget.digModule.DigitalControlButton.setChecked(b)
        self.GlobalDigitalMod(
            [laser.name for laser in self._master.lasersManager if laser.isDigital]
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
            self.thread = Thread()
            self.beadWorker.moveToThread(self.thread)
            self.thread.started.connect(self.beadWorker.run)
            self._master.detectorsManager.execOnAll(lambda c: c.flushBuffers())
            self.thread.start()
        else:
            self.running = False
            self.thread.quit()
            self.thread.wait()

    def update(self):
        self._widget.img.setImage(np.resize(self.recIm, self.dims + 1), autoLevels=False)


class BeadWorker(Worker):
    newChunk = Signal()
    stop = Signal()

    def __init__(self, controller):
        super().__init__()
        self.__controller = controller

    def run(self):
        dims = np.array(self.__controller.dims)
        N = (dims[0] + 1) * (dims[1] + 1)
        self.__controller.recIm = np.zeros(N)
        i = 0

        while self.__controller.running:
            newImages, _ = self.__controller._master.detectorsManager.execOnCurrent(lambda c: c.getChunk())
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
