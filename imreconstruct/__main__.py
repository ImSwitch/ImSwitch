from imcommon import prepareApp, launchApp
from imcommon.controller import ModuleCommunicationChannel
import imreconstruct


app = prepareApp()
moduleCommChannel = ModuleCommunicationChannel()
moduleCommChannel.register(imreconstruct)
mainView, mainController = imreconstruct.getMainViewAndController(moduleCommChannel)
launchApp(app, mainView, [mainController])
