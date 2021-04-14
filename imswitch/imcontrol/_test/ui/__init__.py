from imswitch.imcommon import prepareApp
from imswitch.imcommon.controller import ModuleCommunicationChannel
from imswitch.imcontrol._test import setupInfoBasic
from imswitch import imcontrol


def prepareUI():
    app = prepareApp()
    moduleCommChannel = ModuleCommunicationChannel()
    moduleCommChannel.register(imcontrol)
    mainView, _ = imcontrol.getMainViewAndController(moduleCommChannel,
                                                     overrideSetupInfo=setupInfoBasic)
    return app, mainView


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
