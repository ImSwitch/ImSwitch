from imswitch import IS_HEADLESS
from dataclasses import dataclass

# FIXME: We should probably create another file that does not import these files
from imswitch.imcommon.framework import Signal
if not IS_HEADLESS:
    from pyqtgraph.dockarea import Dock, DockArea
    from qtpy import QtCore, QtWidgets
    from qtpy.QtWidgets import QMainWindow
    from imswitch.imcommon.view import PickDatasetsDialog
    from .PickSetupDialog import PickSetupDialog
else:
    Dock = None
    DockArea = None
    QtCore = None
    QtWidgets = None
    QMainWindow = object
from imswitch.imcommon.model import initLogger

from . import widgets
import pkg_resources
import importlib

class ImConMainView(QMainWindow):
    sigLoadParamsFromHDF5 = Signal()
    sigPickSetup = Signal()
    sigPickConfig = Signal()
    sigClosing = Signal()

    def __init__(self, options, viewSetupInfo, *args, **kwargs):
        self.__logger = initLogger(self)
        self.__logger.debug('Initializing')

        super().__init__(*args, **kwargs)

        self.factory = self.factory = widgets.WidgetFactory(options)
        self.docks = {}
        self.widgets = {}
        self.shortcuts = {}

        self.viewSetupInfo = viewSetupInfo
        if not IS_HEADLESS:
            self.pickSetupDialog = PickSetupDialog(self)
            self.pickDatasetsDialog = PickDatasetsDialog(self, allowMultiSelect=False)

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

            self.pickConfigAction = QtWidgets.QAction('Pick hardware config', self)
            self.pickConfigAction.triggered.connect(self.sigPickConfig)
            tools.addAction(self.pickConfigAction)

            # Window
            self.setWindowTitle('ImSwitch')

            self.cwidget = QtWidgets.QWidget()
            layout = QtWidgets.QHBoxLayout()
            self.cwidget.setLayout(layout)
            self.setCentralWidget(self.cwidget)

        # Dock area
        rightDockInfos = {
            'Autofocus': _DockInfo(name='Autofocus', yPosition=1),
            'FocusLock': _DockInfo(name='Focus Lock', yPosition=0),
            'FOVLock': _DockInfo(name='FOV Lock', yPosition=0),
            'SLM': _DockInfo(name='SLM', yPosition=0),
            'UC2Config': _DockInfo(name='UC2Config', yPosition=0),
            'SIM': _DockInfo(name='SIM', yPosition=0),
            'DPC': _DockInfo(name='DPC', yPosition=0),
            'MCT': _DockInfo(name='MCT', yPosition=0),
            'ROIScan': _DockInfo(name='ROIScan', yPosition=0),
            'Lightsheet': _DockInfo(name='Lightsheet', yPosition=0),
            'WebRTC': _DockInfo(name='WebRTC', yPosition=0),
            'Hypha': _DockInfo(name='Hypha', yPosition=0),
            'MockXX': _DockInfo(name='MockXX', yPosition=0),
            'JetsonNano': _DockInfo(name='JetsonNano', yPosition=0),
            'HistoScan': _DockInfo(name='HistoScan', yPosition=1),
            'Flatfield': _DockInfo(name='Flatfield', yPosition=1),
            'PixelCalibration': _DockInfo(name='PixelCalibration', yPosition=1),
            'ISM': _DockInfo(name='ISM', yPosition=0),
            'Laser': _DockInfo(name='Laser Control', yPosition=0),
            'LED': _DockInfo(name='LED Control', yPosition=0),
            'EtSTED': _DockInfo(name='EtSTED', yPosition=0),
            'Positioner': _DockInfo(name='Positioner', yPosition=1),
            'Rotator': _DockInfo(name='Rotator', yPosition=1),
            'MotCorr': _DockInfo(name='Motorized Correction Collar', yPosition=1),
            'StandaPositioner': _DockInfo(name='StandaPositioner', yPosition=1),
            'StandaStage': _DockInfo(name='StandaStage', yPosition=1),
            'SLM': _DockInfo(name='SLM', yPosition=2),
            'Scan': _DockInfo(name='Scan', yPosition=2),
            'RotationScan': _DockInfo(name='RotationScan', yPosition=2),
            'BeadRec': _DockInfo(name='Bead Rec', yPosition=3),
            'AlignmentLine': _DockInfo(name='Alignment Tool', yPosition=3),
            'AlignAverage': _DockInfo(name='Axial Alignment Tool', yPosition=3),
            'AlignXY': _DockInfo(name='Rotational Alignment Tool', yPosition=3),
            'ULenses': _DockInfo(name='uLenses Tool', yPosition=3),
            'FFT': _DockInfo(name='FFT Tool', yPosition=3),
            'Holo': _DockInfo(name='Holo Tool', yPosition=3),
            'Joystick': _DockInfo(name='Joystick Tool', yPosition=3),
            'Histogramm': _DockInfo(name='Histogramm Tool', yPosition=3),
            'STORMRecon': _DockInfo(name='STORM Recon Tool', yPosition=2),
            'HoliSheet': _DockInfo(name='HoliSheet Tool', yPosition=3),
            'FlowStop': _DockInfo(name='FlowStop Tool', yPosition=3),
            'ObjectiveRevolver': _DockInfo(name='Objective Revolver', yPosition=3),
            'Temperature': _DockInfo(name='Temperature Controller', yPosition=3),
            'SquidStageScan': _DockInfo(name='SquidStageScan Tool', yPosition=3),
            'WellPlate': _DockInfo(name='Wellplate Tool', yPosition=1),
            'Deck': _DockInfo(name="Deck Tool", yPosition=1),
            'DeckScan': _DockInfo(name="Deck Scanner", yPosition=1),
            'LEDMatrix': _DockInfo(name='LEDMatrix Tool', yPosition=0),
            'Watcher': _DockInfo(name='File Watcher', yPosition=3),
            'Tiling': _DockInfo(name='Tiling', yPosition=3)
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
        enabledDockKeys = self.viewSetupInfo.availableWidgets
        if enabledDockKeys is False:
            enabledDockKeys = []
        elif enabledDockKeys is True:
            enabledDockKeys = allDockKeys

        if 'Image' in enabledDockKeys and not IS_HEADLESS:
            self.docks['Image'] = Dock('Image Display', size=(1, 1))
            self.widgets['Image'] = self.factory.createWidget(widgets.ImageWidget)
            self.docks['Image'].addWidget(self.widgets['Image'])
            self.factory.setArgument('napariViewer', self.widgets['Image'].napariViewer)
            dockArea.addDock(self.docks['Image'], 'left')
        # if we load the widget as a plugin we have to set a default position
        # filter those enabeldDockKeys that are not in rightDockInfos
        pluginDockKeys = [key for key in enabledDockKeys if (key not in rightDockInfos and key not in leftDockInfos and key!="Image")]
        # add the pluginDockKeys to the rightDockInfos with default position
        for widgetKey in pluginDockKeys:
            rightDockInfos[widgetKey] = _DockInfo(name=widgetKey, yPosition=0)

        rightDocks = self._addDocks(
            {k: v for k, v in rightDockInfos.items() if k in enabledDockKeys},
            dockArea, 'right'
        )


        lefDocks = self._addDocks(
            {k: v for k, v in leftDockInfos.items() if k in enabledDockKeys},
            dockArea, 'left'
        )

    # Add dock area to layout
        if not IS_HEADLESS:
            layout.addWidget(dockArea)

        '''
        # TODO: THIS HAS NO EFFECT! WHY?
        # Maximize window
        self.hide()  # Minimize time the window is displayed while loading multi module window

        # Adjust dock sizes (the window has to be maximized first for this to work properly)
        if 'Settings' in self.docks:
            self.docks['Settings'].setStretch(1, 1)
            self.docks['Settings'].container().setStretch(1, 1)
        if len(rightDocks) > 0:
            rightDocks[-1].setStretch(1, 1)
        if 'Image' in self.docks:
            self.docks['Image'].setStretch(1, 1)

        self.showMaximized()

        # Adjust dock sizes (the window has to be maximized first for this to work properly)
        if 'Settings' in self.docks:
            self.docks['Settings'].setStretch(1, 1)
            self.docks['Settings'].container().setStretch(1, 1)
        if len(rightDocks) > 0:
            rightDocks[-1].setStretch(1, 1)
        if 'Image' in self.docks:
            self.docks['Image'].setStretch(1, 1)
        '''
    def addShortcuts(self, shortcuts):
        if not IS_HEADLESS:
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
            try:
                self.widgets[widgetKey] = self.factory.createWidget(
                    getattr(widgets, f'{widgetKey}Widget')
                    if widgetKey != 'Scan' else
                    getattr(widgets, f'{widgetKey}Widget{self.viewSetupInfo.scan.scanWidgetType}')
                )
            except Exception as e:
                # try to get it from the plugins
                foundPluginController = False
                for entry_point in pkg_resources.iter_entry_points(f'imswitch.implugins'):
                    if entry_point.name == f'{widgetKey}_widget':
                        packageWidget = entry_point.load()
                        self.widgets[widgetKey] = self.factory.createWidget(packageWidget)
                        foundPluginController = True
                        break
                if not foundPluginController:
                    self.__logger.error(f"Could not load widget {widgetKey} from imswitch.imcontrol.view.widgets", e)
            self.docks[widgetKey] = Dock(dockInfo.name, size=(1, 1))
            try:self.docks[widgetKey].addWidget(self.widgets[widgetKey])
            except:
                self.__logger.error(f"Could not add widget {widgetKey} to dock {dockInfo.name}")
                continue
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

class ImConMainViewNoQt(object):
    # FIXME: Hacky way to make this class compatible with the rest of the code without QT
    def __init__(self, options, viewSetupInfo, *args, **kwargs):
        self.__logger = initLogger(self)
        self.__logger.debug('Initializing')

        super().__init__(*args, **kwargs)
        self.docks = {}
        self.widgets = {}
        self.shortcuts = {}

        self.viewSetupInfo = viewSetupInfo

        # Dock area
        allDockKeys = {
            'Autofocus': _DockInfo(name='Autofocus', yPosition=1),
            'FocusLock': _DockInfo(name='Focus Lock', yPosition=0),
            'FOVLock': _DockInfo(name='FOV Lock', yPosition=0),
            'SLM': _DockInfo(name='SLM', yPosition=0),
            'UC2Config': _DockInfo(name='UC2Config', yPosition=0),
            'SIM': _DockInfo(name='SIM', yPosition=0),
            'DPC': _DockInfo(name='DPC', yPosition=0),
            'MCT': _DockInfo(name='MCT', yPosition=0),
            'ROIScan': _DockInfo(name='ROIScan', yPosition=0),
            'Lightsheet': _DockInfo(name='Lightsheet', yPosition=0),
            'WebRTC': _DockInfo(name='WebRTC', yPosition=0),
            'Hypha': _DockInfo(name='Hypha', yPosition=0),
            'MockXX': _DockInfo(name='MockXX', yPosition=0),
            'JetsonNano': _DockInfo(name='JetsonNano', yPosition=0),
            'HistoScan': _DockInfo(name='HistoScan', yPosition=1),
            'Flatfield': _DockInfo(name='Flatfield', yPosition=1),
            'PixelCalibration': _DockInfo(name='PixelCalibration', yPosition=1),
            'ISM': _DockInfo(name='ISM', yPosition=0),
            'Laser': _DockInfo(name='Laser Control', yPosition=0),
            'LED': _DockInfo(name='LED Control', yPosition=0),
            'EtSTED': _DockInfo(name='EtSTED', yPosition=0),
            'Positioner': _DockInfo(name='Positioner', yPosition=1),
            'Rotator': _DockInfo(name='Rotator', yPosition=1),
            'MotCorr': _DockInfo(name='Motorized Correction Collar', yPosition=1),
            'StandaPositioner': _DockInfo(name='StandaPositioner', yPosition=1),
            'StandaStage': _DockInfo(name='StandaStage', yPosition=1),
            'SLM': _DockInfo(name='SLM', yPosition=2),
            'Scan': _DockInfo(name='Scan', yPosition=2),
            'RotationScan': _DockInfo(name='RotationScan', yPosition=2),
            'BeadRec': _DockInfo(name='Bead Rec', yPosition=3),
            'AlignmentLine': _DockInfo(name='Alignment Tool', yPosition=3),
            'AlignAverage': _DockInfo(name='Axial Alignment Tool', yPosition=3),
            'AlignXY': _DockInfo(name='Rotational Alignment Tool', yPosition=3),
            'ULenses': _DockInfo(name='uLenses Tool', yPosition=3),
            'FFT': _DockInfo(name='FFT Tool', yPosition=3),
            'Holo': _DockInfo(name='Holo Tool', yPosition=3),
            'Joystick': _DockInfo(name='Joystick Tool', yPosition=3),
            'Histogramm': _DockInfo(name='Histogramm Tool', yPosition=3),
            'STORMRecon': _DockInfo(name='STORM Recon Tool', yPosition=2),
            'HoliSheet': _DockInfo(name='HoliSheet Tool', yPosition=3),
            'FlowStop': _DockInfo(name='FlowStop Tool', yPosition=3),
            'FLIMLabs': _DockInfo(name='FLIMLabs Tool', yPosition=3),
            'ObjectiveRevolver': _DockInfo(name='Objective Revolver', yPosition=3),
            'Temperature': _DockInfo(name='Temperature Controller', yPosition=3),
            'SquidStageScan': _DockInfo(name='SquidStageScan Tool', yPosition=3),
            'WellPlate': _DockInfo(name='Wellplate Tool', yPosition=1),
            'Deck': _DockInfo(name="Deck Tool", yPosition=1),
            'DeckScan': _DockInfo(name="Deck Scanner", yPosition=1),
            'LEDMatrix': _DockInfo(name='LEDMatrix Tool', yPosition=0),
            'Watcher': _DockInfo(name='File Watcher', yPosition=3),
            'Tiling': _DockInfo(name='Tiling', yPosition=3),
            'Settings': _DockInfo(name='Detector Settings', yPosition=0),
            'View': _DockInfo(name='Image Controls', yPosition=1),
            'Recording': _DockInfo(name='Recording', yPosition=2),
            'Console': _DockInfo(name='Console', yPosition=3)
        }
        enabledDockKeys = self.viewSetupInfo.availableWidgets
        if enabledDockKeys is False:
            enabledDockKeys = []
        elif enabledDockKeys is True:
            enabledDockKeys = allDockKeys
        self._addWidget(
            {k: v for k, v in allDockKeys.items() if k in enabledDockKeys}
        )


    def closeEvent(self, event):
        self.sigClosing.emit()
        event.accept()

    def _addWidget(self, dockInfoDict):

        for widgetKey, dockInfo in dockInfoDict.items():
            try:
                self.widgets[widgetKey] = (widgetKey)
            except Exception as e:
                # try to get it from the plugins
                foundPluginController = False
                for entry_point in pkg_resources.iter_entry_points(f'imswitch.implugins'):
                    if entry_point.name == f'{widgetKey}_widget':
                        packageWidget = entry_point.load()
                        self.widgets[widgetKey] = packageWidget
                        foundPluginController = True
                        break
                if not foundPluginController:
                    self.__logger.error(f"Could not load widget {widgetKey} from imswitch.imcontrol.view.widgets", e)


@dataclass
class _DockInfo:
    name: str
    yPosition: int


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
