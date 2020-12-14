import os
import psutil

import numpy as np

from pyqtgraph.Qt import QtCore, QtGui, QtWidgets

from imreconstruct.core.DataObj import DataObj


class MultiDataFrame(QtGui.QFrame):
    # Signals
    sigCurrentDataChanged = QtCore.Signal()

    # Methods
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.data_list = QtGui.QListWidget()
        self.data_list.currentItemChanged.connect(self.UpdateInfo)
        self.data_list.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)

        data_loaded_label = QtGui.QLabel('Data loaded')
        data_loaded_label.setAlignment(QtCore.Qt.AlignTop)
        self.data_loaded_status = QtGui.QLabel()
        self.data_loaded_status.setAlignment(QtCore.Qt.AlignTop)

        setDataBtn = QtGui.QPushButton('Set as current data')
        setDataBtn.clicked.connect(self.setCurrentData)
        addDataBtn = QtGui.QPushButton('Add data')
        addDataBtn.clicked.connect(self.addData)
        loadCurrDataBtn = QtGui.QPushButton('Load chosen data')
        loadCurrDataBtn.clicked.connect(self.loadCurrData)
        loadAllDataBtn = QtGui.QPushButton('Load all data')
        loadAllDataBtn.clicked.connect(self.loadAllData)

        delDataBtn = QtGui.QPushButton('Delete')
        delDataBtn.clicked.connect(self.delData)
        unloadDataBtn = QtGui.QPushButton('Unload')
        unloadDataBtn.clicked.connect(self.unloadData)
        delAllDataBtn = QtGui.QPushButton('Delete all')
        delAllDataBtn.clicked.connect(self.delAllData)
        unloadAllDataBtn = QtGui.QPushButton('Unload all')
        unloadAllDataBtn.clicked.connect(self.unloadAllData)

        RAMusageLabel = QtWidgets.QLabel('Current RAM usage')

        self.memBar = QtGui.QProgressBar(self)
        self.memBar.setMaximum(100) #Percentage
        self.updateMemBar()

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.updateMemBar)
        self.timer.start(1000)

        # Set layout
        layout = QtGui.QGridLayout()
        self.setLayout(layout)

        layout.addWidget(self.data_list, 0, 0, 4, 1)
        layout.addWidget(data_loaded_label, 0, 1)
        layout.addWidget(self.data_loaded_status, 0, 2)
        layout.addWidget(addDataBtn, 1, 1)
        layout.addWidget(loadCurrDataBtn, 2, 1)
        layout.addWidget(loadAllDataBtn, 3, 1)
        layout.addWidget(setDataBtn, 4, 1)
        layout.addWidget(delDataBtn, 1, 2)
        layout.addWidget(unloadDataBtn, 2, 2)
        layout.addWidget(delAllDataBtn, 3, 2)
        layout.addWidget(unloadAllDataBtn, 4, 2)
        layout.addWidget(RAMusageLabel, 4, 0)
        layout.addWidget(self.memBar, 5, 0)


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
            self.data_list.item(i).setBackground(QtGui.QColor('transparent'))

    def updateMemBar(self):
        self.memBar.setValue(psutil.virtual_memory()[2])
