import copy
import os

import numpy as np
import tifffile as tiff

import imreconstruct.view.guitools as guitools
from imreconstruct.model import DataObj, ReconObj, PatternFinder, SignalExtractor
from .basecontrollers import ImRecWidgetController
from .DataFrameController import DataFrameController
from .MultiDataFrameController import MultiDataFrameController
from .ReconstructionViewController import ReconstructionViewController
from .ScanParamsController import ScanParamsController


class ImRecMainViewController(ImRecWidgetController):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.dataFrameController = self._factory.createController(DataFrameController, self._widget.dataFrame)
        self.multiDataFrameController = self._factory.createController(MultiDataFrameController, self._widget.multiDataFrame)
        self.reconstructionController = self._factory.createController(ReconstructionViewController, self._widget.reconstructionWidget)
        self.scanParamsController = self._factory.createController(ScanParamsController, self._widget.scanParamsDialog)

        self._signalExtractor = SignalExtractor()
        self._patternFinder = PatternFinder()

        self._currentData = None
        self._pattern = self._widget.getPatternParams()
        self._settingPatternParams = False
        self._scanParDict = {
            'dimensions': [self._widget.r_l_text, self._widget.u_d_text, self._widget.b_f_text,
                           self._widget.timepoints_text],
            'directions': [self._widget.p_text, self._widget.p_text, self._widget.p_text],
            'steps': ['35', '35', '1', '1'],
            'step_sizes': ['35', '35', '35', '1'],
            'unidirectional': True
        }
        self._dataFolder = None
        self._saveFolder = None

        self._commChannel.sigDataFolderChanged.connect(self.dataFolderChanged)
        self._commChannel.sigSaveFolderChanged.connect(self.saveFolderChanged)
        self._commChannel.sigCurrentDataChanged.connect(self.currentDataChanged)
        self._commChannel.sigScanParamsUpdated.connect(self.scanParamsUpdated)

        self._widget.sigSaveReconstruction.connect(lambda: self.saveCurrent('reconstruction'))
        self._widget.sigSaveCoeffs.connect(lambda: self.saveCurrent('coefficients'))
        self._widget.sigSetDataFolder.connect(self.setDataFolder)
        self._widget.sigSetSaveFolder.connect(self.setSaveFolder)

        self._widget.sigReconstuctCurrent.connect(self.reconstructCurrent)
        self._widget.sigReconstructMulti.connect(self.reconstructMulti)
        self._widget.sigQuickLoadData.connect(self.quickLoadData)
        self._widget.sigUpdate.connect(self.updateScanParams)

        self._widget.sigShowPatternChanged.connect(self.togglePattern)
        self._widget.sigFindPattern.connect(self.findPattern)
        self._widget.sigShowScanParamsClicked.connect(self.showScanParamsDialog)
        self._widget.sigPatternParamsChanged.connect(self.updatePattern)

        self.updatePattern()
        self.updateScanParams()

    def dataFolderChanged(self, dataFolder):
        self._dataFolder = dataFolder

    def saveFolderChanged(self, saveFolder):
        self._saveFolder = saveFolder

    def setDataFolder(self):
        dataFolder = guitools.askForFolderPath(self._widget)
        if dataFolder:
            self._commChannel.sigDataFolderChanged.emit(dataFolder)

    def setSaveFolder(self):
        saveFolder = guitools.askForFolderPath(self._widget)
        if saveFolder:
            self._commChannel.sigSaveFolderChanged.emit(saveFolder)

    def findPattern(self):
        print('Find pattern clicked')
        if self._currentData is None:
            return

        meanData = self._currentData.getMeanData()
        if len(meanData) < 1:
            return

        print('Finding pattern')
        pattern = self._patternFinder.findPattern(meanData)
        print('Pattern found as: ', self._pattern)
        self.setPatternParams(pattern)
        self.updatePattern()

    def togglePattern(self, enabled):
        print('Toggling pattern')
        self._commChannel.sigPatternVisibilityChanged.emit(enabled)

    def updatePattern(self):
        if self._settingPatternParams:
            return

        print('Updating pattern')
        self._pattern = self._widget.getPatternParams()
        self._commChannel.sigPatternUpdated.emit(self._pattern)

    def setPatternParams(self, pattern):
        try:
            self._settingPatternParams = True
            self._widget.setPatternParams(*pattern)
        finally:
            self._settingPatternParams = False

    def updateScanParams(self):
        self._commChannel.sigScanParamsUpdated.emit(copy.deepcopy(self._scanParDict))

    def scanParamsUpdated(self, scanParDict):
        self._scanParDict = scanParDict

    def showScanParamsDialog(self):
        self.updateScanParams()
        self._widget.showScanParamsDialog()

    def quickLoadData(self):
        dataPath = guitools.askForFilePath(self._widget, defaultFolder=self._dataFolder)
        if dataPath:
            print(f'Loading data at: {dataPath}')

            name = os.path.split(dataPath)[1]
            if not self._currentData is None:
                self._currentData.checkAndUnloadData()
            self._currentData = DataObj(name, path=dataPath)
            self._currentData.checkAndLoadData()
            if self._currentData.dataLoaded:
                self._commChannel.sigCurrentDataChanged.emit(self._currentData)
                print('Data loaded')
            else:
                pass

    def currentDataChanged(self, dataObj):
        self._currentData = dataObj

        # Update scan params based on new data
        # TODO: What if the attribute names change in imcontrol?
        dimensionMap = {
            b'X': self._widget.r_l_text,
            b'Y': self._widget.u_d_text,
            b'Z': self._widget.b_f_text
        }
        try:
            targetsAttr = dataObj.attrs['ScanStage:Targets[x]']
            for i in range(0, min(3, len(targetsAttr))):
                self._scanParDict['dimensions'][i] = dimensionMap[targetsAttr[i]]
        except KeyError:
            pass

        try:
            positiveDirectionAttr = dataObj.attrs['ScanStage:Positive_direction[x]']
            for i in range(0, min(3, len(positiveDirectionAttr))):
                self._scanParDict['directions'][i] = (self._widget.p_text if positiveDirectionAttr[i]
                                                      else self._widget.n_text)
        except KeyError:
            pass

        for i in range(0, 2):
            self._scanParDict['steps'][i] = str(int(np.sqrt(dataObj.numFrames)))

        try:
            stepSizesAttr = dataObj.attrs['ScanStage:Step_sizes[x]']
        except KeyError:
            pass
        else:
            for i in range(0, min(4, len(stepSizesAttr))):
                self._scanParDict['step_sizes'][i] = str(stepSizesAttr[i])

        self.updateScanParams()

    def extractData(self):
        fwhmNm = self._widget.getFwhmNm()
        bgModelling = self._widget.getBgModelling()
        if bgModelling == 'Constant':
            fwhmNm = np.append(fwhmNm, 9999)  # Code for constant bg
        elif bgModelling == 'No background':
            fwhmNm = np.append(fwhmNm, 0)  # Code for zero bg
        elif bgModelling == 'Gaussian':
            print('In Gaussian version')
            fwhmNm = np.append(fwhmNm, self._widget.getBgGaussianSize())
            print('Appended to sigmas')
        else:
            raise ValueError(f'Invalid BG modelling "{bgModelling}" specified; must be either'
                             f' "Constant", "Gaussian" or "No background".')

        sigmas = np.divide(fwhmNm, 2.355 * self._widget.getPixelSizeNm())

        device = self._widget.getComputeDevice()
        pattern = self._pattern
        if device == 'CPU' or device == 'GPU':
            coeffs = self._signalExtractor.extractSignal(
                self._currentData.data, sigmas, pattern, device.lower()
            )
        else:
            raise ValueError(f'Invalid device "{device}" specified; must be either "CPU" or "GPU"')

        return coeffs

    def reconstructCurrent(self):
        if self._currentData is None:
            return
        elif np.prod(
                np.array(self._scanParDict['steps'], dtype=np.int)) < self._currentData.numFrames:
            print('Too many frames in data')
        else:
            coeffs = self.extractData()
            reconObj = ReconObj(self._currentData.name,
                                self._scanParDict,
                                self._widget.r_l_text,
                                self._widget.u_d_text,
                                self._widget.b_f_text,
                                self._widget.timepoints_text,
                                self._widget.p_text,
                                self._widget.n_text)
            reconObj.addCoeffsTP(coeffs)
            reconObj.updateImages()

            self._widget.addNewData(reconObj)

    def reconstructMulti(self):
        for data in self._widget.getMultiDatas():
            self._currentData = data
            preloaded = self._currentData.dataLoaded
            data.checkAndLoadData()
            coeffs = self.extractData()
            reconObj = ReconObj(data.name,
                                self._scanParDict,
                                self._widget.r_l_text,
                                self._widget.u_d_text,
                                self._widget.b_f_text,
                                self._widget.timepoints_text,
                                self._widget.p_text,
                                self._widget.n_text)
            if not preloaded:
                data.checkAndUnloadData()
            reconObj.addCoeffsTP(coeffs)
            reconObj.updateImages()
            self._widget.addNewData(reconObj)

    def saveCurrent(self, dataType=None):
        """Saves the reconstructed image from self.reconstructor to specified
        destination"""
        if dataType:
            saveName = guitools.askForFilePath(self._widget,
                                               caption='Save File',
                                               defaultFolder=self._saveFolder,
                                               nameFilter='*.tiff', isSaving=True)

            if saveName:
                if dataType == 'reconstruction':
                    reconstructionObj = self.reconstructionController.getActiveReconObj()
                    vxsizec = int(reconstructionObj.scanParDict['step_sizes'][
                                      self._scanParDict['dimensions'].index(self._widget.r_l_text)])
                    vxsizer = int(reconstructionObj.scanParDict['step_sizes'][
                                      self._scanParDict['dimensions'].index(self._widget.u_d_text)])
                    vxsizez = int(reconstructionObj.scanParDict['step_sizes'][
                                      self._scanParDict['dimensions'].index(self._widget.b_f_text)])
                    dt = int(reconstructionObj.scanParDict['step_sizes'][
                                 self._scanParDict['dimensions'].index(self._widget.timepoints_text)])

                    print(f'Trying to save to: {saveName}, Vx size: {vxsizec, vxsizer, vxsizez}')
                    # Reconstructed image
                    reconstrData = copy.deepcopy(reconstructionObj.getReconstruction())
                    reconstrData = reconstrData[:, 0, :, :, :, :]
                    reconstrData.shape = (reconstrData.shape[0], reconstrData.shape[1],
                                          reconstrData.shape[2], reconstrData.shape[3],
                                          reconstrData.shape[4], 1)
                    reconstrData = np.swapaxes(reconstrData, 1, 2)
                    tiff.imwrite(saveName, reconstrData,
                                 imagej=True, resolution=(1 / vxsizec, 1 / vxsizer),
                                 metadata={'spacing': vxsizez, 'unit': 'nm', 'axes': 'TZCYX'})
                elif dataType == 'coefficients':
                    reconstructionObj = self.reconstructionController.getActiveReconObj()
                    coeffs = copy.deepcopy(reconstructionObj.getCoeffs())
                    print('Shape of coeffs = ', coeffs.shape)
                    try:
                        coeffs = np.swapaxes(coeffs, 1, 2)
                        tiff.imwrite(saveName, coeffs,
                                     imagej=True, resolution=(1, 1),
                                     metadata={'spacing': 1, 'unit': 'px', 'axes': 'TZCYX'})
                    except:
                        pass
                else:
                    print('Data type in saveCurrent not recognized')
            else:
                print('No saving path given')
        else:
            print('No data type given in save current')

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