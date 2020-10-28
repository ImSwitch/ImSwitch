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
        self.stagePos = [0, 0, 0]
        self.convFactors = [1.5870, 1.5907, 10]
        self.targets = ['Stage_X', 'Stage_Y', 'Stage_Z']
        self.minVolt = [-10, -10, 0]  # piezzoconcept
        self.maxVolt = [10, 10, 10]  # piezzoconcept

        # Connect PositionerWidget signals
        self._widget.xUpButton.pressed.connect(lambda: self.move(0, float(self._widget.xStepEdit.text())))
        self._widget.xDownButton.pressed.connect(lambda: self.move(0, -float(self._widget.xStepEdit.text())))
        self._widget.yUpButton.pressed.connect(lambda: self.move(1, float(self._widget.yStepEdit.text())))
        self._widget.yDownButton.pressed.connect(lambda: self.move(1, -float(self._widget.yStepEdit.text())))
        self._widget.zUpButton.pressed.connect(lambda: self.move(2, float(self._widget.zStepEdit.text())))
        self._widget.zDownButton.pressed.connect(lambda: self.move(2, -float(self._widget.zStepEdit.text())))

    def move(self, axis, dist):
        """ Moves the piezzos in x y or z (axis) by dist micrometers. """
        self.stagePos[axis] += dist
        self._master.nidaqHelper.setAnalog(target=self.targets[axis],
                                           voltage=self.stagePos[axis] / self.convFactors[axis],
                                           min_val=self.minVolt[axis], max_val=self.maxVolt[axis])
        newText = "<strong>" + ['x', 'y', 'z'][axis] + " = {0:.2f} µm</strong>".format(
            self.stagePos[axis])

        getattr(self._widget, ['x', 'y', 'z'][axis] + "Label").setText(newText)

    def getPos(self):
        return {'X': self.stagePos[0], 'Y': self.stagePos[1], 'Z': self.stagePos[2]}

    def closeEvent(self):
        self._master.nidaqHelper.setAnalog(self.targets[0], 0)
        self._master.nidaqHelper.setAnalog(self.targets[1], 0)
        self._master.nidaqHelper.setAnalog(self.targets[2], 0)


class LaserController(WidgetController):
    """ Linked to LaserWidget."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.digMod = False
        self.aotfLasers = {'473': False}

        # Connect LaserWidget signals
        for laserModule in self._widget.laserModules.values():
            if not laserModule.laser == '473': self.changeEdit(laserModule.laser)
            laserModule.enableButton.toggled.connect(lambda: self.toggleLaser(laserModule.laser))
            laserModule.slider.valueChanged[int].connect(lambda: self.changeSlider(laserModule.laser))
            laserModule.setPointEdit.returnPressed.connect(lambda: self.changeEdit(laserModule.laser))

        self._widget.digModule.powers['405'].textChanged.connect(lambda: self.updateDigitalPowers(['405']))
        self._widget.digModule.powers['488'].textChanged.connect(lambda: self.updateDigitalPowers(['488']))
        self._widget.digModule.powers['473'].textChanged.connect(lambda: self.updateDigitalPowers(['473']))
        self._widget.digModule.DigitalControlButton.clicked.connect(
            lambda: self.GlobalDigitalMod(['405', '473', '488'])
        )
        self._widget.digModule.updateDigPowersButton.clicked.connect(
            lambda: self.updateDigitalPowers(['405', '473', '488'])
        )

    def closeEvent(self):
        self._master.laserHelper.toggleLaser(False, '405')
        self._master.laserHelper.changePower(0, '405', False)
        self._master.laserHelper.toggleLaser(False, '488')
        self._master.laserHelper.changePower(0, '488', False)
        self._master.nidaqHelper.setAnalog('473', 0, min_val=0, max_val=5)
        self._master.nidaqHelper.setDigital('473', False)

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
                self._master.nidaqHelper.setAnalog(laser, magnitude, min_val=0, max_val=5)
                self._widget.laserModules[laser].setPointEdit.setText(str(magnitude))
        else:
            self._master.laserHelper.changePower(magnitude, laser, self.digMod)
            self._widget.laserModules[laser].setPointEdit.setText(str(magnitude))

    def changeEdit(self, laser):
        """ Change power with edit magnitude. """
        magnitude = float(self._widget.laserModules[laser].setPointEdit.text())
        if laser in self.aotfLasers.keys():
            if not self.aotfLasers[laser]:
                self._master.nidaqHelper.setAnalog(laser, magnitude, min_val=0, max_val=5)
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
                    self._master.nidaqHelper.setAnalog(
                        target=laser, voltage=float(self._widget.digModule.powers[laser].text()),
                        min_val=0, max_val=5
                    )
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
                self._master.nidaqHelper.setAnalog(
                    target=laser, voltage=float(self._widget.digModule.powers[laser].text()),
                    min_val=0, max_val=5
                )
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
        self.GlobalDigitalMod([405, 488])


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
            ROIcenter = self._comm_channel.centerROI()

            ROIpos = (ROIcenter[0] - 0.5 * ROIsize[0],
                      ROIcenter[1] - 0.5 * ROIsize[1])

            self._widget.ROI.setPos(ROIpos)
            self._widget.ROI.setSize(ROIsize)
            self._widget.ROI.show()
            self.active = True
            self._widget.roiButton.setText('Hide ROI')

    def addROI(self):
        """ Adds the ROI to ImageWidget viewbox through the CommunicationChannel. """
        self._comm_channel.addItemTovb(self._widget.ROI)

    def run(self):
        if not self.running:
            self.dims = np.array(self._comm_channel.getDimsScan()).astype(int)
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
