import dataclasses
import pkg_resources
import h5py
import imswitch
from imswitch.imcommon.controller import MainController, PickDatasetsController
from imswitch.imcommon.model import (
    ostools, initLogger, generateAPI, generateShortcuts, SharedAttributes
)
from imswitch.imcommon.framework import Thread
from .server import ImSwitchServer
from imswitch.imcontrol.model import configfiletools
from imswitch.imcontrol.view import guitools
from . import controllers
from .CommunicationChannel import CommunicationChannel
from .MasterController import MasterController
from .PickSetupController import PickSetupController
from .PickUC2BoardConfigController import PickUC2BoardConfigController
from .basecontrollers import ImConWidgetControllerFactory


class ImConMainController(MainController):
    def __init__(self, options, setupInfo, mainView, moduleCommChannel):
        self.__logger = initLogger(self)
        self.__logger.debug('Initializing')

        self.__options = options
        self.__setupInfo = setupInfo
        self.__mainView = mainView
        self._moduleCommChannel = moduleCommChannel

        # Connect view signals
        self.__mainView.sigLoadParamsFromHDF5.connect(self.loadParamsFromHDF5)
        self.__mainView.sigPickSetup.connect(self.pickSetup)
        self.__mainView.sigPickConfig.connect(self.pickUC2Config)
        self.__mainView.sigClosing.connect(self.closeEvent)

        # Init communication channel and master controller
        self.__commChannel = CommunicationChannel(self, self.__setupInfo)
        self.__masterController = MasterController(self.__setupInfo, self.__commChannel,
                                                   self._moduleCommChannel)

        # List of Controllers for the GUI Widgets
        self.__factory = ImConWidgetControllerFactory(
            self.__setupInfo, self.__masterController, self.__commChannel, self._moduleCommChannel
        )
        
        if not imswitch.IS_HEADLESS:
            self.pickSetupController = self.__factory.createController(
                PickSetupController, self.__mainView.pickSetupDialog
            )
            self.pickDatasetsController = self.__factory.createController(
                PickDatasetsController, self.__mainView.pickDatasetsDialog
            )

        self.controllers = {}

        for widgetKey, widget in self.__mainView.widgets.items():
            try:
                self.controllers[widgetKey] = self.__factory.createController(
                    (getattr(controllers, f'{widgetKey}Controller')
                    if widgetKey != 'Scan' else
                    getattr(controllers, f'{widgetKey}Controller{self.__setupInfo.scan.scanWidgetType}')), widget
                )
            except Exception as e:
                #try to get it from the plugins
                for entry_point in pkg_resources.iter_entry_points(f'imswitch.implugins'):
                    if entry_point.name == f'{widgetKey}_controller':
                        packageController = entry_point.load()
                        self.controllers[widgetKey] = self.__factory.createController(packageController, widget)
                        break
                raise ValueError(f'No controller found for widget {widgetKey} with error {e}')
        # Generate API
        self.__api = None
        apiObjs = list(self.controllers.values()) + [self.__commChannel]
        self.__api = generateAPI(
            apiObjs,
            missingAttributeErrorMsg=lambda attr: f'The imcontrol API does either not have any'
                                                  f' method {attr}, or the widget that defines it'
                                                  f' is not included in your currently active'
                                                  f' hardware setup file.'
        )
        # Generate Shorcuts
        self.__shortcuts = None
        shorcutObjs = list(self.__mainView.widgets.values())
        self.__shortcuts = generateShortcuts(shorcutObjs)
        self.__mainView.addShortcuts(self.__shortcuts)


        self.__logger.debug("Start ImSwitch Server")
        self._serverWorker = ImSwitchServer(self.__api, setupInfo)
        self.__logger.debug(self.__api)
        self._thread = Thread()
        self._serverWorker.moveToThread(self._thread)
        self._thread.started.connect(self._serverWorker.run)
        self._thread.finished.connect(self._serverWorker.stop)
        self._thread.start()

    @property
    def api(self):
        return self.__api

    @property
    def shortcuts(self):
        return self.__shortcuts

    def loadParamsFromHDF5(self):
        """ Set detector, positioner, laser etc. params from values saved in a
        user-picked HDF5 snap/recording. """

        filePath = guitools.askForFilePath(self.__mainView, 'Open HDF5 file', nameFilter='*.hdf5')
        if not filePath:
            return

        with h5py.File(filePath) as file:
            datasetsInFile = file.keys()
            if len(datasetsInFile) < 1:
                # File does not contain any datasets
                return
            elif len(datasetsInFile) == 1:
                datasetToLoad = list(datasetsInFile)[0]
            else:
                # File contains multiple datasets
                self.pickDatasetsController.setDatasets(filePath, datasetsInFile)
                if not self.__mainView.showPickDatasetsDialogBlocking():
                    return

                datasetsSelected = self.pickDatasetsController.getSelectedDatasets()
                if len(datasetsSelected) != 1:
                    return

                datasetToLoad = datasetsSelected[0]

            attrs = SharedAttributes.fromHDF5File(file, datasetToLoad)
            self.__commChannel.sharedAttrs.update(attrs)

    def pickSetup(self):
        """ Let the user change which setup is used. """

        options, _ = configfiletools.loadOptions()

        self.pickSetupController.setSetups(configfiletools.getSetupList())
        self.pickSetupController.setSelectedSetup(options.setupFileName)
        if not self.__mainView.showPickSetupDialogBlocking():
            return
        setupFileName = self.pickSetupController.getSelectedSetup()
        if not setupFileName:
            return

        proceed = guitools.askYesNoQuestion(self.__mainView, 'Warning',
                                            'The software will restart. Continue?')
        if not proceed:
            return

        options = dataclasses.replace(options, setupFileName=setupFileName)
        configfiletools.saveOptions(options)
        ostools.restartSoftware()

    def closeEvent(self):
        self.__logger.debug('Shutting down')
        self.__factory.closeAllCreatedControllers()
        self.__masterController.closeEvent()
        
        # seems like the imswitchserver is not closing from the closing event, need to hard kill it
        #self._serverWorker.stop()
        #self._thread.quit()
        #self._thread.terminate()        
        #del self._thread

    def pickUC2Config(self):
        """ Let the user change which UC2 Board config is used. """

        options, _ = configfiletools.loadUC2BoardConfigs()

        self.pickSetupController.setSetups(configfiletools.getBoardConfigList())
        self.pickSetupController.setSelectedSetup(options.setupFileName)
        if not self.__mainView.showPickSetupDialogBlocking():
            return
        setupFileName = self.pickSetupController.getSelectedSetup()
        if not setupFileName:
            return

        guitools.informationDisplay(self.__mainView, "Now select 'load from file' in the UC2 Config Widget and flash the pin-configuration")


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
