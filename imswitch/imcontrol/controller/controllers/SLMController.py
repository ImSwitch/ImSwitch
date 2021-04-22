import os
import pickle

import numpy as np

from imswitch.imcommon import constants
from imswitch.imcontrol.model.managers.SLMManager import MaskMode, Direction
from .basecontrollers import ImConWidgetController


class SLMController(ImConWidgetController):
    """Linked to SLMWidget."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.slmDir = os.path.join(constants.rootFolderPath, 'save/slm')
        if not os.path.exists(self.slmDir):
            os.makedirs(self.slmDir)

        self._widget.initControls()
        # self.loadPreset(self._defaultPreset)

        # Connect SLMWidget buttons
        self._widget.controlPanel.upButton.clicked.connect(
            lambda: self.moveMask(Direction.Up))  # change 'up' to (x,y)=(0,1)
        self._widget.controlPanel.downButton.clicked.connect(
            lambda: self.moveMask(Direction.Down))  # change 'down' to (x,y)=(0,-1)
        self._widget.controlPanel.leftButton.clicked.connect(
            lambda: self.moveMask(Direction.Left))  # change 'left' to (x,y)=(-1,0)
        self._widget.controlPanel.rightButton.clicked.connect(
            lambda: self.moveMask(Direction.Right))  # change 'right' to (x,y)=(1,0)

        self._widget.controlPanel.saveButton.clicked.connect(self.saveParams)
        self._widget.controlPanel.loadButton.clicked.connect(self.loadParams)

        self._widget.controlPanel.donutButton.clicked.connect(lambda: self.setMask(MaskMode.Donut))
        self._widget.controlPanel.tophatButton.clicked.connect(
            lambda: self.setMask(MaskMode.Tophat))

        self._widget.controlPanel.blackButton.clicked.connect(lambda: self.setMask(MaskMode.Black))
        self._widget.controlPanel.gaussianButton.clicked.connect(
            lambda: self.setMask(MaskMode.Gauss))

        self._widget.controlPanel.halfButton.clicked.connect(lambda: self.setMask(MaskMode.Half))
        self._widget.controlPanel.quadrantButton.clicked.connect(
            lambda: self.setMask(MaskMode.Quad))
        self._widget.controlPanel.hexButton.clicked.connect(lambda: self.setMask(MaskMode.Hex))
        self._widget.controlPanel.splitbullButton.clicked.connect(
            lambda: self.setMask(MaskMode.Split))

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
        # print(f'Move {mask} phase mask {amount} pixels {direction}.')

    def saveParams(self):
        obj = self._widget.controlPanel.objlensComboBox.currentText()
        general_paramtree = self._widget.slmParameterTree
        aber_paramtree = self._widget.aberParameterTree
        center_coords = self._master.slmManager.getCenters()

        if obj == 'No objective':
            print('You have to choose an objective from the drop down menu.')
            return
        elif obj == 'Oil':
            filename = 'info_oil.slm'
        elif obj == 'Glycerol':
            filename = 'info_glyc.slm'
        else:
            raise ValueError(f'Unsupported objective "{obj}"')

        state_general = general_paramtree.p.saveState()
        state_aber = aber_paramtree.p.saveState()
        state_pos = center_coords
        with open(os.path.join(self.slmDir, filename), 'wb') as f:
            pickler = pickle.Pickler(f)
            pickler.dump(state_general)
            pickler.dump(state_pos)
            pickler.dump(state_aber)
        # print(f'Saved SLM parameters for {obj} objective.')

    def loadParams(self):
        obj = self._widget.controlPanel.objlensComboBox.currentText()
        general_paramtree = self._widget.slmParameterTree
        aber_paramtree = self._widget.aberParameterTree

        if obj == 'No objective':
            print('You have to choose an objective from the drop down menu.')
            return
        elif obj == 'Oil':
            filename = 'info_oil.slm'
        elif obj == 'Glycerol':
            filename = 'info_glyc.slm'
        else:
            raise ValueError(f'Unsupported objective "{obj}"')

        with open(os.path.join(self.slmDir, filename), 'rb') as f:
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
        # print(f'Loaded SLM parameters for {obj} objective.')

    def setMask(self, maskMode):
        mask = self._widget.controlPanel.maskComboBox.currentIndex()  # 0 = donut (left), 1 = tophat (right)
        angle = np.float(self._widget.controlPanel.rotationEdit.text())
        sigma = np.float(
            self._widget.slmParameterTree.p.param('General parameters').param('Sigma').value())
        self._master.slmManager.setMask(mask, angle, sigma, maskMode)
        image = self._master.slmManager.update()
        self.updateDisplayImage(image)
        # print("Updated image on SLM")

    def applyGeneral(self):
        self._master.slmManager.setGeneral(self._widget.slmParameterTree)
        image = self._master.slmManager.update()
        self.updateDisplayImage(image)
        # print('Apply changes to general slm mask parameters.')

    def applyAberrations(self):
        self._master.slmManager.setAberrations(self._widget.aberParameterTree)
        image = self._master.slmManager.update()
        self.updateDisplayImage(image)
        # print('Apply changes to aberration correction masks.')

    def updateDisplayImage(self, image):
        image = np.fliplr(image.transpose())
        self._widget.img.setImage(image, autoLevels=True, autoDownsample=False)
        # print("Updated displayed image")

    # def loadPreset(self, preset):
    #    print('Loaded default SLM settings.')


# Copyright (C) 2020, 2021 TestaLab
# This file is part of ImSwitch.
#
# ImSwitch is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# ImSwitch is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
