from pyqtgraph.Qt import QtCore, QtGui, QtWidgets

from .guitools import BetterPushButton


class MultiDataFrame(QtWidgets.QFrame):
    # Signals
    sigAddDataClicked = QtCore.Signal()
    sigLoadCurrentDataClicked = QtCore.Signal()
    sigLoadAllDataClicked = QtCore.Signal()
    sigUnloadCurrentDataClicked = QtCore.Signal()
    sigUnloadAllDataClicked = QtCore.Signal()
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

        setDataBtn = BetterPushButton('Set as current data')
        setDataBtn.clicked.connect(self.sigSetAsCurrentDataClicked)
        addDataBtn = BetterPushButton('Add data')
        addDataBtn.clicked.connect(self.sigAddDataClicked)
        loadCurrDataBtn = BetterPushButton('Load chosen data')
        loadCurrDataBtn.clicked.connect(self.sigLoadCurrentDataClicked)
        loadAllDataBtn = BetterPushButton('Load all data')
        loadAllDataBtn.clicked.connect(self.sigLoadAllDataClicked)

        delDataBtn = BetterPushButton('Delete')
        delDataBtn.clicked.connect(self.delData)
        unloadDataBtn = BetterPushButton('Unload')
        unloadDataBtn.clicked.connect(self.sigUnloadCurrentDataClicked)
        delAllDataBtn = BetterPushButton('Delete all')
        delAllDataBtn.clicked.connect(self.delAllData)
        unloadAllDataBtn = BetterPushButton('Unload all')
        unloadAllDataBtn.clicked.connect(self.sigUnloadAllDataClicked)

        ramUsageLabel = QtWidgets.QLabel('Current RAM usage')

        self.memBar = QtWidgets.QProgressBar(self)
        self.memBar.setMaximum(100)  # Percentage

        # Set layout
        layout = QtWidgets.QGridLayout()
        self.setLayout(layout)

        layout.addWidget(self.dataList, 0, 0, 4, 1)
        layout.addWidget(dataLoadedLabel, 0, 1)
        layout.addWidget(self.dataLoadedStatus, 0, 2)
        layout.addWidget(addDataBtn, 1, 1)
        layout.addWidget(loadCurrDataBtn, 2, 1)
        layout.addWidget(loadAllDataBtn, 3, 1)
        layout.addWidget(setDataBtn, 4, 1)
        layout.addWidget(delDataBtn, 1, 2)
        layout.addWidget(unloadDataBtn, 2, 2)
        layout.addWidget(delAllDataBtn, 3, 2)
        layout.addWidget(unloadAllDataBtn, 4, 2)
        layout.addWidget(ramUsageLabel, 4, 0)
        layout.addWidget(self.memBar, 5, 0)

    def requestFilePathsFromUser(self, defaultFolder=None):
        return QtWidgets.QFileDialog().getOpenFileNames(directory=defaultFolder)[0]

    def addDataObj(self, dataObj):
        listItem = QtWidgets.QListWidgetItem('Data: ' + dataObj.name)
        listItem.setData(1, dataObj)
        self.dataList.addItem(listItem)
        self.dataList.setCurrentItem(listItem)

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

    def delData(self):
        for _ in range(len(self.dataList.selectedIndexes())):
            row = self.dataList.selectedIndexes()[0].row()
            self.dataList.takeItem(row)

    def delAllData(self):
        for _ in range(self.dataList.count()):
            currRow = self.dataList.currentRow()
            self.dataList.takeItem(currRow)

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

    def updateMemBar(self, percentUsed):
        self.memBar.setValue(percentUsed)
