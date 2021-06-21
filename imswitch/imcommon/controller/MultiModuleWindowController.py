from imswitch.imcommon.view import guitools
from imswitch.imcommon.model import modulesconfigtools, ostools, APIExport
from .basecontrollers import WidgetController


class MultiModuleWindowController(WidgetController):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._moduleIdNameMap = {}

        # Connect signals
        self._widget.sigPickModules.connect(self.pickModules)
        self._widget.sigModuleAdded.connect(self.moduleAdded)

    def pickModules(self):
        """ Let the user change which modules are active. """

        moduleIds = guitools.PickModulesDialog.showAndWaitForResult(
            parent=self._widget, moduleIdsAndNamesDict=modulesconfigtools.getAvailableModules(),
            preselectedModules=modulesconfigtools.getEnabledModuleIds()
        )
        if moduleIds is None:
            return

        proceed = guitools.askYesNoQuestion(self._widget, 'Warning',
                                            'The software will restart. Continue?')
        if not proceed:
            return

        modulesconfigtools.setEnabledModuleIds(moduleIds)
        ostools.restartSoftware()

    def moduleAdded(self, moduleId, moduleName):
        self._moduleIdNameMap[moduleId] = moduleName

    @APIExport
    def setCurrentModule(self, moduleId):
        """ Sets the currently displayed module to the module with the
        specified ID (e.g. "imcontrol"). """
        moduleName = self._moduleIdNameMap[moduleId]
        self._widget.setSelectedModule(moduleName)
