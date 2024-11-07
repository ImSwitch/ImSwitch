import os

import h5py

from imswitch.imreconstruct.model import DataObj
from .basecontrollers import ImRecWidgetController


class MultiDataFrameController(ImRecWidgetController):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._loadingData = False
        self._dataFolder = None

        self._moduleCommChannel.memoryRecordings.sigDataSet.connect(self.memoryDataSet)
        self._moduleCommChannel.memoryRecordings.sigDataSavedToDisk.connect(
            self.memoryDataSavedToDisk
        )
        self._moduleCommChannel.memoryRecordings.sigDataWillRemove.connect(
            self.memoryDataWillRemove
        )
        self._commChannel.sigDataFolderChanged.connect(self.dataFolderChanged)
        self._commChannel.sigCurrentDataChanged.connect(self.currentDataChanged)
        self._commChannel.sigAddToMultiData.connect(
            lambda path, datasetName: self.makeAndAddDataObj(os.path.basename(path), datasetName,
                                                             path=path)
        )

        self._widget.sigAddDataClicked.connect(self.addDataClicked)
        self._widget.sigLoadCurrentDataClicked.connect(self.loadCurrData)
        self._widget.sigLoadAllDataClicked.connect(self.loadAllData)
        self._widget.sigUnloadCurrentDataClicked.connect(self.unloadCurrData)
        self._widget.sigUnloadAllDataClicked.connect(self.unloadAllData)
        self._widget.sigDeleteCurrentDataClicked.connect(self.deleteCurrData)
        self._widget.sigDeleteAllDataClicked.connect(self.deleteAllData)
        self._widget.sigSetAsCurrentDataClicked.connect(self.setAsCurrentData)
        self._widget.sigSaveCurrentDataClicked.connect(self.saveCurrData)
        self._widget.sigSaveAllDataClicked.connect(self.saveAllData)
        self._widget.sigSelectedItemChanged.connect(self.updateInfo)

        self.updateInfo()

    def dataFolderChanged(self, dataFolder):
        self._dataFolder = dataFolder

    def currentDataChanged(self):
        if not self._loadingData:
            self._widget.setAllRowsHighlighted(False)

    def memoryDataSet(self, name, vFileItem):
        data = vFileItem.data
        if not isinstance(data, h5py.File):
            data = h5py.File(data)

        for datasetName in data.keys():
            self.makeAndAddDataObj(
                name, datasetName, path=vFileItem.filePath if vFileItem.savedToDisk else None,
                file=data
            )

    def memoryDataSavedToDisk(self, name, filePath):
        for dataObj in self.getDataObjsByMemRecordingName(name):
            dataObj.dataPath = filePath
            self._widget.setDataObjMemoryFlag(dataObj, False)
        self.updateInfo()

    def memoryDataWillRemove(self, name):
        for dataObj in self.getDataObjsByMemRecordingName(name):
            dataObj.checkAndUnloadData()
            self._widget.delDataByDataObj(dataObj)
        self.updateInfo()

    def getDataObjsByMemRecordingName(self, name):
        for dataObj in self._widget.getAllDataObjs():
            try:
                expectedFilename = str(self._moduleCommChannel.memoryRecordings[name].data)
            except KeyError:
                pass
            else:
                if dataObj._file is not None and dataObj._file.filename == expectedFilename:
                    yield dataObj

    def makeAndAddDataObj(self, name, datasetName, path=None, file=None):
        dataObj = DataObj(name, datasetName, path=path, file=file)
        for existingDataObj in self._widget.getAllDataObjs():
            if dataObj.describesSameAs(existingDataObj):
                return  # Already added

        self._widget.addDataObj(name, datasetName, dataObj)
        self._widget.setDataObjMemoryFlag(dataObj, path is None)
        self.updateInfo()

    def addDataClicked(self):
        paths = self._widget.requestFilePathsFromUser(self._dataFolder)
        for path in paths:
            datasetsInFile = DataObj.getDatasetNames(path)
            for datasetName in datasetsInFile:
                self.makeAndAddDataObj(os.path.basename(path), datasetName, path=path)

    def loadCurrData(self):
        for dataObj in self._widget.getSelectedDataObjs():
            dataObj.checkAndLoadData()
        self.updateInfo()

    def loadAllData(self):
        for dataObj in self._widget.getAllDataObjs():
            dataObj.checkAndLoadData()
        self.updateInfo()

    def unloadCurrData(self):
        for dataObj in self._widget.getSelectedDataObjs():
            if dataObj.dataPath is not None:  # Don't allow unloading RAM-only data
                dataObj.checkAndUnloadData()
        self.updateInfo()

    def unloadAllData(self):
        for dataObj in self._widget.getAllDataObjs():
            if dataObj.dataPath is not None:  # Don't allow unloading RAM-only data
                dataObj.checkAndUnloadData()
        self.updateInfo()

    def deleteCurrData(self):
        if not self._widget.requestDeleteSelectedConfirmation():
            return

        self.unloadCurrData()
        for dataObj in list(self._widget.getSelectedDataObjs()):
            self.deleteDataObj(dataObj)
        self.updateInfo()

    def deleteAllData(self):
        if not self._widget.requestDeleteAllConfirmation():
            return

        self.unloadAllData()
        for dataObj in list(self._widget.getAllDataObjs()):
            self.deleteDataObj(dataObj)
        self.updateInfo()

    def deleteDataObj(self, dataObj):
        if len(list(self.getDataObjsByMemRecordingName(dataObj.name))) == 1:
            del self._moduleCommChannel.memoryRecordings[dataObj.name]
            # No need to call delDataByDataObj, it will be called in memoryDataWillRemove
        else:
            self._widget.delDataByDataObj(dataObj)

    def saveCurrData(self):
        for dataObj in self._widget.getSelectedDataObjs():
            self.saveDataObj(dataObj)

    def saveAllData(self):
        for dataObj in self._widget.getAllDataObjs():
            self.saveDataObj(dataObj)

    def saveDataObj(self, dataObj):
        if dataObj.dataPath is not None:
            return  # Can't save data already on disk

        if (os.path.exists(self._moduleCommChannel.memoryRecordings.getSavePath(dataObj.name)) and
                not self._widget.requestOverwriteConfirmation(dataObj.name)):
            return  # File exists, user does not wish to overwrite

        self._moduleCommChannel.memoryRecordings.saveToDisk(dataObj.name)

    def setAsCurrentData(self):
        try:
            self._loadingData = True
            selectedDataObj = self._widget.getSelectedDataObj()
            selectedDataObj.checkAndLoadData()
            self._commChannel.sigCurrentDataChanged.emit(selectedDataObj)

            self._widget.setAllRowsHighlighted(False)
            self._widget.setCurrentRowHighlighted(True)
            self.updateInfo()
        finally:
            self._loadingData = False

    def updateInfo(self):
        selectedDataObj = self._widget.getSelectedDataObj()
        if selectedDataObj is None:
            self._widget.setLoadedStatusText('')
        else:
            if selectedDataObj.dataLoaded:
                self._widget.setLoadedStatusText('Yes')
            else:
                self._widget.setLoadedStatusText('No')

        self._widget.setLoadButtonEnabled(
            selectedDataObj is not None and not selectedDataObj.dataLoaded
        )
        self._widget.setUnloadButtonEnabled(
            selectedDataObj is not None and selectedDataObj.dataLoaded
            and selectedDataObj.dataPath is not None
        )
        self._widget.setSaveButtonEnabled(
            selectedDataObj is not None and selectedDataObj.dataPath is None
        )
        self._widget.setDeleteButtonEnabled(selectedDataObj is not None)
        self._widget.setSetCurrentButtonEnabled(selectedDataObj is not None)

        allDataObjs = list(self._widget.getAllDataObjs())
        self._widget.setLoadAllButtonEnabled(
            len(allDataObjs) > 0 and any([not obj.dataLoaded for obj in allDataObjs])
        )
        self._widget.setUnloadAllButtonEnabled(
            len(allDataObjs) > 0 and any([obj.dataLoaded and obj.dataPath is not None
                                          for obj in allDataObjs])
        )
        self._widget.setSaveAllButtonEnabled(
            len(allDataObjs) > 0 and any([obj.dataLoaded and obj.dataPath is None
                                          for obj in allDataObjs])
        )
        self._widget.setDeleteAllButtonEnabled(len(allDataObjs) > 0)


# Copyright (C) 2020-2023 ImSwitch developers
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
