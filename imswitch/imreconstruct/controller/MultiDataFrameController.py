import os

import h5py
import psutil

from imswitch.imcommon.framework import Timer
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

        self._updateMemBarTimer = Timer()
        self._updateMemBarTimer.timeout.connect(self.updateMemBar)
        self._updateMemBarTimer.start(1000)

        self.updateMemBar()
        self.updateInfo()

    def dataFolderChanged(self, dataFolder):
        self._dataFolder = dataFolder

    def currentDataChanged(self):
        if not self._loadingData:
            self._widget.setAllRowsHighlighted(False)

    def memoryDataSet(self, name, dataItem):
        if not isinstance(dataItem.data, h5py.File):
            raise TypeError(f'Data has unsupported type "{type(dataItem.data).__name__}"; should be'
                            f' h5py.File')

        self.makeAndAddDataObj(
            name, path=dataItem.filePath if dataItem.savedToDisk else None, file=dataItem.data
        )

    def memoryDataSavedToDisk(self, name, filePath):
        self._widget.getDataObjByName(name).dataPath = filePath
        self._widget.setDataObjMemoryFlag(name, False)
        self.updateInfo()

    def memoryDataWillRemove(self, name):
        self._widget.getDataObjByName(name).checkAndUnloadData()
        self._widget.delDataByName(name)
        self.updateInfo()

    def makeAndAddDataObj(self, name, path=None, file=None):
        self._widget.addDataObj(name, DataObj(name, path=path, file=file))
        self._widget.setDataObjMemoryFlag(name, path is None)
        self.updateInfo()

    def addDataClicked(self):
        paths = self._widget.requestFilePathsFromUser(self._dataFolder)
        for path in paths:
            self.makeAndAddDataObj(os.path.basename(path), path)

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
            if dataObj.name in self._moduleCommChannel.memoryRecordings:
                del self._moduleCommChannel.memoryRecordings[dataObj.name]
                # No need to call delDataByName, it will be called in memoryDataWillRemove
            else:
                self._widget.delDataByName(dataObj.name)
        self.updateInfo()

    def deleteAllData(self):
        if not self._widget.requestDeleteAllConfirmation():
            return

        self.unloadAllData()
        for dataObj in list(self._widget.getAllDataObjs()):
            if dataObj.name in self._moduleCommChannel.memoryRecordings:
                del self._moduleCommChannel.memoryRecordings[dataObj.name]
                # No need to call delDataByName, it will be called in memoryDataWillRemove
            else:
                self._widget.delDataByName(dataObj.name)
        self.updateInfo()

    def saveCurrData(self):
        for dataObj in self._widget.getSelectedDataObjs():
            if dataObj.dataPath is None:  # Can't save data already on disk
                self._moduleCommChannel.memoryRecordings.saveToDisk(dataObj.name)

    def saveAllData(self):
        for dataObj in self._widget.getAllDataObjs():
            if dataObj.dataPath is None:  # Can't save data already on disk
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

    def updateMemBar(self):
        self._widget.updateMemBar(psutil.virtual_memory()[2])


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
