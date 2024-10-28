from imswitch import imcontrol
from imswitch.imcommon import prepareApp, launchApp
from imswitch.imcommon.controller import ModuleCommunicationChannel
from imswitch import IS_HEADLESS
import os

if IS_HEADLESS:
    os.environ["DISPLAY"] = ":0"
    os.environ["QT_QPA_PLATFORM"] = "offscreen"


def main():
    global app
    app = prepareApp()
    moduleCommChannel = ModuleCommunicationChannel()
    moduleCommChannel.register(imcontrol)
    mainView, mainController = imcontrol.getMainViewAndController(moduleCommChannel)
    launchApp(app, mainView, [mainController])


if __name__ == '__main__':
    main()

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
