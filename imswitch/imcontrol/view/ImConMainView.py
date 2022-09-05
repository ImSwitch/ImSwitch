from dataclasses import dataclass

from pyqtgraph.dockarea import Dock, DockArea
from qtpy import QtCore, QtWidgets

from imswitch.imcommon.model import initLogger
from imswitch.imcommon.view import PickDatasetsDialog
from . import widgets
from .PickSetupDialog import PickSetupDialog


class ImConMainView(QtWidgets.QMainWindow):
    sigLoadParamsFromHDF5 = QtCore.Signal()
    sigPickSetup = QtCore.Signal()
    sigClosing = QtCore.Signal()

    def __init__(self, options, viewSetupInfo, *args, **kwargs):
        self.__logger = initLogger(self)
        self.__logger.debug('Initializing')

        super().__init__(*args, **kwargs)

        self.pickSetupDialog = PickSetupDialog(self)
        self.pickDatasetsDialog = PickDatasetsDialog(self, allowMultiSelect=False)

        # Widget factory
        self.factory = widgets.WidgetFactory(options)
        self.docks = {}
        self.widgets = {}
        self.shortcuts = {}

        # Menu Bar
        menuBar = self.menuBar()
        file = menuBar.addMenu('&File')
        tools = menuBar.addMenu('&Tools')
        self.shortcuts = menuBar.addMenu('&Shortcuts')

        self.loadParamsAction = QtWidgets.QAction('Load parameters from saved HDF5 file…', self)
        self.loadParamsAction.setShortcut('Ctrl+P')
        self.loadParamsAction.triggered.connect(self.sigLoadParamsFromHDF5)
        file.addAction(self.loadParamsAction)

        self.pickSetupAction = QtWidgets.QAction('Pick hardware setup…', self)
        self.pickSetupAction.triggered.connect(self.sigPickSetup)
        tools.addAction(self.pickSetupAction)

        # Window
        self.setWindowTitle('ImSwitch')

        self.cwidget = QtWidgets.QWidget()
        layout = QtWidgets.QHBoxLayout()
        self.cwidget.setLayout(layout)
        self.setCentralWidget(self.cwidget)

        # Dock area
        rightDockInfos = {
            'Autofocus': _DockInfo(name='Autofocus', yPosition=0),
            'FocusLock': _DockInfo(name='Focus Lock', yPosition=0),
            'SLM': _DockInfo(name='SLM', yPosition=0),
            'UC2Config': _DockInfo(name='UC2Config', yPosition=0),
            'SIM': _DockInfo(name='SIM', yPosition=0),
            'MCT': _DockInfo(name='MCT', yPosition=0),
            'ISM': _DockInfo(name='ISM', yPosition=0),
            'Laser': _DockInfo(name='Laser Control', yPosition=0),
            'EtSTED': _DockInfo(name='EtSTED', yPosition=0),
            'Positioner': _DockInfo(name='Positioner', yPosition=1),
            'SLM': _DockInfo(name='SLM', yPosition=2),
            'Scan': _DockInfo(name='Scan', yPosition=2),
            'BeadRec': _DockInfo(name='Bead Rec', yPosition=3),
            'AlignmentLine': _DockInfo(name='Alignment Tool', yPosition=3),
            'AlignAverage': _DockInfo(name='Axial Alignment Tool', yPosition=3),
            'AlignXY': _DockInfo(name='Rotational Alignment Tool', yPosition=3),
            'ULenses': _DockInfo(name='uLenses Tool', yPosition=3),
            'FFT': _DockInfo(name='FFT Tool', yPosition=3),
            'Holo': _DockInfo(name='Holo Tool', yPosition=3),
            'HoliSheet': _DockInfo(name='HoliSheet Tool', yPosition=3),
            'SquidStageScan': _DockInfo(name='SquidStageScan Tool', yPosition=3),
            'WellPlate': _DockInfo(name='Wellplate Tool', yPosition=1),
            'LEDMatrix': _DockInfo(name='LEDMatrix Tool', yPosition=0),
        }
        leftDockInfos = {
            'Settings': _DockInfo(name='Detector Settings', yPosition=0),
            'View': _DockInfo(name='Image Controls', yPosition=1),
            'Recording': _DockInfo(name='Recording', yPosition=2),
            'Console': _DockInfo(name='Console', yPosition=3)
        }
        otherDockKeys = ['Image']
        allDockKeys = list(rightDockInfos.keys()) + list(leftDockInfos.keys()) + otherDockKeys

        dockArea = DockArea()
        enabledDockKeys = viewSetupInfo.availableWidgets
        if enabledDockKeys is False:
            enabledDockKeys = []
        elif enabledDockKeys is True:
            enabledDockKeys = allDockKeys

        if 'Image' in enabledDockKeys:
            self.docks['Image'] = Dock('Image Display', size=(1, 1))
            self.widgets['Image'] = self.factory.createWidget(widgets.ImageWidget)
            self.docks['Image'].addWidget(self.widgets['Image'])
            self.factory.setArgument('napariViewer', self.widgets['Image'].napariViewer)

        rightDocks = self._addDocks(
            {k: v for k, v in rightDockInfos.items() if k in enabledDockKeys},
            dockArea, 'right'
        )

        if 'Image' in enabledDockKeys:
            dockArea.addDock(self.docks['Image'], 'left')

        self._addDocks(
            {k: v for k, v in leftDockInfos.items() if k in enabledDockKeys},
            dockArea, 'left'
        )

        # Add dock area to layout
        layout.addWidget(dockArea)

        # Maximize window
        #self.showMaximized()
        self.hide()  # Minimize time the window is displayed while loading multi module window

        # Adjust dock sizes (the window has to be maximized first for this to work properly)
        if 'Settings' in self.docks:
            self.docks['Settings'].setStretch(1, 5)
            self.docks['Settings'].container().setStretch(3, 1)
        if len(rightDocks) > 0:
            rightDocks[-1].setStretch(1, 5)
        if 'Image' in self.docks:
            self.docks['Image'].setStretch(10, 1)

    def addShortcuts(self, shortcuts):
        for s in shortcuts.values():
            action = QtWidgets.QAction(s["name"], self)
            action.setShortcut(s["key"])
            action.triggered.connect(s["callback"])
            self.shortcuts.addAction(action)

    def showPickSetupDialogBlocking(self):
        result = self.pickSetupDialog.exec_()
        return result == QtWidgets.QDialog.Accepted

    def showPickDatasetsDialogBlocking(self):
        result = self.pickDatasetsDialog.exec_()
        return result == QtWidgets.QDialog.Accepted

    def closeEvent(self, event):
        self.sigClosing.emit()
        event.accept()

    def _addDocks(self, dockInfoDict, dockArea, position):
        docks = []

        prevDock = None
        prevDockYPosition = -1
        for widgetKey, dockInfo in dockInfoDict.items():
            self.widgets[widgetKey] = self.factory.createWidget(
                getattr(widgets, f'{widgetKey}Widget')
            )
            self.docks[widgetKey] = Dock(dockInfo.name, size=(1, 1))
            self.docks[widgetKey].addWidget(self.widgets[widgetKey])
            if prevDock is None:
                dockArea.addDock(self.docks[widgetKey], position)
            elif dockInfo.yPosition > prevDockYPosition:
                dockArea.addDock(self.docks[widgetKey], 'bottom', prevDock)
            else:
                dockArea.addDock(self.docks[widgetKey], 'above', prevDock)
            prevDock = self.docks[widgetKey]
            prevDockYPosition = dockInfo.yPosition
            docks.append(prevDock)

        return docks


@dataclass
class _DockInfo:
    name: str
    yPosition: int


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
