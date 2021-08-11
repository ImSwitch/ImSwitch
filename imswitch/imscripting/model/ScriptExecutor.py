import os
import sys
import traceback
from io import StringIO
from time import strftime

from imswitch.imcommon.framework import Signal, SignalInterface, Thread, Worker
from .actions import getActionsScope


class ScriptExecutor(SignalInterface):
    """ Handles execution and state of scripts. """

    sigOutputAppended = Signal(str)  # (outputText)
    _sigExecute = Signal(str, str)  # (scriptPath, code)

    def __init__(self, scriptScope):
        super().__init__()
        self._executionWorker = ExecutionThread(scriptScope)
        self._executionWorker.sigOutputAppended.connect(self.sigOutputAppended)
        self._executionThread = Thread()
        self._executionWorker.moveToThread(self._executionThread)
        self._sigExecute.connect(self._executionWorker.execute)

    def execute(self, scriptPath, code):
        """ Executes the specified script code. scriptPath is the path to the
        script file if if exists, or None if the script has not been saved to a
        file. """
        self.terminate()
        self._executionThread.start()
        self._sigExecute.emit(scriptPath, code)

    def terminate(self):
        """ Terminates the currently running script. Does nothing if no script
        is running. """
        if self.isExecuting():
            print(f'\nTerminated script at {strftime("%Y-%m-%d %H:%M:%S")}')
            self._executionThread.terminate()

    def isExecuting(self):
        """ Returns whether a script is currently being executed. """
        return self._executionThread.isRunning() and self._executionWorker.isWorking()


class ExecutionThread(Worker):
    sigOutputAppended = Signal(str)  # (outputText)

    def __init__(self, scriptScope):
        super().__init__()
        self._scriptScope = scriptScope
        self._isWorking = False

    def execute(self, scriptPath, code):
        scriptScope = {}
        scriptScope.update(self._scriptScope)
        scriptScope.update(getActionsScope(scriptPath))

        self._isWorking = True
        oldStdout = sys.stdout
        oldStderr = sys.stderr
        try:
            outputIO = SignaledStringIO(self.sigOutputAppended)
            sys.stdout = outputIO
            sys.stderr = outputIO
            os.chdir(os.path.dirname(scriptPath))  # This is a permanent change, but should be fine

            print(f'Started script at {strftime("%Y-%m-%d %H:%M:%S")}\n')
            try:
                exec(code, scriptScope)
            except Exception:
                print(traceback.format_exc())
            print(f'\nFinished script at {strftime("%Y-%m-%d %H:%M:%S")}')
        finally:
            sys.stdout = oldStdout
            sys.stderr = oldStderr
            self._isWorking = False

    def isWorking(self):
        return self._isWorking


class SignaledStringIO(StringIO):
    def __init__(self, signal):
        super().__init__()
        self._signal = signal

    def write(self, text):
        super().write(text)
        self._signal.emit(text)


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
