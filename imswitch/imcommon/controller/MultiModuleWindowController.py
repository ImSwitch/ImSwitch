from imswitch.imcommon.view import guitools
from imswitch.imcommon.model import dirtools, modulesconfigtools, ostools, APIExport
from .basecontrollers import WidgetController
from .CheckUpdatesController import CheckUpdatesController
from .PickModulesController import PickModulesController


class MultiModuleWindowController(WidgetController):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.checkUpdatesController = self._factory.createController(CheckUpdatesController, self._widget.checkUpdatesDialog)

        self._moduleIdNameMap = {}

        # Connect signals
        self._widget.sigPickModules.connect(self.pickModules)
        self._widget.sigOpenUserDir.connect(self.openUserDir)
        self._widget.sigCheckUpdates.connect(self.checkUpdates)

        self._widget.sigModuleAdded.connect(self.moduleAdded)

    def pickModules(self):
        """ Let the user change which modules are active. """

        self.pickModulesController.setModules(modulesconfigtools.getAvailableModules())
        self.pickModulesController.setSelectedModules(modulesconfigtools.getEnabledModuleIds())
        if not self._widget.showPickModulesDialogBlocking():
            return
        moduleIds = self.pickModulesController.getSelectedModules()
        if not moduleIds:
            return

        proceed = guitools.askYesNoQuestion(self._widget, 'Warning',
                                            'The software will restart. Continue?')
        if not proceed:
            return

        modulesconfigtools.setEnabledModuleIds(moduleIds)
        ostools.restartSoftware()

    def openUserDir(self):
        """ Shows the user files directory in system file explorer. """
        ostools.openFolderInOS(dirtools.UserFileDirs.Root)

    def checkUpdates(self):
        """ Checks if there are any updates to ImSwitch available and notifies
        the user. """
        self.checkUpdatesController.checkForUpdates()
        self._widget.showCheckUpdatesDialogBlocking()

    def moduleAdded(self, moduleId, moduleName):
        self._moduleIdNameMap[moduleId] = moduleName

    @APIExport
    def setCurrentModule(self, moduleId):
        """ Sets the currently displayed module to the module with the
        specified ID (e.g. "imcontrol"). """
        moduleName = self._moduleIdNameMap[moduleId]
        self._widget.setSelectedModule(moduleName)
