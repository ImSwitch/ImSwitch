import traceback

from imcommon import prepareApp, launchApp
from imcommon.controller import ModuleCommunicationChannel
from imcommon.view import MultiModuleWindow

import imcontrol
import imreconstruct
import imscripting


modules = {
    imcontrol: 'Hardware Control',
    imreconstruct: 'Image Reconstruction',
    imscripting: 'Scripting'  # Must be last!
}

app = prepareApp()
moduleCommChannel = ModuleCommunicationChannel()
multiModuleWindow = MultiModuleWindow('ImSwitch')
moduleMainViews = dict()
moduleMainControllers = dict()

for modulePackage in modules.keys():
    moduleCommChannel.register(modulePackage)

for modulePackage, moduleName in modules.items():
    try:
        view, controller = modulePackage.getMainViewAndController(
            moduleCommChannel=moduleCommChannel,
            multiModuleWindow=multiModuleWindow,
            moduleMainViews=moduleMainViews,
            moduleMainControllers=moduleMainControllers
        )
    except:
        print(f'Failed to initialize module {modulePackage.__name__}')
        print(traceback.format_exc())
        moduleCommChannel.unregister(modulePackage)
    else:
        multiModuleWindow.addModule(modulePackage.__name__, moduleName, view)
        moduleMainViews[modulePackage.__name__] = view
        moduleMainControllers[modulePackage.__name__] = controller

launchApp(app, multiModuleWindow, moduleMainControllers.values())


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
