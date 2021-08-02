import numpy as np
import pyqtgraph as pg
from pyqtgraph.dockarea import Dock, DockArea
from pyqtgraph.parametertree import Parameter, ParameterTree
from qtpy import QtCore, QtWidgets

from .DataFrame import DataFrame
from .MultiDataFrame import MultiDataFrame
from .PickDatasetsDialog import PickDatasetsDialog
from .ReconstructionView import ReconstructionView
from .ScanParamsDialog import ScanParamsDialog
from .guitools import BetterPushButton


class ImRecMainView(QtWidgets.QMainWindow):
    sigSaveReconstruction = QtCore.Signal()
    sigSaveCoeffs = QtCore.Signal()
    sigSetDataFolder = QtCore.Signal()
    sigSetSaveFolder = QtCore.Signal()

    sigReconstuctCurrent = QtCore.Signal()
    sigReconstructMulti = QtCore.Signal()
    sigQuickLoadData = QtCore.Signal()
    sigUpdate = QtCore.Signal()

    sigShowPatternChanged = QtCore.Signal(bool)
    sigFindPattern = QtCore.Signal()
    sigShowScanParamsClicked = QtCore.Signal()
    sigPatternParamsChanged = QtCore.Signal()

    sigClosing = QtCore.Signal()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setWindowTitle('Image Reconstruction')

        # self parameters
        self.r_l_text = 'Right/Left'
        self.u_d_text = 'Up/Down'
        self.b_f_text = 'Back/Forth'
        self.timepoints_text = 'Timepoints'
        self.p_text = 'pos'
        self.n_text = 'neg'

        # Actions in menubar
        menuBar = self.menuBar()
        file = menuBar.addMenu('&File')

        saveReconAction = QtWidgets.QAction('Save reconstruction', self)
        saveReconAction.setShortcut('Ctrl+D')
        saveReconAction.triggered.connect(self.sigSaveReconstruction)
        file.addAction(saveReconAction)
        saveCoeffsAction = QtWidgets.QAction('Save coefficients', self)
        saveCoeffsAction.setShortcut('Ctrl+A')
        saveCoeffsAction.triggered.connect(self.sigSaveCoeffs)
        file.addAction(saveCoeffsAction)

        setDataFolder = QtWidgets.QAction('Set data folder', self)
        setDataFolder.triggered.connect(self.sigSetDataFolder)
        file.addAction(setDataFolder)

        setSaveFolder = QtWidgets.QAction('Set save folder', self)
        setSaveFolder.triggered.connect(self.sigSetSaveFolder)
        file.addAction(setSaveFolder)

        self.dataFrame = DataFrame()
        self.multiDataFrame = MultiDataFrame()

        btnFrame = BtnFrame()
        btnFrame.sigReconstuctCurrent.connect(self.sigReconstuctCurrent)
        btnFrame.sigReconstructMulti.connect(self.sigReconstructMulti)
        btnFrame.sigQuickLoadData.connect(self.sigQuickLoadData)
        btnFrame.sigUpdate.connect(self.sigUpdate)

        self.reconstructionWidget = ReconstructionView()

        self.parTree = ReconParTree()
        self.showPatBool = self.parTree.p.param('Show pattern')
        self.showPatBool.sigValueChanged.connect(lambda _, v: self.sigShowPatternChanged.emit(v))
        self.bleachBool = self.parTree.p.param('Bleaching correction')
        self.findPatBtn = self.parTree.p.param('Pattern').param('Find pattern')
        self.findPatBtn.sigActivated.connect(self.sigFindPattern)
        self.scanParWinBtn = self.parTree.p.param('Scanning parameters')
        self.scanParWinBtn.sigActivated.connect(self.sigShowScanParamsClicked)
        self.parTree.p.param('Pattern').sigTreeStateChanged.connect(self.sigPatternParamsChanged)

        self.scanParamsDialog = ScanParamsDialog(
            self, self.r_l_text, self.u_d_text, self.b_f_text,
            self.timepoints_text, self.p_text, self.n_text
        )

        self.pickDatasetsDialog = PickDatasetsDialog(self)

        parameterFrame = QtWidgets.QFrame()
        parameterGrid = QtWidgets.QGridLayout()
        parameterFrame.setLayout(parameterGrid)
        parameterGrid.addWidget(self.parTree, 0, 0)

        DataDock = DockArea()

        self.multiDataDock = Dock('Multidata management')
        self.multiDataDock.addWidget(self.multiDataFrame)
        DataDock.addDock(self.multiDataDock)

        self.currentDataDock = Dock('Current data')
        self.currentDataDock.addWidget(self.dataFrame)
        DataDock.addDock(self.currentDataDock, 'above', self.multiDataDock)

        layout = QtWidgets.QHBoxLayout()
        self.cwidget = QtWidgets.QWidget()
        self.setCentralWidget(self.cwidget)
        self.cwidget.setLayout(layout)

        leftContainer = QtWidgets.QVBoxLayout()
        leftContainer.setContentsMargins(0, 0, 0, 0)

        rightContainer = QtWidgets.QVBoxLayout()
        rightContainer.setContentsMargins(0, 0, 0, 0)

        leftContainer.addWidget(parameterFrame, 1)
        leftContainer.addWidget(btnFrame, 0)
        leftContainer.addWidget(DataDock, 1)
        rightContainer.addWidget(self.reconstructionWidget)

        layout.addLayout(leftContainer, 1)
        layout.addLayout(rightContainer, 3)

        pg.setConfigOption('imageAxisOrder', 'row-major')

    def requestFilePathFromUser(self, caption=None, defaultFolder=None, nameFilter=None,
                                isSaving=False):
        func = (QtWidgets.QFileDialog().getOpenFileName if not isSaving
                else QtWidgets.QFileDialog().getSaveFileName)

        return func(self, caption=caption, directory=defaultFolder, filter=nameFilter)[0]

    def requestFolderPathFromUser(self, caption=None, defaultFolder=None):
        return QtWidgets.QFileDialog.getExistingDirectory(caption=caption, directory=defaultFolder)

    def raiseCurrentDataDock(self):
        self.currentDataDock.raiseDock()

    def raiseMultiDataDock(self):
        self.multiDataDock.raiseDock()

    def addNewData(self, reconObj):
        self.reconstructionWidget.addNewData(reconObj)

    def getMultiDatas(self):
        dataList = self.multiDataFrame.dataList
        for i in range(dataList.count()):
            yield dataList.item(i).data(1)

    def showScanParamsDialog(self, blocking=False):
        if blocking:
            result = self.scanParamsDialog.exec_()
            return result == QtWidgets.QDialog.Accepted
        else:
            self.scanParamsDialog.show()

    def showPickDatasetsDialog(self, blocking=False):
        if blocking:
            result = self.pickDatasetsDialog.exec_()
            return result == QtWidgets.QDialog.Accepted
        else:
            self.pickDatasetsDialog.show()

    def getPatternParams(self):
        patternPars = self.parTree.p.param('Pattern')
        return (np.mod(patternPars.param('Row-offset').value(),
                       patternPars.param('Row-period').value()),
                np.mod(patternPars.param('Col-offset').value(),
                       patternPars.param('Col-period').value()),
                patternPars.param('Row-period').value(),
                patternPars.param('Col-period').value())

    def setPatternParams(self, rowOffset, colOffset, rowPeriod, colPeriod):
        patternPars = self.parTree.p.param('Pattern')
        patternPars.param('Row-offset').setValue(rowOffset)
        patternPars.param('Col-offset').setValue(colOffset)
        patternPars.param('Row-period').setValue(rowPeriod)
        patternPars.param('Col-period').setValue(colPeriod)

    def getComputeDevice(self):
        return self.parTree.p.param('CPU/GPU').value()

    def getPixelSizeNm(self):
        return self.parTree.p.param('Pixel size').value()

    def getFwhmNm(self):
        return self.parTree.p.param('Reconstruction options').param('PSF FWHM').value()

    def getBgModelling(self):
        return self.parTree.p.param('Reconstruction options').param('BG modelling').value()

    def getBgGaussianSize(self):
        return self.parTree.p.param('Reconstruction options').param('BG modelling') \
            .param('BG Gaussian size').value()

    def closeEvent(self, event):
        self.sigClosing.emit()
        event.accept()


class ReconParTree(ParameterTree):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Parameter tree for the reconstruction
        params = [
            {'name': 'Pixel size', 'type': 'float', 'value': 65, 'suffix': 'nm'},
            {'name': 'CPU/GPU', 'type': 'list', 'values': ['GPU', 'CPU']},
            {'name': 'Pattern', 'type': 'group', 'children': [
                {'name': 'Row-offset', 'type': 'float', 'value': 9.89, 'limits': (0, 9999)},
                {'name': 'Col-offset', 'type': 'float', 'value': 10.4, 'limits': (0, 9999)},
                {'name': 'Row-period', 'type': 'float', 'value': 11.05, 'limits': (0, 9999)},
                {'name': 'Col-period', 'type': 'float', 'value': 11.05, 'limits': (0, 9999)},
                {'name': 'Find pattern', 'type': 'action'}]},
            {'name': 'Reconstruction options', 'type': 'group', 'children': [
                {'name': 'PSF FWHM', 'type': 'float', 'value': 220, 'limits': (0, 9999),
                 'suffix': 'nm'},
                {'name': 'BG modelling', 'type': 'list',
                 'values': ['Constant', 'Gaussian', 'No background'], 'children': [
                    {'name': 'BG Gaussian size', 'type': 'float', 'value': 500, 'suffix': 'nm'}]}]},
            {'name': 'Scanning parameters', 'type': 'action'},
            {'name': 'Show pattern', 'type': 'bool'},
            {'name': 'Bleaching correction', 'type': 'bool'}]

        self.p = Parameter.create(name='params', type='group', children=params)
        self.setParameters(self.p, showTop=False)
        self._writable = True


class BtnFrame(QtWidgets.QFrame):
    sigReconstuctCurrent = QtCore.Signal()
    sigReconstructMulti = QtCore.Signal()
    sigQuickLoadData = QtCore.Signal()
    sigUpdate = QtCore.Signal()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        reconCurrBtn = BetterPushButton('Reconstruct current')
        reconCurrBtn.clicked.connect(self.sigReconstuctCurrent)
        reconMultiBtn = BetterPushButton('Reconstruct multidata')
        reconMultiBtn.clicked.connect(self.sigReconstructMulti)
        quickLoadDataBtn = BetterPushButton('Quick load data')
        quickLoadDataBtn.clicked.connect(self.sigQuickLoadData)
        updateBtn = BetterPushButton('Update reconstruction')
        updateBtn.clicked.connect(self.sigUpdate)

        layout = QtWidgets.QGridLayout()
        self.setLayout(layout)

        layout.addWidget(quickLoadDataBtn, 0, 0, 1, 2)
        layout.addWidget(reconCurrBtn, 1, 0)
        layout.addWidget(reconMultiBtn, 1, 1)
        layout.addWidget(updateBtn, 2, 0, 1, 2)


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
