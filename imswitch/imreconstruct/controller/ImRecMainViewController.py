import copy
import os

import numpy as np
import tifffile as tiff

import imswitch.imreconstruct.view.guitools as guitools
from imswitch.imcommon.controller import PickDatasetsController
from imswitch.imreconstruct.model import DataObj, ReconObj, PatternFinder, SignalExtractor
from .DataFrameController import DataFrameController
from .MultiDataFrameController import MultiDataFrameController
from .WatcherFrameController import WatcherFrameController
from .ReconstructionViewController import ReconstructionViewController
from .ScanParamsController import ScanParamsController
from .basecontrollers import ImRecWidgetController


class ImRecMainViewController(ImRecWidgetController):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._commChannel.extension = self._widget.extension
        
        self.dataFrameController = self._factory.createController(
            DataFrameController, self._widget.dataFrame
        )
        self.multiDataFrameController = self._factory.createController(
            MultiDataFrameController, self._widget.multiDataFrame
        )
        self.watcherFrameController = self._factory.createController(
            WatcherFrameController, self._widget.watcherFrame
        )
        self.reconstructionController = self._factory.createController(
            ReconstructionViewController, self._widget.reconstructionWidget
        )
        self.scanParamsController = self._factory.createController(
            ScanParamsController, self._widget.scanParamsDialog
        )
        self.pickDatasetsController = self._factory.createController(
            PickDatasetsController, self._widget.pickDatasetsDialog
        )

        self._signalExtractor = SignalExtractor()
        self._patternFinder = PatternFinder()

        self._currentDataObj = None
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
        self._commChannel.sigReconstruct.connect(self.reconstruct)


        self._widget.sigSaveReconstruction.connect(lambda: self.saveCurrent('reconstruction'))
        self._widget.sigSaveReconstructionAll.connect(lambda: self.saveAll('reconstruction'))
        self._widget.sigSaveCoeffs.connect(lambda: self.saveCurrent('coefficients'))
        self._widget.sigSaveCoeffsAll.connect(lambda: self.saveAll('coefficients'))
        self._widget.sigSetDataFolder.connect(self.setDataFolder)
        self._widget.sigSetSaveFolder.connect(self.setSaveFolder)

        self._widget.sigReconstuctCurrent.connect(self.reconstructCurrent)
        self._widget.sigReconstructMultiConsolidated.connect(
            lambda: self.reconstructMulti(consolidate=True)
        )
        self._widget.sigReconstructMultiIndividual.connect(
            lambda: self.reconstructMulti(consolidate=False)
        )
        self._widget.sigQuickLoadData.connect(self.quickLoadData)
        self._widget.sigUpdate.connect(lambda: self.updateScanParams(applyOnCurrentRecon=True))

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
        self._logger.debug('Find pattern clicked')
        if self._currentDataObj is None:
            return

        meanData = self._currentDataObj.getMeanData()
        if len(meanData) < 1:
            return

        self._logger.debug('Finding pattern')
        pattern = self._patternFinder.findPattern(meanData)
        self._logger.debug(f'Pattern found as: {self._pattern}')
        self.setPatternParams(pattern)
        self.updatePattern()

    def togglePattern(self, enabled):
        self._logger.debug('Toggling pattern')
        self._commChannel.sigPatternVisibilityChanged.emit(enabled)

    def updatePattern(self):
        if self._settingPatternParams:
            return

        self._logger.debug('Updating pattern')
        self._pattern = self._widget.getPatternParams()
        self._commChannel.sigPatternUpdated.emit(self._pattern)

    def setPatternParams(self, pattern):
        try:
            self._settingPatternParams = True
            self._widget.setPatternParams(*pattern)
        finally:
            self._settingPatternParams = False

    def updateScanParams(self, applyOnCurrentRecon=False):
        self._commChannel.sigScanParamsUpdated.emit(copy.deepcopy(self._scanParDict),
                                                    applyOnCurrentRecon)

    def scanParamsUpdated(self, scanParDict):
        self._scanParDict = scanParDict

    def showScanParamsDialog(self):
        self.updateScanParams()
        self._widget.showScanParamsDialog()

    def quickLoadData(self):
        extension = self._widget.extension.value()
        if extension == 'zarr':
            dataPath = guitools.askForFolderPath(self._widget, defaultFolder=self._dataFolder)
        elif extension == 'hdf5':
            dataPath = guitools.askForFilePath(self._widget, defaultFolder=self._dataFolder)

        if dataPath:
            self._logger.debug(f'Loading data at: {dataPath}')

            datasetsInFile = DataObj.getDatasetNames(dataPath)
            datasetToLoad = None
            if len(datasetsInFile) < 1:
                # File does not contain any datasets
                return
            elif len(datasetsInFile) > 1:
                # File contains multiple datasets
                self.pickDatasetsController.setDatasets(dataPath, datasetsInFile)
                if not self._widget.showPickDatasetsDialog(blocking=True):
                    return

                datasetsSelected = self.pickDatasetsController.getSelectedDatasets()
                if len(datasetsSelected) < 1:
                    # No datasets selected
                    return
                elif len(datasetsSelected) == 1:
                    datasetToLoad = datasetsSelected[0]
                else:
                    # Load into multi-data list
                    for datasetName in datasetsSelected:
                        self._commChannel.sigAddToMultiData.emit(dataPath, datasetName)
                    self._widget.raiseMultiDataDock()
                    return

            name = os.path.split(dataPath)[1]
            if self._currentDataObj is not None:
                self._currentDataObj.checkAndUnloadData()
            self._currentDataObj = DataObj(name, datasetToLoad, path=dataPath)
            self._currentDataObj.checkAndLoadData()
            if self._currentDataObj.dataLoaded:
                self._commChannel.sigCurrentDataChanged.emit(self._currentDataObj)
                self._logger.debug('Data loaded')
                self._widget.raiseCurrentDataDock()
            else:
                pass

    def currentDataChanged(self, dataObj):
        self._currentDataObj = dataObj

        # Update scan params based on new data
        # TODO: What if the attribute names change in imcontrol?
        dimensionMap = {
            b'X': self._widget.r_l_text,
            b'Y': self._widget.u_d_text,
            b'Z': self._widget.b_f_text
        }
        try:
            targetsAttr = dataObj.attrs['ScanStage:target_device']
            for i in range(0, min(3, len(targetsAttr))):
                self._scanParDict['dimensions'][i] = dimensionMap[targetsAttr[i]]
        except KeyError:
            pass

        try:
            positiveDirectionAttr = dataObj.attrs['ScanStage:positive_direction']
            for i in range(0, min(3, len(positiveDirectionAttr))):
                self._scanParDict['directions'][i] = (
                    self._widget.p_text if positiveDirectionAttr[i]
                    else self._widget.n_text
                )
        except KeyError:
            pass

        for i in range(0, 2):
            self._scanParDict['steps'][i] = str(int(np.sqrt(dataObj.numFrames)))

        try:
            stepSizesAttr = dataObj.attrs['ScanStage:axis_step_size']
        except KeyError:
            pass
        else:
            for i in range(0, min(4, len(stepSizesAttr))):
                self._scanParDict['step_sizes'][i] = str(stepSizesAttr[i] * 1000)  # convert um->nm

        self.updateScanParams()

    def extractData(self, data):
        fwhmNm = self._widget.getFwhmNm()
        bgModelling = self._widget.getBgModelling()
        if bgModelling == 'Constant':
            fwhmNm = np.append(fwhmNm, 9999)  # Code for constant bg
        elif bgModelling == 'No background':
            fwhmNm = np.append(fwhmNm, 0)  # Code for zero bg
        elif bgModelling == 'Gaussian':
            self._logger.debug('In Gaussian version')
            fwhmNm = np.append(fwhmNm, self._widget.getBgGaussianSize())
            self._logger.debug('Appended to sigmas')
        else:
            raise ValueError(f'Invalid BG modelling "{bgModelling}" specified; must be either'
                             f' "Constant", "Gaussian" or "No background".')

        sigmas = np.divide(fwhmNm, 2.355 * self._widget.getPixelSizeNm())

        device = self._widget.getComputeDevice()
        pattern = self._pattern
        if device == 'CPU' or device == 'GPU':
            coeffs = self._signalExtractor.extractSignal(data, sigmas, pattern, device.lower())
        else:
            raise ValueError(f'Invalid device "{device}" specified; must be either "CPU" or "GPU"')

        return coeffs

    def reconstructCurrent(self):
        if self._currentDataObj is None:
            return

        self.reconstruct([self._currentDataObj], consolidate=False)

    def reconstructMulti(self, consolidate):
        self.reconstruct(self._widget.getMultiDatas(), consolidate)

    def reconstruct(self, dataObjs, consolidate):
        reconObj = None
        for index, dataObj in enumerate(dataObjs):
            preloaded = dataObj.dataLoaded
            try:
                dataObj.checkAndLoadData()

                if np.prod(np.array(self._scanParDict['steps'], dtype=int)) < dataObj.numFrames:
                    self._logger.error('Too many frames in data')
                    return

                if not consolidate or index == 0:
                    reconObj = ReconObj(dataObj.name,
                                        self._scanParDict,
                                        self._widget.r_l_text,
                                        self._widget.u_d_text,
                                        self._widget.b_f_text,
                                        self._widget.timepoints_text,
                                        self._widget.p_text,
                                        self._widget.n_text)

                data = dataObj.data
                if self._widget.bleachBool.value():
                    data = self.bleachingCorrection(data)

                coeffs = self.extractData(data)
            finally:
                if not preloaded:
                    dataObj.checkAndUnloadData()

            reconObj.addCoeffsTP(coeffs)
            if not consolidate:
                reconObj.updateImages()
                self._widget.addNewData(reconObj, reconObj.name)

        if consolidate and reconObj is not None:
            reconObj.updateImages()
            self._widget.addNewData(reconObj, f'{reconObj.name}_multi')
            self._commChannel.sigExecutionFinished.emit(self.reconstructionController.getImage())

    def bleachingCorrection(self, data):
        correctedData = data.copy()
        energy = np.sum(data, axis=(1, 2))
        for i in range(data.shape[0]):
            c = (energy[0] / energy[i]) ** 4
            correctedData[i, :, :] = data[i, :, :] * c
        return correctedData

    def saveCurrent(self, dataType):
        """ Saves the reconstructed image or coefficeints from the current
        ReconObj to a user-specified destination. """

        filePath = guitools.askForFilePath(self._widget,
                                           caption=f'Save {dataType}',
                                           defaultFolder=self._saveFolder or self._dataFolder,
                                           nameFilter='*.tiff', isSaving=True)

        if filePath:
            reconObj = self.reconstructionController.getActiveReconObj()
            if dataType == 'reconstruction':
                self.saveReconstruction(reconObj, filePath)
            elif dataType == 'coefficients':
                self.saveCoefficients(reconObj, filePath)
            else:
                raise ValueError(f'Invalid save data type "{dataType}"')

    def saveAll(self, dataType):
        """ Saves the reconstructed image or coefficeints from all available
        ReconObj objects to a user-specified directory. """

        dirPath = guitools.askForFolderPath(self._widget,
                                            caption=f'Save all {dataType}',
                                            defaultFolder=self._saveFolder or self._dataFolder)

        if dirPath:
            for name, reconObj in self.reconstructionController.getAllReconObjs():
                # Avoid overwriting
                filePath = os.path.join(dirPath, f'{name}.{dataType}.tiff')
                filePathNew = filePath
                numExisting = 0
                while os.path.exists(filePathNew):
                    numExisting += 1
                    pathWithoutExt, pathExt = os.path.splitext(filePath)
                    filePathNew = f'{pathWithoutExt}_{numExisting}{pathExt}'
                filePath = filePathNew

                # Save
                if dataType == 'reconstruction':
                    self.saveReconstruction(reconObj, filePath)
                elif dataType == 'coefficients':
                    self.saveCoefficients(reconObj, filePath)
                else:
                    raise ValueError(f'Invalid save data type "{dataType}"')

    def saveReconstruction(self, reconObj, filePath):
        scanParDict = reconObj.getScanParams()
        vxsizec = int(float(
            scanParDict['step_sizes'][scanParDict['dimensions'].index(
                self._widget.r_l_text
            )]
        ))
        vxsizer = int(float(
            scanParDict['step_sizes'][scanParDict['dimensions'].index(
                self._widget.u_d_text
            )]
        ))
        vxsizez = int(float(
            reconObj.scanParDict['step_sizes'][scanParDict['dimensions'].index(
                self._widget.b_f_text
            )]
        ))
        dt = int(float(
            scanParDict['step_sizes'][scanParDict['dimensions'].index(
                self._widget.timepoints_text
            )]
        ))

        self._logger.debug(f'Trying to save to: {filePath}, Vx size: {vxsizec, vxsizer, vxsizez},'
                           f' dt: {dt}')
        # Reconstructed image
        reconstrData = copy.deepcopy(reconObj.getReconstruction())
        reconstrData = reconstrData[:, 0, :, :, :, :]
        reconstrData = np.swapaxes(reconstrData, 1, 2)
        tiff.imwrite(filePath, reconstrData,
                     imagej=True, resolution=(1 / vxsizec, 1 / vxsizer),
                     metadata={'spacing': vxsizez, 'unit': 'nm', 'axes': 'TZCYX'})

    def saveCoefficients(self, reconObj, filePath):
        coeffs = copy.deepcopy(reconObj.getCoeffs())
        self._logger.debug(f'Shape of coeffs: {coeffs.shape}')
        coeffs = np.swapaxes(coeffs, 1, 2)
        tiff.imwrite(filePath, coeffs,
                     imagej=True, resolution=(1, 1),
                     metadata={'spacing': 1, 'unit': 'px', 'axes': 'TZCYX'})


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
