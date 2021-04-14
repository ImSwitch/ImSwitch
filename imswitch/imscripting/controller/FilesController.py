import mimetypes
import os

from imswitch.imcommon import constants
from imswitch.imcommon.model import osutils
from imswitch.imscripting.view import guitools
from .basecontrollers import ImScrWidgetController


class FilesController(ImScrWidgetController):
    """ Connected to FilesView. """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._rootPath = os.path.join(constants.rootFolderPath, 'scripts')
        self._widget.setRootPath(self._rootPath)

        # Connect FilesView signals
        self._widget.sigItemDoubleClicked.connect(self.checkAndOpenItem)
        self._widget.sigRootPathSubmit.connect(self.setRootPath)
        self._widget.sigBrowseClicked.connect(self.browse)
        self._widget.sigOpenRootInOSClicked.connect(self.openRootInOS)

    def checkAndOpenItem(self, itemPath):
        mime, _ = mimetypes.guess_type(itemPath)
        if mime is not None and mime.startswith('text/'):  # Only open text-like files
            self._commChannel.sigOpenFileFromPath.emit(itemPath)

    def setRootPath(self, rootPath):
        if os.path.isdir(rootPath):
            self._rootPath = rootPath
            self._widget.setRootPath(rootPath)

    def browse(self):
        rootPath = guitools.askForFolderPath(self._widget, defaultFolder=self._rootPath)
        if rootPath:
            self.setRootPath(rootPath)

    def openRootInOS(self):
        osutils.openFolderInOS(self._rootPath)


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
