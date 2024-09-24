from imswitch import IS_HEADLESS
from imswitch.imcommon.controller import MainController
from .ImScrMainViewController import ImScrMainViewController
from .basecontrollers import ImScrWidgetControllerFactory

class ImScrMainController(MainController):
    """ Main controller of imscripting. """

    def __init__(self, mainView, moduleCommChannel, multiModuleWindowController,
                 moduleMainControllers):
        self.__mainView = mainView
        self.__moduleCommChannel = moduleCommChannel

        # List of Controllers for the GUI Widgets
        self.__factory = ImScrWidgetControllerFactory(
            None, None, self.__moduleCommChannel
        )
        self.mainViewController = self.__factory.createController(
            ImScrMainViewController, self.__mainView
        )

        # Connect signals from ModuleCommunicationChannel
        if IS_HEADLESS:
            
            return
        self.__mainView.sigClosing.connect(self.closeEvent)

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
