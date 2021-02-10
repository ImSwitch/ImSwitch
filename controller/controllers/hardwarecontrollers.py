# -*- coding: utf-8 -*-
"""
Created on Sun Mar 22 10:40:53 2020

@author: _Xavi
"""
import numpy as np

from framework import Signal, Thread, Worker
from .basecontrollers import WidgetController


class PositionerController(WidgetController):
    """ Linked to PositionerWidget."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for pName, pManager in self._master.positionersManager:
            self._widget.addPositioner(pName)
            self.setSharedAttr(pName, 'Position', pManager.position)

        # Connect CommunicationChannel signals
        self._commChannel.moveZstage.connect(lambda step: self.move('Z', step))

        # Connect PositionerWidget signals
        self._widget.sigStepUpClicked.connect(
            lambda positionerName: self.move(positionerName, self._widget.getStepSize(positionerName))
        )
        self._widget.sigStepDownClicked.connect(
            lambda positionerName: self.move(positionerName, -self._widget.getStepSize(positionerName))
        )

    def closeEvent(self):
        self._master.positionersManager.execOnAll(lambda p: p.setPosition(0))

    def getPos(self):
        return self._master.positionersManager.execOnAll(lambda p: p.position)

    def move(self, positionerName, dist):
        """ Moves the piezzos in x y or z (axis) by dist micrometers. """
        newPos = self._master.positionersManager[positionerName].move(dist)
        self._widget.updatePosition(positionerName, newPos)
        self.setSharedAttr(positionerName, 'Position', newPos)

    def setSharedAttr(self, positionerName, attr, value):
        self._commChannel.sharedAttrs[('Positioners', positionerName, attr)] = value


class LaserController(WidgetController):
    """ Linked to LaserWidget."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.aotfLasers = {}

        for lName, lManager in self._master.lasersManager:
            self._widget.addLaser(
                lName, lManager.valueUnits, lManager.wavelength,
                (lManager.valueRangeMin, lManager.valueRangeMax) if not lManager.isBinary else None
            )

            if not lManager.isDigital:
                self.aotfLasers[lName] = False
            elif not lManager.isBinary:
                self.valueChanged(lName, lManager.valueRangeMin)

            self.setSharedAttr(lName, 'DigMod', self._widget.isDigModActive())
            self.setSharedAttr(lName, 'Enabled', self._widget.isLaserActive(lName))
            self.setSharedAttr(lName, 'Value',
                               self._widget.getValue(lName) if not self._widget.isDigModActive()
                               else self._widget.getDigValue(lName))

        # Connect LaserWidget signals
        self._widget.sigEnableChanged.connect(self.toggleLaser)
        self._widget.sigValueChanged.connect(self.valueChanged)

        self._widget.sigDigitalModToggled.connect(
            lambda digMod: self.GlobalDigitalMod(
                digMod, [laser.name for _, laser in self._master.lasersManager]
            )
        )
        self._widget.sigDigitalValueChanged.connect(
            lambda laserName: self.updateDigitalPowers([laserName])
        )

    def closeEvent(self):
        self._master.lasersManager.execOnAll(lambda l: l.setDigitalMod(False, 0))
        self._master.lasersManager.execOnAll(lambda l: l.setValue(0))

    def toggleLaser(self, laserName, enabled):
        """ Enable or disable laser (on/off)."""
        self._master.lasersManager[laserName].setEnabled(enabled)
        self.setSharedAttr(laserName, 'Enabled', enabled)

    def valueChanged(self, laserName, magnitude):
        """ Change magnitude. """
        if laserName not in self.aotfLasers.keys() or not self.aotfLasers[laserName]:
            self._master.lasersManager[laserName].setValue(magnitude)
            self._widget.setValue(laserName, magnitude)

        self.setSharedAttr(laserName, 'Value', magnitude)

    def updateDigitalPowers(self, laserNames):
        """ Update the powers if the digital mod is on. """
        if self._widget.isDigModActive():
            for laserName in laserNames:
                value = self._widget.getDigValue(laserName)
                self._master.lasersManager[laserName].setValue(value)
                self.setSharedAttr(laserName, 'Value', value)

    def GlobalDigitalMod(self, digMod, laserNames):
        """ Start/stop digital modulation. """
        for laserName in laserNames:
            laserManager = self._master.lasersManager[laserName]

            if laserManager.isBinary:
                continue

            value = self._widget.getDigValue(laserName)
            if laserManager.isDigital:
                laserManager.setDigitalMod(digMod, value)
            else:
                laserManager.setValue(value)
                self._widget.setLaserActive(laserName, False)
                self._widget.setLaserActivatable(laserName, not digMod)
                self.aotfLasers[laserName] = digMod
                laserManager.setEnabled(False)  # TODO: Correct?
            self._widget.setLaserEditable(laserName, not digMod)

            self.setSharedAttr(laserName, 'DigMod', digMod)
            if not digMod:
                self.valueChanged(laserName, self._widget.getValue(laserName))
            else:
                self.setSharedAttr(laserName, 'Value', value)

    def setSharedAttr(self, laserName, attr, value):
        self._commChannel.sharedAttrs[('Lasers', laserName, attr)] = value


class BeadController(WidgetController):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.running = False
        self.addROI()

        # Connect BeadRecWidget signals
        self._widget.sigROIToggled.connect(self.roiToggled)
        self._widget.sigRunClicked.connect(self.run)

    def roiToggled(self, enabled):
        """ Show or hide ROI."""
        if enabled:
            ROIsize = (64, 64)
            ROIcenter = self._commChannel.getCenterROI()

            ROIpos = (ROIcenter[0] - 0.5 * ROIsize[0],
                      ROIcenter[1] - 0.5 * ROIsize[1])

            self._widget.showROI(ROIpos, ROIsize)
        else:
            self._widget.hideROI()

        self._widget.updateDisplayState(enabled)

    def addROI(self):
        """ Adds the ROI to ImageWidget viewbox through the CommunicationChannel. """
        self._commChannel.addItemTovb.emit(self._widget.getROIGraphicsItem())

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
        self._widget.updateImage(np.resize(self.recIm, self.dims + 1))


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
                roiItem = self.__controller._widget.getROIGraphicsItem()
                pos = roiItem.pos()
                size = roiItem.size()

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
