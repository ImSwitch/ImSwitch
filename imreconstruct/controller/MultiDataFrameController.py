import os
import psutil

import numpy as np

from imcommon.framework import Timer
from imreconstruct.model.DataObj import DataObj
from .basecontrollers import ImRecWidgetController


class MultiDataFrameController(ImRecWidgetController):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._loadingData = False
        self._dataFolder = None

        self._moduleCommChannel.sigMemoryRecordingAvailable.connect(self.makeAndAddDataObj)
        self._commChannel.sigDataFolderChanged.connect(self.dataFolderChanged)
        self._commChannel.sigCurrentDataChanged.connect(self.currentDataChanged)

        self._widget.sigAddDataClicked.connect(self.addDataClicked)
        self._widget.sigLoadCurrentDataClicked.connect(self.loadCurrData)
        self._widget.sigLoadAllDataClicked.connect(self.loadAllData)
        self._widget.sigUnloadCurrentDataClicked.connect(self.unloadCurrData)
        self._widget.sigUnloadAllDataClicked.connect(self.unloadAllData)
        self._widget.sigSetAsCurrentDataClicked.connect(self.setAsCurrentData)
        self._widget.sigSelectedItemChanged.connect(self.updateInfo)

        self.updateMemBar()
        self._updateMemBarTimer = Timer()
        self._updateMemBarTimer.timeout.connect(self.updateMemBar)
        self._updateMemBarTimer.start(1000)

    def dataFolderChanged(self, dataFolder):
        self._dataFolder = dataFolder

    def currentDataChanged(self):
        if not self._loadingData:
            self._widget.setAllRowsHighlighted(False)

    def makeAndAddDataObj(self, name, path=None, data=None):
        self._widget.addDataObj(DataObj(name, path=path, data=data))
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
            dataObj.checkAndUnloadData()
        self.updateInfo()

    def unloadAllData(self):
        for dataObj in self._widget.getAllDataObjs():
            dataObj.checkAndUnloadData()
        self.updateInfo()

    def delData(self):
        numSelected = np.shape(self.dataList.selectedIndexes())[0]
        while not numSelected == 0:
            ind = self.dataList.selectedIndexes()[0]
            row = ind.row()
            self.dataList.takeItem(row)
            numSelected -= 1

    def delAllData(self):
        for i in range(self.dataList.count()):
            currRow = self.dataList.currentRow()
            self.dataList.takeItem(currRow)

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

    def updateMemBar(self):
        self._widget.updateMemBar(psutil.virtual_memory()[2])
