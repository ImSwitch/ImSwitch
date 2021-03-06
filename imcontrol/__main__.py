from imcommon import prepareApp, launchApp
from imcommon.controller import ModuleCommunicationChannel
import imcontrol


app = prepareApp()
moduleCommChannel = ModuleCommunicationChannel()
moduleCommChannel.register(imcontrol)
mainView, mainController = imcontrol.getMainViewAndController(moduleCommChannel)
launchApp(app, mainView, [mainController])

# Copyright (C) 2020, 2021 Staffan Al-Kadhimi, Xavier Casas, Andreas Boden
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
