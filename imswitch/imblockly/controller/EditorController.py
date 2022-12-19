import os

from imswitch.imcommon.model import dirtools
from imswitch.imblockly.model import ScriptExecutor, ScriptStore, ScriptEntry
from imswitch.imblockly.view import guitools
from .basecontrollers import ImScrWidgetController


class EditorController(ImScrWidgetController):
    """ Connected to EditorView. """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.scriptExecutor = ScriptExecutor(self._scriptScope)
        self.scriptStore = ScriptStore()
        self.loadingFile = False

        # Connect ScriptExecutor signals
        self.scriptExecutor.sigOutputAppended.connect(self._commChannel.sigOutputAppended)

        # Connect CommunicationChannel signals
        self._commChannel.sigNewFile.connect(self.newFile)
        self._commChannel.sigOpenFile.connect(self.openFile)
        self._commChannel.sigOpenFileFromPath.connect(self.openFile)
        self._commChannel.sigSaveFile.connect(self.saveFile)
        self._commChannel.sigSaveAsFile.connect(self.saveAsFile)

        # Connect EditorView signals
        self._widget.sigRunAllClicked.connect(self.runCurrentCode)
        self._widget.sigRunSelectedClicked.connect(self.runCurrentCode)
        self._widget.sigStopClicked.connect(self.stopExecution)
        self._widget.sigTextChanged.connect(self.textChanged)
        self._widget.sigInstanceCloseClicked.connect(self.instanceCloseClicked)

        # Basic setup
        self.newFile()

    def newFile(self):
        """ Creates a new file. """
        instance = self._widget.addEditor(_untitledFileName)
        self.scriptStore[instance.getID()] = ScriptEntry(filePath=None)

    def openFile(self, scriptPath=None):
        """ Opens an existing file. If scriptPath is None, the user will
        specify which file will be opened. """

        if scriptPath is None:
            scriptPath = guitools.askForFilePath(
                self._widget, 'Open script', defaultFolder=_scriptsFolderPath, nameFilter='*.py'
            )
            if not scriptPath:
                return

        for existingInstanceID, existingEntry in self.scriptStore:
            if scriptPath == existingEntry.filePath:
                # File already open
                self._widget.setCurrentInstanceByID(existingInstanceID)
                return

        scriptEntry = ScriptEntry.loadFromFile(scriptPath)
        instance = self._widget.addEditor(os.path.basename(scriptPath))

        self.loadingFile = True
        try:
            instance.setText(scriptEntry.code)
        finally:
            self.loadingFile = False

        self.scriptStore[instance.getID()] = scriptEntry

    def saveFile(self):
        """ Saves the current file. If it's not already saved to a file, the
        user will specify the path to save to. """
        instance = self._widget.getCurrentInstance()
        scriptEntry = self.scriptStore[instance.getID()]
        if scriptEntry.isSavedToFile():
            scriptEntry.code = instance.getText()
            scriptEntry.save()
            self._widget.setEditorName(instance.getID(), os.path.basename(scriptEntry.filePath))
        else:
            self.saveAsFile()

    def saveAsFile(self):
        """ Saves the current file to the path specified by the user. """
        instance = self._widget.getCurrentInstance()

        scriptPath = guitools.askForFilePath(
            self._widget, 'Save script', defaultFolder=_scriptsFolderPath, nameFilter='*.py',
            isSaving=True
        )
        if not scriptPath:
            return

        self.scriptStore[instance.getID()].filePath = scriptPath
        self.saveFile()

    def runCurrentCode(self, instanceID, code):
        """ Executes the specified code. instanceID is the ID of the instance
        that contains the code. """

        if self.scriptExecutor.isExecuting():
            if not guitools.askYesNoQuestion(self._widget,
                                             'Warning: Already Executing',
                                             'A script is already running; it will be terminated if'
                                             ' you proceed. Do you want to proceed?'):
                return

        self._commChannel.sigExecutionStarted.emit()
        self.scriptExecutor.execute(self.scriptStore[instanceID].filePath, code)

    def stopExecution(self):
        """ Stops the currently running script. Does nothing if no script is
        running. """

        if not self.scriptExecutor.isExecuting():
            return

        if not guitools.askYesNoQuestion(self._widget,
                                         'Stop execution?',
                                         'Are you sure that you want to stop the script?'):
            return

        self.scriptExecutor.terminate()

    def textChanged(self, instanceID):
        if self.loadingFile or instanceID not in self.scriptStore:
            return  # This happens when the file has not been fully loaded yet

        self.scriptStore[instanceID].unsaved = True
        self._widget.setEditorName(instanceID, f'{self.getScriptName(instanceID)}*')

    def instanceCloseClicked(self, instanceID):
        if not self.verifyNotUnsaved(instanceID):
            return

        self._widget.closeInstance(instanceID)
        del self.scriptStore[instanceID]

    def verifyNotUnsaved(self, instanceID):
        if self.scriptStore[instanceID].unsaved:
            return guitools.askYesNoQuestion(self._widget,
                                             'Warning: Unsaved Changes',
                                             'Are you sure you want to close the file? There are'
                                             ' unsaved changes that will be lost.')

        return True

    def getScriptName(self, instanceID):
        """ Returns the name that should be used for the editor with the
        specified instance ID. """
        scriptEntry = self.scriptStore[instanceID]
        if scriptEntry.isSavedToFile():
            return os.path.basename(scriptEntry.filePath)
        else:
            return _untitledFileName


_untitledFileName = '(untitled)'
_scriptsFolderPath = os.path.join(dirtools.UserFileDirs.Root, 'scripts')


# Copyright (C) 2020-2021 ImSwitch developers
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
