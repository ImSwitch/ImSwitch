import json
import os

import numpy as np
from pathlib import Path
from imswitch.imcommon.model import dirtools, initLogger
from imswitch.imcontrol.model.managers.SLMmlManager import MaskMode, Direction
from ..basecontrollers import ImConWidgetController
from imswitch.imcontrol.view import guitools
from imswitch.imcommon.model import APIExport
import imswitch.imcontrol.controller.Generation_Hologramme.parameters as parameters
import imswitch.imcontrol.controller.Generation_Hologramme.main as main_holo

class SLMmlController(ImConWidgetController):
    """Linked to SLMWidget."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__logger = initLogger(self)
        
        """if slm_info is None:
            return

        self.__slmInfo = slm_info
        self.__serial_number = self.__slmInfo.serial_number
        self.__pixelsize = self.__slmInfo.pixelSize
        self.__slmSize = (self.__slmInfo.width, self.__slmInfo.height)"""

        self.slmDir = os.path.join(dirtools.UserFileDirs.Root, r'imcontrol_slm')
        parameters.file_path = os.path.join(self.slmDir,"MFA")

        if not os.path.exists(self.slmDir):
            os.makedirs(self.slmDir)

        if self._setupInfo.slm is None:
            self._widget.replaceWithError('SLM is not configured in your setup file.')
            return

        self._widget.initSLMDisplay(self._setupInfo.slm.monitorIdx)

        # Connect CommunicationChannel signals
        self._commChannel.sigSLMMaskUpdated.connect(lambda mask: self.displayMask(mask))

        # Connect SLMWidget signals
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

        self._widget.applyChangesButton.clicked.connect(self.applyParams)
        self._widget.sigSLMDisplayToggled.connect(self.toggleSLMDisplay)
        self._widget.sigSLMMonitorChanged.connect(self.monitorChanged)
        
        #MFA specific
        self._widget.loadMFABtn.clicked.connect(self.loadMFA)
        self._widget.create_and_loadMFABtn.clicked.connect(self.create_and_loadMFA)
        self._widget.sigSLMApplyMFA.connect(self.updateApplyMFA)

        # Initial SLM display
        self.displayMask(self._master.slmManager.maskCombined)



    def updateApplyMFA(self,state:bool):
        self._master.slmManager.applyMFA = state


    def loadMFA(self):
        path = guitools.askForFilePath(self._widget, 'Choose MFA hologram BMP image',defaultFolder=self.slmDir)
        self._widget.updateMLAlabel(Path(path).name)
        self._master.slmManager.updateMFApath(path)
        
        
    def create_and_loadMFA(self):
        
        #MODIFIE
        state = self.getInfoDict(mfaParams=self._widget.mfaParameterTree.p)["mfa"]
        parameters.n = int(state["n"])
        parameters.N = int(state["N"])
        parameters.period_grid = int(state["period_grid"])
        parameters.file_name = state["file_name"]
        
        main_holo.hologramCreationMFA()
        
        print("parameters.n =", state["n"], "   ;parameters.N =", state["N"],"    ;parameters.period_grid =", state["period_grid"])
        
        path = os.path.join(parameters.file_path, parameters.file_name+'.bmp')
        #path = guitools.askForFilePath(self._widget, 'Choose MFA hologram BMP image',defaultFolder=self.slmDir)
        self._widget.updateMLAlabel(Path(path).name)
        self._master.slmManager.updateMFApath(path)

    @APIExport(runOnUIThread=True)
    def toggleSLMDisplay(self, enabled):
        self._widget.setSLMDisplayVisible(enabled)

    def monitorChanged(self, monitor):
        self._widget.setSLMDisplayMonitor(monitor)

    def displayMask(self, maskCombined):
        """ Display the mask in the SLM display. Originates from slmPy:
        https://github.com/wavefrontshaping/slmPy """

        arr = maskCombined.image()

        # Padding: Like they do in the software
        pad = np.zeros((1024, 8), dtype=np.uint8)
        arr = np.append(arr, pad, 1)

        # Create final image array
        h, w = arr.shape[0], arr.shape[1]

        if len(arr.shape) == 2:
            # Array is grayscale
            arrGray = arr.copy()
            arrGray.shape = h, w, 1
            img = np.concatenate((arrGray, arrGray, arrGray), axis=2)
        else:
            img = arr

        self._widget.updateSLMDisplay(img)

    # Button pressed functions
    def moveMask(self, direction):
        print(f'Exec: {self.moveMask.__qualname__}')
        amount = self._widget.controlPanel.incrementSpinBox.value()
        self._master.slmManager.moveMask(direction, amount)
        image = self._master.slmManager.update(maskChange=True, aberChange=True, tiltChange=True, focalChange=True)
        self.updateDisplayImage(image)

    def saveParams(self):
        obj = self._widget.controlPanel.objlensComboBox.currentText()
        if obj == 'No objective':
            self.__logger.error('You have to choose an objective from the drop down menu.')
            return
        elif obj == 'Oil':
            filename = 'info_oil.json'
        elif obj == 'Glycerol':
            filename = 'info_glyc.json'
        else:
            raise ValueError(f'Unsupported objective "{obj}"')

        slm_info_dict = self.getInfoDict(self._widget.slmParameterTree.p,
                                         self._widget.aberParameterTree.p,
                                         self._widget.mfaParameterTree.p,      #MODIFIE
                                         self._master.slmManager.getCenter())
        print(os.path.join(self.slmDir, filename))
        with open(os.path.join(self.slmDir, filename), 'w') as f:
            json.dump(slm_info_dict, f, indent=4)
        self.__logger.info(f'Saved SLM parameters for {obj} objective.')

    def getInfoDict(self, generalParams=None, aberParams=None, mfaParams=None, center=None):        #MODIFIE
        state_general = None
        state_pos = None
        state_aber = None
        state_mfa = None

        if generalParams is not None:
            # create dict for general params
            generalparamnames = ["radius", "focal", "sigma", "rotationAngle", "tiltAngle"]
            state_general = {generalparamname: float(
                generalParams.param("general").param(generalparamname).value()) for generalparamname
                             in generalparamnames}

        if aberParams is not None:
            # create dict for aberration params
            maskname = "mask"
            aberparamnames = ["tilt", "tip", "defocus", "spherical", "verticalComa",
                              "horizontalComa", "verticalAstigmatism", "obliqueAstigmatism"]
            state_aber = dict.fromkeys([maskname])
            state_aber[maskname] = {
                aberparamname: float(aberParams.param(maskname).param(aberparamname).value())
                for aberparamname in aberparamnames}
            
        if mfaParams is not None:                   #MODIFIE
            # create dict for general params
            mfavarnames ={"n number of focal point (n*n)":"n","N size of the target images (number of pixels N*N)":"N","period in pixels":"period_grid","file name of the generated hologram":"file_name"}
            mfaparamnames = ["n number of focal point (n*n)", "N size of the target images (number of pixels N*N)", "period in pixels","file name of the generated hologram"]
            state_mfa = {mfavarnames[mfaparamname]: 
                mfaParams.param("MFA").param(mfaparamname).value() for mfaparamname
                             in mfaparamnames}

        if center is not None:
            # create dict for position params
            state_pos = dict.fromkeys([maskname])
            state_pos[maskname] = {
                "xcenter": int(center[maskname][0]),
                "ycenter": int(center[maskname][1])
            }

        info_dict = {
            "general": state_general,
            "position": state_pos,
            "aber": state_aber,
            "mfa" : state_mfa                                    #MODIFIE
        }
        return info_dict

    def loadParams(self):
        obj = self._widget.controlPanel.objlensComboBox.currentText()
        if obj == 'No objective':
            self.__logger.error('You have to choose an objective from the drop down menu.')
            return
        elif obj == 'Oil':
            filename = 'info_oil.json'
        elif obj == 'Glycerol':
            filename = 'info_glyc.json'
        else:
            raise ValueError(f'Unsupported objective "{obj}"')

        with open(os.path.join(self.slmDir, filename), 'rb') as f:
            print(os.path.join(self.slmDir, filename))
            slm_info_dict = json.load(f)
            state_general = slm_info_dict["general"]
            state_pos = slm_info_dict["position"]
            state_aber = slm_info_dict["aber"]

        self.setParamTree(state_general=state_general, state_aber=state_aber, state_mfa=None)
        self._master.slmManager.setGeneral(state_general)
        self._master.slmManager.setCenter(state_pos)
        self._master.slmManager.setAberrationFactors(state_aber)
        self._master.slmManager.saveState(state_general, state_pos, state_aber)
        image = self._master.slmManager.update(maskChange=True, tiltChange=True, aberChange=True, focalChange=True)
        self.updateDisplayImage(image)

    def setParamTree(self, state_general, state_aber, state_mfa):
        generalParams = self._widget.slmParameterTree.p
        aberParams = self._widget.aberParameterTree.p
        mfaParams = self._widget.mfaParameterTree.p

        generalparamnames = ["radius", "focal", "sigma", "rotationAngle", "tiltAngle"]
        for generalparamname in generalparamnames:
            generalParams.param("general").param(generalparamname).setValue(
                float(state_general[generalparamname])
            )
        
        if state_mfa is not None:
            mfaparamnames = ["n number of focal point (n*n)", "N size of the target images (number of pixels N*N)", "period in pixels","file name of the generated hologram"]
            for mfaparamname in mfaparamnames:
                mfaParams.param("MFA").param(mfaparamname).setValue(
                    float(state_mfa[mfaparamname])
                )
            
        maskname = "mask"
        aberparamnames = ["tilt", "tip", "defocus", "spherical", "verticalComa", "horizontalComa",
                          "verticalAstigmatism", "obliqueAstigmatism"]
        for aberparamname in aberparamnames:
            aberParams.param(maskname).param(aberparamname).setValue(
                float(state_aber[maskname][aberparamname])
            )

    @APIExport(runOnUIThread=True)
    def setMask(self, maskMode):
        if maskMode != MaskMode.Black:
            slm_info_dict = self.getInfoDict(generalParams=self._widget.slmParameterTree.p,
                                            aberParams=self._widget.aberParameterTree.p)
            self.applyAberrations(slm_info_dict["aber"])
        self._master.slmManager.setMask(maskMode)
        image = self._master.slmManager.update(maskChange=True, tiltChange=True, aberChange=True, focalChange=True)
        self.updateDisplayImage(image)

    def applyParams(self):
        slm_info_dict = self.getInfoDict(generalParams=self._widget.slmParameterTree.p,
                                         aberParams=self._widget.aberParameterTree.p)
        self.applyGeneral(slm_info_dict["general"])
        self.applyAberrations(slm_info_dict["aber"])
        image = self._master.slmManager.update(maskChange=True, tiltChange=True, aberChange=True, focalChange=True)
        self.updateDisplayImage(image)
        self._master.slmManager.saveState(state_general=slm_info_dict["general"],
                                          state_aber=slm_info_dict["aber"])

    def applyGeneral(self, info_dict):
        self._master.slmManager.setGeneral(info_dict)

    def applyAberrations(self, info_dict):
        self._master.slmManager.setAberrations(info_dict)

    def updateDisplayImage(self, image):
        image = np.fliplr(image.transpose())
        self._widget.img.setImage(image, autoLevels=True, autoDownsample=False)


# Copyright (C) 2020-2021 ImSwitch developers
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
