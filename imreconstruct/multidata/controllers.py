import os
import psutil

import numpy as np

from pyqtgraph.Qt import QtCore, QtGui

from imcommon.controller import Controller
from imreconstruct.core.DataObj import DataObj


class MultiDataFrameController(Controller):
    # Signals
    sigCurrentDataChanged = QtCore.Signal()

    # Methods
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.updateMemBar()
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.updateMemBar)
        self.timer.start(1000)

    def addData(self):
        dlg = QtGui.QFileDialog()

        if hasattr(self, 'data_folder'):
            fileNames = dlg.getOpenFileNames(directory=self.data_folder)[0]
        else:
            fileNames = dlg.getOpenFileNames()[0]

        for i in range(np.shape(fileNames)[0]):
            self.addDataObj(os.path.split(fileNames[i])[1], fileNames[i])

    def addDataObj(self, name, path):
        list_item = QtGui.QListWidgetItem('Data: ' + name)
        list_item.setData(1, DataObj(name, path))
        self.data_list.addItem(list_item)
        self.data_list.setCurrentItem(list_item)
        self.UpdateInfo()

    def loadCurrData(self):
        self.data_list.currentItem().data(1).checkAndLoadData()
        self.UpdateInfo()

    def loadAllData(self):
        for i in range(self.data_list.count()):
            self.data_list.item(i).data(1).checkAndLoadData()
        self.UpdateInfo()

    def delData(self):
        nr_selected = np.shape(self.data_list.selectedIndexes())[0]
        while not nr_selected == 0:
            ind = self.data_list.selectedIndexes()[0]
            row = ind.row()
            removedItem = self.data_list.takeItem(row)
            nr_selected -= 1

    def unloadData(self):
        self.data_list.currentItem().data(1).checkAndUnloadData()
        self.UpdateInfo()

    def delAllData(self):
        for i in range(self.data_list.count()):
            currRow = self.data_list.currentRow()
            removedItem = self.data_list.takeItem(currRow)

    def unloadAllData(self):
        for i in range(self.data_list.count()):
            self.data_list.item(i).data(1).checkAndUnloadData()
        self.UpdateInfo()

    def setCurrentData(self):
        self.sigCurrentDataChanged.emit()
        self.allWhite()
        self.data_list.currentItem().setBackground(QtGui.QColor('green'))
        self.UpdateInfo()

    def UpdateInfo(self):
        if self.data_list.currentItem() is None:
            self.data_loaded_status.setText('')
        else:
            if self.data_list.currentItem().data(1).data_loaded:
                self.data_loaded_status.setText('Yes')
            else:
                self.data_loaded_status.setText('No')

    def allWhite(self):
        for i in range(self.data_list.count()):
            self.data_list.item(i).setBackground(QtGui.QColor('white'))

    def updateMemBar(self):
        self.memBar.setValue(psutil.virtual_memory()[2])
