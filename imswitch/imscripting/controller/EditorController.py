import os

from imswitch.imcommon import constants
from imswitch.imscripting.model import ScriptExecutor
from imswitch.imscripting.view import guitools
from .basecontrollers import ImScrWidgetController


class EditorController(ImScrWidgetController):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.scriptExecutor = ScriptExecutor(self._scriptScope)

        self._scriptPaths = {}  # { editorViewInstanceID: filePath }
        self._unsavedScripts = {}  # { editorViewInstanceID: unsaved }

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
        self._widget.sigStopClicked.connect(self.scriptExecutor.terminate)
        self._widget.sigTextChanged.connect(self.textChanged)
        self._widget.sigInstanceCloseClicked.connect(self.instanceCloseClicked)

        # Basic setup
        self.newFile()

    def newFile(self):
        instance = self._widget.addEditor(_untitledFileName)
        self._scriptPaths[instance.getID()] = None
        self._unsavedScripts[instance.getID()] = False

    def openFile(self, scriptPath=None):
        if scriptPath is None:
            scriptPath = guitools.askForFilePath(
                self._widget, 'Open script', defaultFolder=_scriptsFolderPath, nameFilter='*.py'
            )
            if not scriptPath:
                return

        with open(scriptPath) as file:
            code = file.read()

        for existingInstanceID, existingScriptPath in self._scriptPaths.items():
            if scriptPath == existingScriptPath:
                # File already open
                self._widget.setCurrentInstanceByID(existingInstanceID)
                return

        instance = self._widget.addEditor(os.path.basename(scriptPath))
        instance.setText(code)
        self._scriptPaths[instance.getID()] = scriptPath
        self._unsavedScripts[instance.getID()] = False

    def saveFile(self):
        instance = self._widget.getCurrentInstance()
        scriptPath = self._scriptPaths[instance.getID()]
        if scriptPath is None:
            self.saveAsFile()
        else:
            with open(scriptPath, 'w') as file:
                file.write(instance.getText())
            self._widget.setEditorName(instance.getID(), os.path.basename(scriptPath))
            self._unsavedScripts[instance.getID()] = False

    def saveAsFile(self):
        instance = self._widget.getCurrentInstance()

        scriptPath = guitools.askForFilePath(
            self._widget, 'Save script', defaultFolder=_scriptsFolderPath, nameFilter='*.py',
            isSaving=True
        )
        if not scriptPath:
            return

        self._scriptPaths[instance.getID()] = scriptPath
        self.saveFile()

    def runCurrentCode(self, instanceID, code):
        self._commChannel.sigExecutionStarted.emit()
        self.scriptExecutor.execute(self._scriptPaths[instanceID], code)

    def textChanged(self, instanceID):
        if instanceID not in self._scriptPaths:
            return  # This happens when the file has not been fully loaded yet

        self._unsavedScripts[instanceID] = True
        self._widget.setEditorName(instanceID, f'{self.getScriptName(instanceID)}*')

    def instanceCloseClicked(self, instanceID):
        self._widget.closeInstance(instanceID)
        del self._scriptPaths[instanceID]
        del self._unsavedScripts[instanceID]

    def getScriptName(self, instanceID):
        scriptPath = self._scriptPaths[instanceID]
        if scriptPath is not None:
            return os.path.basename(scriptPath)
        else:
            return _untitledFileName


_untitledFileName = '(untitled)'
_scriptsFolderPath = os.path.join(constants.rootFolderPath, 'scripts')


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
