# -*- coding: utf-8 -*-
"""
Created on Sun Mar 22 10:40:53 2020

@author: _Xavi
"""

import pickle
import time
import threading
import textwrap

import numpy as np

from framework import Signal, Thread, Worker
from .basecontrollers import WidgetController
from model.managers.SLMManager import MaskMode, Direction, MaskChoice
from skimage.feature import peak_local_max
import pyqtgraph.ptime as ptime
import scipy.ndimage as ndi


class SLMController(WidgetController):
    """Linked to SLMWidget."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._widget.initControls()
        #self.loadPreset(self._defaultPreset)

        # Connect SLMWidget buttons
        self._widget.controlPanel.upButton.clicked.connect(lambda: self.moveMask(Direction.Up))  # change 'up' to (x,y)=(0,1)
        self._widget.controlPanel.downButton.clicked.connect(lambda: self.moveMask(Direction.Down))  # change 'down' to (x,y)=(0,-1)
        self._widget.controlPanel.leftButton.clicked.connect(lambda: self.moveMask(Direction.Left))  # change 'left' to (x,y)=(-1,0)
        self._widget.controlPanel.rightButton.clicked.connect(lambda: self.moveMask(Direction.Right))  # change 'right' to (x,y)=(1,0)

        self._widget.controlPanel.saveButton.clicked.connect(self.saveParams)
        self._widget.controlPanel.loadButton.clicked.connect(self.loadParams)

        self._widget.controlPanel.donutButton.clicked.connect(lambda: self.setMask(MaskMode.Donut))
        self._widget.controlPanel.tophatButton.clicked.connect(lambda: self.setMask(MaskMode.Tophat))

        self._widget.controlPanel.blackButton.clicked.connect(lambda: self.setMask(MaskMode.Black))
        self._widget.controlPanel.gaussianButton.clicked.connect(lambda: self.setMask(MaskMode.Gauss))
        
        self._widget.controlPanel.halfButton.clicked.connect(lambda: self.setMask(MaskMode.Half))
        self._widget.controlPanel.quadrantButton.clicked.connect(lambda: self.setMask(MaskMode.Quad))
        self._widget.controlPanel.hexButton.clicked.connect(lambda: self.setMask(MaskMode.Hex))
        self._widget.controlPanel.splitbullButton.clicked.connect(lambda: self.setMask(MaskMode.Split))

        # Connect SLMWidget parameter tree updates
        self.applySlmParam = self._widget.slmParameterTree.p.param('Apply')
        self.applySlmParam.sigStateChanged.connect(self.applyGeneral)
        self.applyAberParam = self._widget.aberParameterTree.p.param('Apply')
        self.applyAberParam.sigStateChanged.connect(self.applyAberrations)

    # Button pressed functions
    def moveMask(self, direction):
        amount = self._widget.controlPanel.incrementSpinBox.value()
        mask = self._widget.controlPanel.maskComboBox.currentIndex()
        self._master.slmManager.moveMask(mask, direction, amount)
        image = self._master.slmManager.update()
        self.updateDisplayImage(image)
        #print(f'Move {mask} phase mask {amount} pixels {direction}.')

    def saveParams(self):
        obj = self._widget.controlPanel.objlensComboBox.currentText()
        general_paramtree = self._widget.slmParameterTree
        aber_paramtree = self._widget.aberParameterTree
        center_coords = self._master.slmManager.getCenters()

        if(obj=='No objective'):
            print('You have to choose an objective from the drop down menu.')
            return
        else:
            if(obj=='Oil'):
                filename = 'info_oil.slm'
            elif(obj=='Glycerol'):
                filename = 'info_glyc.slm'
        state_general = general_paramtree.p.saveState()
        state_aber = aber_paramtree.p.saveState()
        state_pos = center_coords
        with open(filename, 'wb') as f:
            pickler = pickle.Pickler(f)
            pickler.dump(state_general)
            pickler.dump(state_pos)
            pickler.dump(state_aber)
        #print(f'Saved SLM parameters for {obj} objective.')

    def loadParams(self):
        obj = self._widget.controlPanel.objlensComboBox.currentText()
        general_paramtree = self._widget.slmParameterTree
        aber_paramtree = self._widget.aberParameterTree

        if(obj=='No objective'):
            print('You have to choose an objective from the drop down menu.')
            return
        else:
            if(obj=='Oil'):
                filename = 'info_oil.slm'
            elif(obj=='Glycerol'):
                filename = 'info_glyc.slm'
        with open(filename, 'rb') as f:
            unpickler = pickle.Unpickler(f)
            state_general = unpickler.load()
            state_pos = unpickler.load()
            state_aber = unpickler.load()
        
        self._widget.slmParameterTree.p.restoreState(state_general)
        self._widget.aberParameterTree.p.restoreState(state_aber)
        self._master.slmManager.setCenters(state_pos)
        self._master.slmManager.setAberrations(self._widget.aberParameterTree)
        self._master.slmManager.setGeneral(self._widget.slmParameterTree)
        image = self._master.slmManager.update()
        self.updateDisplayImage(image)
        #print(f'Loaded SLM parameters for {obj} objective.')

    def setMask(self, maskMode):
        mask = self._widget.controlPanel.maskComboBox.currentIndex()  # 0 = donut (left), 1 = tophat (right)
        angle = np.float(self._widget.controlPanel.rotationEdit.text())
        sigma = np.float(self._widget.slmParameterTree.p.param('General parameters').param('Sigma').value())
        self._master.slmManager.setMask(mask, angle, sigma, maskMode)
        image = self._master.slmManager.update()
        self.updateDisplayImage(image)
        #print("Updated image on SLM")

    def applyGeneral(self):
        self._master.slmManager.setGeneral(self._widget.slmParameterTree)
        image = self._master.slmManager.update()
        self.updateDisplayImage(image)
        #print('Apply changes to general slm mask parameters.')
        
    def applyAberrations(self):
        self._master.slmManager.setAberrations(self._widget.aberParameterTree)
        image = self._master.slmManager.update()
        self.updateDisplayImage(image)
        #print('Apply changes to aberration correction masks.')

    def updateDisplayImage(self, image):
        image = np.fliplr(image.transpose())
        self._widget.img.setImage(image, autoLevels=True, autoDownsample=False)
        #print("Updated displayed image")

    #def loadPreset(self, preset):
    #    print('Loaded default SLM settings.')


class PositionerController(WidgetController):
    """ Linked to PositionerWidget."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._widget.initControls(self._setupInfo.positioners)

        # Connect CommunicationChannel signals
        self._commChannel.moveZstage.connect(lambda step: self.move('Z', step))

        # Connect PositionerWidget signals
        for positionerName in self._setupInfo.positioners.keys():
            axes = self._setupInfo.positioners[positionerName].managerProperties['axisCount']
            axislabels = textwrap.wrap(self._setupInfo.positioners[positionerName].managerProperties['axisLabels'],1)
            for i in range(axes):
                self._widget.pars['UpButton' + positionerName + axislabels[i]].pressed.connect(
                    lambda positionerName=positionerName, axislabel=axislabels[i], i=i: self.move(
                        positionerName,
                        float(self._widget.pars['StepEdit' + positionerName + axislabel].text()),
                        i
                    )
                )
                self._widget.pars['DownButton' + positionerName + axislabels[i]].pressed.connect(
                    lambda positionerName=positionerName, axislabel=axislabels[i], i=i: self.move(
                        positionerName,
                        -float(self._widget.pars['StepEdit' + positionerName + axislabel].text()),
                        i
                    )
                )

    def move(self, positioner, dist, axis):
        """ Moves the piezzos in x y or z (axis) by dist micrometers. """
        newPos = self._master.positionersManager[positioner].move(dist, axis)
        newText = "<strong>{0:.2f} µm</strong>".format(newPos)
        axislabels = textwrap.wrap(self._setupInfo.positioners[positioner].managerProperties['axisLabels'],1)
        self._widget.pars['Position' + positioner + axislabels[axis]].setText(newText)

    def getPos(self):
        return self._master.positionersManager.execOnAll(lambda p: p.position)

    def closeEvent(self):
        self._master.positionersManager.execOnAll(lambda p: p.setPosition(0))


class LaserController(WidgetController):
    """ Linked to LaserWidget."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
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
