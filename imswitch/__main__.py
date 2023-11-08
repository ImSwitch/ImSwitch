import importlib
import traceback

import imswitch
from imswitch.imcommon import prepareApp, launchApp
from imswitch.imcommon.controller import ModuleCommunicationChannel, MultiModuleWindowController
from imswitch.imcommon.model import modulesconfigtools, pythontools, initLogger
from imswitch.imcommon.view import MultiModuleWindow, ModuleLoadErrorView

# FIXME: Add to configuration file
global IS_HEADLESS 
IS_HEADLESS = False
def main():
    logger = initLogger('main')
    logger.info(f'Starting ImSwitch {imswitch.__version__}')    

    app = prepareApp()
    enabledModuleIds = modulesconfigtools.getEnabledModuleIds()
    
    if 'imscripting' in enabledModuleIds:
        # Ensure th at imscripting is added last
        
        enabledModuleIds.append(enabledModuleIds.pop(enabledModuleIds.index('imscripting')))


    modulePkgs = [importlib.import_module(pythontools.joinModulePath('imswitch', moduleId))
                  for moduleId in enabledModuleIds]

    moduleCommChannel = ModuleCommunicationChannel()

    if not IS_HEADLESS:
        multiModuleWindow = MultiModuleWindow('ImSwitch')
        multiModuleWindowController = MultiModuleWindowController.create(
            multiModuleWindow, moduleCommChannel
        )
        multiModuleWindow.show(showLoadingScreen=True)
    else: 
        multiModuleWindow = None
        multiModuleWindowController = None
    
    app.processEvents()  # Draw window before continuing

    # Register modules
    for modulePkg in modulePkgs:
        moduleCommChannel.register(modulePkg)

    # Load modules
    moduleMainControllers = dict()

    for i, modulePkg in enumerate(modulePkgs):
        moduleId = modulePkg.__name__
        moduleId = moduleId[moduleId.rindex('.') + 1:]  # E.g. "imswitch.imcontrol" -> "imcontrol"

        # The displayed module name will be the module's __title__, or alternatively its ID if
        # __title__ is not set
        moduleName = modulePkg.__title__ if hasattr(modulePkg, '__title__') else moduleId

        try:
            view, controller = modulePkg.getMainViewAndController(
                moduleCommChannel=moduleCommChannel,
                multiModuleWindowController=multiModuleWindowController,
                moduleMainControllers=moduleMainControllers
            )
        except Exception as e:
            logger.error(f'Failed to initialize module {moduleId}')
            logger.error(traceback.format_exc())
            moduleCommChannel.unregister(modulePkg)
            if not IS_HEADLESS: multiModuleWindow.addModule(moduleId, moduleName, ModuleLoadErrorView(e))
        else:
            # Add module to window
            if not IS_HEADLESS: multiModuleWindow.addModule(moduleId, moduleName, view)
            moduleMainControllers[moduleId] = controller

            # Update loading progress
            if not IS_HEADLESS: multiModuleWindow.updateLoadingProgress(i / len(modulePkgs))
            app.processEvents()  # Draw window before continuing

    launchApp(app, multiModuleWindow, moduleMainControllers.values())


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
