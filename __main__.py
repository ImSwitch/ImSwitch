import traceback

from imcommon import prepareApp, launchApp
from imcommon.controller import ModuleCommunicationChannel
from imcommon.view import MultiModuleWindow

import imcontrol
import imreconstruct


modules = {
    imcontrol: 'Hardware Control',
    imreconstruct: 'Image Reconstruction'
}

app = prepareApp()
moduleCommChannel = ModuleCommunicationChannel()
multiModuleWindow = MultiModuleWindow('ImSwitch')
mainControllers = set()

for modulePackage in modules.keys():
    moduleCommChannel.register(modulePackage)

for modulePackage, moduleName in modules.items():
    try:
        view, controller = modulePackage.getMainViewAndController(moduleCommChannel)
    except:
        print(f'Failed to initialize module {modulePackage.__name__}')
        print(traceback.format_exc())
        moduleCommChannel.unregister(modulePackage)
    else:
        multiModuleWindow.addModule(moduleName, view)
        mainControllers.add(controller)

launchApp(app, multiModuleWindow, mainControllers)

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
