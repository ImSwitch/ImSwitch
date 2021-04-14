from pyqtgraph.Qt import QtCore, QtGui, QtWidgets

from .guitools import BetterPushButton


class MultiDataFrame(QtWidgets.QFrame):
    # Signals
    sigAddDataClicked = QtCore.Signal()
    sigLoadCurrentDataClicked = QtCore.Signal()
    sigLoadAllDataClicked = QtCore.Signal()
    sigUnloadCurrentDataClicked = QtCore.Signal()
    sigUnloadAllDataClicked = QtCore.Signal()
    sigDeleteCurrentDataClicked = QtCore.Signal()
    sigDeleteAllDataClicked = QtCore.Signal()
    sigSaveCurrentDataClicked = QtCore.Signal()
    sigSaveAllDataClicked = QtCore.Signal()
    sigSetAsCurrentDataClicked = QtCore.Signal()
    sigSelectedItemChanged = QtCore.Signal()

    # Methods
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.dataList = QtWidgets.QListWidget()
        self.dataList.currentItemChanged.connect(self.sigSelectedItemChanged)
        self.dataList.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)

        dataLoadedLabel = QtWidgets.QLabel('Data loaded')
        dataLoadedLabel.setAlignment(QtCore.Qt.AlignTop)
        self.dataLoadedStatus = QtWidgets.QLabel()
        self.dataLoadedStatus.setAlignment(QtCore.Qt.AlignTop)

        self.setDataBtn = BetterPushButton('Set as current data')
        self.setDataBtn.clicked.connect(self.sigSetAsCurrentDataClicked)
        self.addDataBtn = BetterPushButton('Add data')
        self.addDataBtn.clicked.connect(self.sigAddDataClicked)
        self.loadCurrDataBtn = BetterPushButton('Load selected data')
        self.loadCurrDataBtn.clicked.connect(self.sigLoadCurrentDataClicked)
        self.loadAllDataBtn = BetterPushButton('Load all data')
        self.loadAllDataBtn.clicked.connect(self.sigLoadAllDataClicked)

        self.delDataBtn = BetterPushButton('Remove')
        self.delDataBtn.clicked.connect(self.sigDeleteCurrentDataClicked)
        self.unloadDataBtn = BetterPushButton('Unload')
        self.unloadDataBtn.clicked.connect(self.sigUnloadCurrentDataClicked)
        self.delAllDataBtn = BetterPushButton('Remove all')
        self.delAllDataBtn.clicked.connect(self.sigDeleteAllDataClicked)
        self.unloadAllDataBtn = BetterPushButton('Unload all')
        self.unloadAllDataBtn.clicked.connect(self.sigUnloadAllDataClicked)
        self.saveDataBtn = BetterPushButton('Save selected data')
        self.saveDataBtn.clicked.connect(self.sigSaveCurrentDataClicked)
        self.saveAllDataBtn = BetterPushButton('Save all')
        self.saveAllDataBtn.clicked.connect(self.sigSaveAllDataClicked)

        ramUsageLabel = QtWidgets.QLabel('Current RAM usage')

        self.memBar = QtWidgets.QProgressBar(self)
        self.memBar.setMaximum(100)  # Percentage

        # Set layout
        layout = QtWidgets.QGridLayout()
        self.setLayout(layout)

        layout.addWidget(self.dataList, 0, 0, 4, 1)
        layout.addWidget(dataLoadedLabel, 0, 1)
        layout.addWidget(self.dataLoadedStatus, 0, 2)
        layout.addWidget(self.addDataBtn, 1, 1)
        layout.addWidget(self.loadCurrDataBtn, 2, 1)
        layout.addWidget(self.loadAllDataBtn, 3, 1)
        layout.addWidget(self.setDataBtn, 4, 1)
        layout.addWidget(self.delDataBtn, 1, 2)
        layout.addWidget(self.unloadDataBtn, 2, 2)
        layout.addWidget(self.delAllDataBtn, 3, 2)
        layout.addWidget(self.unloadAllDataBtn, 4, 2)
        layout.addWidget(self.saveDataBtn, 5, 1)
        layout.addWidget(self.saveAllDataBtn, 5, 2)
        layout.addWidget(self.unloadAllDataBtn, 4, 2)
        layout.addWidget(ramUsageLabel, 4, 0)
        layout.addWidget(self.memBar, 5, 0)

    def requestFilePathsFromUser(self, defaultFolder=None):
        return QtWidgets.QFileDialog().getOpenFileNames(directory=defaultFolder)[0]

    def requestDeleteSelectedConfirmation(self):
        result = QtWidgets.QMessageBox.question(
            self, 'Remove selected?', 'Remove the selected item?',
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
        )
        return result == QtWidgets.QMessageBox.Yes

    def requestDeleteAllConfirmation(self):
        result = QtWidgets.QMessageBox.question(
            self, 'Remove all?', 'Remove all items?',
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
        )
        return result == QtWidgets.QMessageBox.Yes

    def addDataObj(self, name, dataObj):
        listItem = QtWidgets.QListWidgetItem(f'Data: {name}')
        listItem.setData(1, dataObj)
        listItem.setData(3, name)
        self.dataList.addItem(listItem)
        self.dataList.setCurrentItem(listItem)

    def getDataObjByName(self, name):
        for i in range(self.dataList.count()):
            if self.dataList.item(i).data(3) == name:
                return self.dataList.item(i).data(1)

        return None

    def setDataObjMemoryFlag(self, name, inMemory):
        for i in range(self.dataList.count()):
            if self.dataList.item(i).data(3) == name:
                dataObj = self.dataList.item(i).data(1)
                itemName = f'Data: {dataObj.name}'
                if inMemory:
                    itemName += ' (MEMORY)'
                self.dataList.item(i).setText(itemName)

    def getSelectedDataObj(self):
        currentItem = self.dataList.currentItem()
        return self.dataList.currentItem().data(1) if currentItem is not None else None

    def getSelectedDataObjs(self):
        for i in range(self.dataList.count()):
            if self.dataList.item(i).isSelected():
                yield self.dataList.item(i).data(1)

    def getAllDataObjs(self):
        for i in range(self.dataList.count()):
            yield self.dataList.item(i).data(1)

    def delDataByName(self, name):
        for i in range(self.dataList.count()):
            if self.dataList.item(i) is not None and self.dataList.item(i).data(3) == name:
                self.dataList.takeItem(i)

    def setCurrentRowHighlighted(self, highlighted):
        self.dataList.currentItem().setBackground(
            QtGui.QColor('green' if highlighted else 'transparent')
        )

    def setAllRowsHighlighted(self, highlighted):
        for i in range(self.dataList.count()):
            self.dataList.item(i).setBackground(
                QtGui.QColor('green' if highlighted else 'transparent')
            )

    def setLoadedStatusText(self, text):
        self.dataLoadedStatus.setText(text)

    def setAddButtonEnabled(self, value):
        self.addDataBtn.setEnabled(value)

    def setSetCurrentButtonEnabled(self, value):
        self.setDataBtn.setEnabled(value)

    def setLoadButtonEnabled(self, value):
        self.loadCurrDataBtn.setEnabled(value)

    def setLoadAllButtonEnabled(self, value):
        self.loadAllDataBtn.setEnabled(value)

    def setUnloadButtonEnabled(self, value):
        self.unloadDataBtn.setEnabled(value)

    def setUnloadAllButtonEnabled(self, value):
        self.unloadAllDataBtn.setEnabled(value)

    def setDeleteButtonEnabled(self, value):
        self.delDataBtn.setEnabled(value)

    def setDeleteAllButtonEnabled(self, value):
        self.delAllDataBtn.setEnabled(value)

    def setSaveButtonEnabled(self, value):
        self.saveDataBtn.setEnabled(value)

    def setSaveAllButtonEnabled(self, value):
        self.saveAllDataBtn.setEnabled(value)

    def updateMemBar(self, percentUsed):
        self.memBar.setValue(percentUsed)


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
