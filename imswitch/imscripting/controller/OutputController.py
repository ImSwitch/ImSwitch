import re
from .basecontrollers import ImScrWidgetController


# ANSI escape sequence regex. Source: https://stackoverflow.com/a/38662876
ansiEscape = re.compile(r'(?:\x1B[@-_]|[\x80-\x9F])[0-?]*[ -/]*[@-~]')


class OutputController(ImScrWidgetController):
    """ Connected to OutputView. """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Connect CommunicationChannel signals
        self._commChannel.sigExecutionStarted.connect(self.executionStarted)
        self._commChannel.sigOutputAppended.connect(self.outputAppended)

    def executionStarted(self):
        self._widget.clearText()

    def outputAppended(self, outputText):
        textWithoutANSIEscape = ansiEscape.sub('', outputText)
        self._widget.appendText(textWithoutANSIEscape)


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
