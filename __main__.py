import traceback

from imcommon import prepareApp, launchApp
from imcommon.controller import ModuleCommunicationChannel
from imcommon.view import MultiModuleWindow

import imcontrol
import imreconstruct


modulePackages = [imcontrol, imreconstruct]
moduleNames = {
    imcontrol: 'Hardware Control',
    imreconstruct: 'Image Reconstruction'
}

app = prepareApp()
moduleCommChannel = ModuleCommunicationChannel()
multiModuleWindow = MultiModuleWindow('ImSwitch')
mainControllers = set()

for modulePackage in modulePackages:
    moduleCommChannel.register(modulePackage)

for modulePackage in modulePackages:
    view = None
    try:
        view, controller = modulePackage.getMainViewAndController(moduleCommChannel)
        multiModuleWindow.addModule(moduleNames[modulePackage], view)
        mainControllers.add(controller)
    except:
        print(f'Failed to initialize module {modulePackage.__name__}')
        print(traceback.format_exc())
        moduleCommChannel.unregister(modulePackage)
        if view is not None:
            view.deleteLater()

launchApp(app, multiModuleWindow, mainControllers)
