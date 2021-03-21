from dotmap import DotMap

from imcommon.controller import MainController
from .CommunicationChannel import CommunicationChannel
from .basecontrollers import ImScrWidgetControllerFactory
from .ImScrMainViewController import ImScrMainViewController
from ..model import getActionsScope


class ImScrMainController(MainController):
    def __init__(self, mainView, moduleCommChannel, multiModuleWindow,
                 moduleMainViews, moduleMainControllers):
        self.__mainView = mainView
        self.__moduleCommChannel = moduleCommChannel
        self.__scriptScope = self._createScriptScope(moduleCommChannel, multiModuleWindow,
                                                     moduleMainViews, moduleMainControllers)

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

    def _createScriptScope(self, moduleCommChannel, multiModuleWindow,
                          moduleMainViews, moduleMainControllers):
        """ Generates a scope of objects that are intended to be accessible by scripts. """

        #if not set(moduleMainViews.keys()) == set(moduleMainControllers.keys()):
        #    raise ValueError('moduleMainViews and moduleMainControllers do not have the same keys')

        scope = {}
        scope.update(getActionsScope())
        scope.update({
            'moduleCommChannel': moduleCommChannel,
            'mainWindow': multiModuleWindow,
            'controllers': DotMap(moduleMainControllers),
            'api': DotMap({key: controller.api
                           for key, controller in moduleMainControllers.items()
                           if hasattr(controller, 'api')})
        })

        #for moduleId in moduleMainViews.keys():
        #    scope['modules'][moduleId] = {
        #        'api': moduleMainControllers[moduleId].api
        #        'controller': moduleMainControllers[moduleId],
        #        #'view': moduleMainViews[moduleId]
        #    }

        return scope

    def closeEvent(self):
        self.__factory.closeAllCreatedControllers()


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
