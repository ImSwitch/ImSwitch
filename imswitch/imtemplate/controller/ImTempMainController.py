from imswitch.imcommon.controller import MainController
from .CommunicationChannel import CommunicationChannel
from .basecontrollers import ImTempWidgetControllerFactory


class ImTempMainController(MainController):
    def __init__(self, mainView, moduleCommChannel):
        self.__mainView = mainView
        self.__moduleCommChannel = moduleCommChannel

        # Connect view signals
        self.__mainView.sigClosing.connect(self.closeEvent)

        # Init communication channel and master controller
        self.__commChannel = CommunicationChannel()

        # List of Controllers for the GUI Widgets
        self.__factory = ImTempWidgetControllerFactory(
            self.__commChannel, self.__moduleCommChannel
        )


    def closeEvent(self):
        self.__factory.closeAllCreatedControllers()


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