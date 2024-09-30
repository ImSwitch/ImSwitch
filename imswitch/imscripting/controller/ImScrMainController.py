from imswitch.imcommon.controller import MainController
from imswitch.imcommon.model import generateAPI, pythontools
from imswitch.imscripting.model import getActionsScope
from .CommunicationChannel import CommunicationChannel
from .ImScrMainViewController import ImScrMainViewController
from .basecontrollers import ImScrWidgetControllerFactory


class ImScrMainController(MainController):
    """ Main controller of imscripting. """

    def __init__(self, mainView, moduleCommChannel, multiModuleWindowController,
                 moduleMainControllers):
        self.__mainView = mainView
        self.__moduleCommChannel = moduleCommChannel
        self.__scriptScope = self._createScriptScope(moduleCommChannel, multiModuleWindowController,
                                                     moduleMainControllers)

        # Connect view signals
        self.__mainView.sigClosing.connect(self.closeEvent)

        # Init communication channel and master controller
        self.__commChannel = CommunicationChannel()

        # List of Controllers for the GUI Widgets
        self.__factory = ImScrWidgetControllerFactory(
            self.__scriptScope, self.__commChannel, self.__moduleCommChannel
        )

        self.mainViewController = self.__factory.createController(
            ImScrMainViewController, self.__mainView
        )

        # Connect signals from ModuleCommunicationChannel
        self.__moduleCommChannel.sigRunScript.connect(self.__commChannel.sigRunScript)

    def _createScriptScope(self, moduleCommChannel, multiModuleWindowController,
                           moduleMainControllers):
        """ Generates a scope of objects that are intended to be accessible by scripts. """

        scope = {}
        scope.update({
            'moduleCommChannel': moduleCommChannel,
            'mainWindow': generateAPI([multiModuleWindowController]),
            'controllers': pythontools.dictToROClass(moduleMainControllers),
            'api': pythontools.dictToROClass(
                {key: controller.api
                 for key, controller in moduleMainControllers.items()
                 if hasattr(controller, 'api')}
            )
        })
        scope.update(getActionsScope(scope.copy()))
        
        return scope

    def closeEvent(self):
        self.__factory.closeAllCreatedControllers()


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
