from imswitch.imcommon.controller import WidgetController, MainController
from imswitch.imcommon.model import generateAPI, SharedAttributes
from imswitch.imcontrol.view import guitools
from .CommunicationChannel import CommunicationChannel
from .MasterController import MasterController
from . import controllers


class ImConMainController(MainController):
    def __init__(self, options, setupInfo, mainView, moduleCommChannel):
        self.__options = options
        self.__setupInfo = setupInfo
        self.__mainView = mainView
        self.__moduleCommChannel = moduleCommChannel

        # Connect view signals
        self.__mainView.sigLoadParamsFromHDF5.connect(self.loadParamsFromHDF5)
        self.__mainView.sigClosing.connect(self.closeEvent)

        # Init communication channel and master controller
        self.__commChannel = CommunicationChannel(self)
        self.__masterController = MasterController(self.__setupInfo, self.__commChannel,
                                                   self.__moduleCommChannel)

        # List of Controllers for the GUI Widgets
        self.__factory = controllers.ImConWidgetControllerFactory(
            self.__setupInfo, self.__masterController, self.__commChannel, self.__moduleCommChannel
        )
        self.controllers = {}

        for widgetKey, widget in self.__mainView.widgets.items():
            self.controllers[widgetKey] = self.__factory.createController(
                getattr(controllers, f'{widgetKey}Controller'), widget
            )

        self.__mainView.setDetectorRelatedDocksVisible(
            self.__masterController.detectorsManager.hasDevices()
        )

        # Generate API
        self.__api = None
        apiObjs = list(self.controllers) + [self.__commChannel]
        self.__api = generateAPI(apiObjs)

    @property
    def api(self):
        return self.__api

    def loadParamsFromHDF5(self):
        """ Set detector, positioner, laser etc. params from values saved in a
        user-picked HDF5 snap/recording. """

        filePath = guitools.askForFilePath(self.__mainView, 'Open HDF5 file', nameFilter='*.hdf5')
        if not filePath:
            return

        attrs = SharedAttributes.fromHDF5File(filePath)
        self.__commChannel.sharedAttrs.update(attrs)

    def closeEvent(self):
        self.__factory.closeAllCreatedControllers()
        self.__masterController.closeEvent()


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

