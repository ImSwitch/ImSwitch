import os
import json

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
        self._widget.applyChangesButton.clicked.connect(self.applyParams)

    # Button pressed functions
    def moveMask(self, direction):
        amount = self._widget.controlPanel.incrementSpinBox.value()
        mask = self._widget.controlPanel.maskComboBox.currentIndex()
        self._master.slmManager.moveMask(mask, direction, amount)
        image = self._master.slmManager.update(maskChange=True, aberChange=True, tiltChange=True)
        self.updateDisplayImage(image)
        # print(f'Move {mask} phase mask {amount} pixels {direction}.')

    def saveParams(self):
        obj = self._widget.controlPanel.objlensComboBox.currentText()
        if obj == 'No objective':
            print('You have to choose an objective from the drop down menu.')
            return
        elif obj == 'Oil':
            filename = 'info_oil.json'
        elif obj == 'Glycerol':
            filename = 'info_glyc.json'
        else:
            raise ValueError(f'Unsupported objective "{obj}"')

        slm_info_dict = self.getInfoDict(self._widget.slmParameterTree.p, self._widget.aberParameterTree.p, self._master.slmManager.getCenters())
        with open(os.path.join(self.slmDir, filename), 'w') as f:
            json.dump(slm_info_dict, f, indent=4)
        print(f'Saved SLM parameters for {obj} objective.')

    def getInfoDict(self, generalParams=None, aberParams=None, centers=None):
        state_general = None
        state_pos = None
        state_aber = None

        if generalParams != None:
            # create dict for general params
            generalparamnames = ["radius", "sigma", "rotationAngle"]
            state_general = {generalparamname: float(generalParams.param("general").param(generalparamname).value()) for generalparamname in generalparamnames}

        if aberParams != None:
            # create dict for aberration params
            masknames = ["left", "right"]
            aberparamnames = ["tilt", "tip", "defocus", "spherical", "verticalComa", "horizontalComa", "verticalAstigmatism", "obliqueAstigmatism"]
            state_aber = dict.fromkeys(masknames)
            for maskname in masknames:
                state_aber[maskname] = {aberparamname: float(aberParams.param(maskname).param(aberparamname).value()) for aberparamname in aberparamnames}

        if centers != None:
            # create dict for position params
            state_pos = dict.fromkeys(masknames)
            for maskname in masknames:
                state_pos[maskname] = {
                                    "xcenter": int(centers[maskname][0]),
                                    "ycenter": int(centers[maskname][1])
                                    }

        info_dict = {
                    "general": state_general,
                    "position": state_pos,
                    "aber": state_aber
                    }
        return info_dict

    def loadParams(self):
        obj = self._widget.controlPanel.objlensComboBox.currentText()
        if obj == 'No objective':
            print('You have to choose an objective from the drop down menu.')
            return
        elif obj == 'Oil':
            filename = 'info_oil.json'
        elif obj == 'Glycerol':
            filename = 'info_glyc.json'
        else:
            raise ValueError(f'Unsupported objective "{obj}"')

        with open(os.path.join(self.slmDir, filename), 'rb') as f:
            slm_info_dict = json.load(f)
            state_general = slm_info_dict["general"]
            state_pos = slm_info_dict["position"]
            state_aber = slm_info_dict["aber"]

        self.setParamTree(state_general=state_general, state_aber=state_aber)
        self._master.slmManager.setGeneral(state_general)
        self._master.slmManager.setCenters(state_pos)
        self._master.slmManager.setAberrations(state_aber)
        self._master.slmManager.saveState(state_general, state_pos, state_aber)
        image = self._master.slmManager.update(maskChange=True, tiltChange=True, aberChange=True)
        self.updateDisplayImage(image)
        # print(f'Loaded SLM parameters for {obj} objective.')

    def setParamTree(self, state_general, state_aber):
        generalParams = self._widget.slmParameterTree.p
        aberParams = self._widget.aberParameterTree.p

        generalparamnames = ["radius", "sigma", "rotationAngle"]
        for generalparamname in generalparamnames:
             generalParams.param("general").param(generalparamname).setValue(float(state_general[generalparamname]))

        masknames = ["left", "right"]
        aberparamnames = ["tilt", "tip", "defocus", "spherical", "verticalComa", "horizontalComa", "verticalAstigmatism", "obliqueAstigmatism"]
        for maskname in masknames:
            for aberparamname in aberparamnames:
                aberParams.param(maskname).param(aberparamname).setValue(float(state_aber[maskname][aberparamname]))

    def setMask(self, maskMode):
        mask = self._widget.controlPanel.maskComboBox.currentIndex()  # 0 = donut (left), 1 = tophat (right)
        self._master.slmManager.setMask(mask, maskMode)
        image = self._master.slmManager.update(maskChange=True)
        self.updateDisplayImage(image)
        # print("Updated image on SLM")

    def applyParams(self):
        slm_info_dict = self.getInfoDict(generalParams=self._widget.slmParameterTree.p, aberParams=self._widget.aberParameterTree.p)
        self.applyGeneral(slm_info_dict["general"])
        self.applyAberrations(slm_info_dict["aber"])
        self._master.slmManager.saveState(state_general=slm_info_dict["general"], state_aber=slm_info_dict["aber"])

    def applyGeneral(self, info_dict):
        self._master.slmManager.setGeneral(info_dict)
        image = self._master.slmManager.update(maskChange=True)
        self.updateDisplayImage(image)
        # print('Apply changes to general slm mask parameters.')

    def applyAberrations(self, info_dict):
        self._master.slmManager.setAberrations(info_dict)
        image = self._master.slmManager.update(aberChange=True)
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
