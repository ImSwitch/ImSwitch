from .basecontrollers import ImScrWidgetController
from .ConsoleController import ConsoleController
from .EditorController import EditorController
from .FilesController import FilesController
from .OutputController import OutputController


class ImScrMainViewController(ImScrWidgetController):
    """ Connected to ImScrMainView. """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.filesController = self._factory.createController(FilesController, self._widget.files)
        self.editorController = self._factory.createController(EditorController, self._widget.editor)
        self.consoleController = self._factory.createController(ConsoleController, self._widget.console)
        self.outputController = self._factory.createController(OutputController, self._widget.output)

        # Connect signals
        self._widget.newFileAction.triggered.connect(self._commChannel.sigNewFile)
        self._widget.openFileAction.triggered.connect(self._commChannel.sigOpenFile)
        self._widget.saveFileAction.triggered.connect(self._commChannel.sigSaveFile)
        self._widget.saveAsFileAction.triggered.connect(self._commChannel.sigSaveAsFile)


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
