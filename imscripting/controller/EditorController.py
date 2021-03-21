import contextlib
import sys
import traceback
from io import StringIO

from .basecontrollers import ImScrWidgetController


@contextlib.contextmanager
def stdoutIO(stdout=None):
    old = sys.stdout
    if stdout is None:
        stdout = StringIO()
    sys.stdout = stdout
    yield stdout
    sys.stdout = old


class EditorController(ImScrWidgetController):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Connect EditorView signals
        self._widget.sigRunAllClicked.connect(self.runCode)
        self._widget.sigRunSelectedClicked.connect(self.runCode)

    def runCode(self, code):
        with stdoutIO() as s:
            try:
                exec(code, self._scriptScope)
            except:
                print(traceback.format_exc())

            self._widget.setOutput(s.getvalue())


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
