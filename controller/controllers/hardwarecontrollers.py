# -*- coding: utf-8 -*-
"""
Created on Sun Mar 22 10:40:53 2020

@author: _Xavi
"""
import numpy as np
from pyqtgraph.Qt import QtCore

from .basecontrollers import WidgetController


class PositionerController(WidgetController):
    """ Linked to PositionerWidget."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._widget.initControls(self._setupInfo.stagePiezzos)

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

    def closeEvent(self):
        for stagePiezzoId in self._setupInfo.stagePiezzos.keys():
            self._master.nidaqHelper.setAnalog(stagePiezzoId, 0)


class LaserController(WidgetController):
    """ Linked to LaserWidget."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._widget.initControls(self._setupInfo.lasers)

        self.digMod = False
        self.aotfLasers = {}
        for laserId, laserInfo in self._setupInfo.lasers.items():
            if laserInfo.analogChannel is not None:
                self.aotfLasers[laserId] = False

        # Connect LaserWidget signals
        for laserModule in self._widget.laserModules.values():
            if laserModule.laser not in self.aotfLasers:
                self.changeEdit(laserModule.laser)

            laserModule.enableButton.toggled.connect(lambda _, laser=laserModule.laser: self.toggleLaser(laser))
            laserModule.slider.valueChanged[int].connect(lambda _, laser=laserModule.laser: self.changeSlider(laser))
            laserModule.setPointEdit.returnPressed.connect(lambda laser=laserModule.laser: self.changeEdit(laser))

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

    def closeEvent(self):
        for laserId, laserInfo in self._setupInfo.lasers.items():
            if laserId in self.aotfLasers:
                self.setAnalogLaserVoltage(laserId, 0)
                self._master.nidaqHelper.setDigital(laserId, False)
            else:
                self._master.laserHelper.toggleLaser(False, laserId)
                self._master.laserHelper.changePower(0, laserId, False)

    def toggleLaser(self, laser):
        """ Enable or disable laser (on/off)."""
        enable = self._widget.laserModules[laser].enableButton.isChecked()
        if laser in self.aotfLasers.keys():
            if not self.aotfLasers[laser]:
                self._master.nidaqHelper.setDigital(laser, enable)
        else:
            self._master.laserHelper.toggleLaser(enable, laser)

    def changeSlider(self, laser):
        """ Change power with slider magnitude. """
        magnitude = self._widget.laserModules[laser].slider.value()
        if laser in self.aotfLasers.keys():
            if not self.aotfLasers[laser]:
                self.setAnalogLaserVoltage(laser, magnitude)
                self._widget.laserModules[laser].setPointEdit.setText(str(magnitude))
        else:
            self._master.laserHelper.changePower(magnitude, laser, self.digMod)
            self._widget.laserModules[laser].setPointEdit.setText(str(magnitude))

    def changeEdit(self, laser):
        """ Change power with edit magnitude. """
        magnitude = float(self._widget.laserModules[laser].setPointEdit.text())
        if laser in self.aotfLasers.keys():
            if not self.aotfLasers[laser]:
                self.setAnalogLaserVoltage(laser, magnitude)
                self._widget.laserModules[laser].slider.setValue(magnitude)
        else:
            self._master.laserHelper.changePower(magnitude, laser, self.digMod)
            self._widget.laserModules[laser].slider.setValue(magnitude)

    def updateDigitalPowers(self, lasers):
        """ Update the powers if the digital mod is on. """
        self.digMod = self._widget.digModule.DigitalControlButton.isChecked()
        if self.digMod:
            for i in np.arange(len(lasers)):
                laser = lasers[i]
                if laser in self.aotfLasers.keys():
                    self.setAnalogLaserVoltage(laser, float(self._widget.digModule.powers[laser].text()))
                else:
                    self._master.laserHelper.changePower(
                        power=int(self._widget.digModule.powers[laser].text()),
                        laser=laser, dlg=self.digMod
                    )

    def GlobalDigitalMod(self, lasers):
        """ Start digital modulation. """
        self.digMod = self._widget.digModule.DigitalControlButton.isChecked()
        for i in np.arange(len(lasers)):
            laser = lasers[i]
            if laser in self.aotfLasers.keys():
                self.setAnalogLaserVoltage(laser, float(self._widget.digModule.powers[laser].text()))
                self.aotfLasers[laser] = self.digMod
                self._master.nidaqHelper.setDigital(laser, False)
            else:
                self._master.laserHelper.digitalMod(
                    digital=self.digMod, power=int(self._widget.digModule.powers[laser].text()),
                    laser=laser
                )
            if not self.digMod:
                self.changeEdit(laser)

    def setDigitalButton(self, b):
        self._widget.digModule.DigitalControlButton.setChecked(b)
        self.GlobalDigitalMod(
            [laser for laser in self._setupInfo.lasers.keys() if laser not in self.aotfLasers]
        )

    def setAnalogLaserVoltage(self, laserId, voltage):
        laserInfo = self._setupInfo.lasers[laserId]
        self._master.nidaqHelper.setAnalog(
            target=laserId, voltage=voltage,
            min_val=laserInfo.valueRangeMin, max_val=laserInfo.valueRangeMax
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
            self._master.cameraHelper.updateCameraIndices()
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
        pos = self.__controller._widget.ROI.pos()
        size = self.__controller._widget.ROI.size()

        x0 = int(pos[0])
        y0 = int(pos[1])
        x1 = int(x0 + size[0])
        y1 = int(y0 + size[1])

        dims = np.array(self.__controller.dims)
        N = (dims[0] + 1) * (dims[1] + 1)
        self.__controller.recIm = np.zeros(N)
        i = 0

        while self.__controller.running:
            newImages, _ = self.__controller._master.cameraHelper.getChunk()
            n = len(newImages)
            if n > 0:
                for j in range(0, n):
                    img = np.array(newImages[j])
                    img = img[x0:x1, y0:y1]
                    mean = np.mean(img)
                    self.__controller.recIm[i] = mean
                    i = i + 1
                    if i == N:
                        i = 0
                self.newChunk.emit()
