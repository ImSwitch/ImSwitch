import os
import traceback

from imcommon import prepareApp, launchApp
from imcommon.controller import ModuleCommunicationChannel
from imcommon.view import MultiModuleWindow

import imcontrol
import imreconstruct


os.environ['NAPARI_ASYNC'] = '1'
os.environ['NAPARI_OCTREE'] = '0'

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
