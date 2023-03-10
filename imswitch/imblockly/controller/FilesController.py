import mimetypes
import os

from send2trash import send2trash

from imswitch.imcommon.model import dirtools, ostools
from imswitch.imblockly.view import guitools
from .basecontrollers import ImScrWidgetController


class FilesController(ImScrWidgetController):
    """ Connected to FilesView. """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._rootPath = os.path.join(dirtools.UserFileDirs.Root, 'scripts')
        self._widget.setRootPath(self._rootPath)

        # Connect FilesView signals
        self._widget.sigNewFileClicked.connect(self._commChannel.sigNewFile)
        self._widget.sigItemDoubleClicked.connect(self.checkAndOpenItem)
        self._widget.sigItemDeleteClicked.connect(self.deleteItem)
        self._widget.sigRootPathSubmit.connect(self.setRootPath)
        self._widget.sigBrowseClicked.connect(self.browse)
        self._widget.sigOpenRootInOSClicked.connect(self.openRootInOS)

    def checkAndOpenItem(self, itemPath):
        mime, _ = mimetypes.guess_type(itemPath)
        if mime is not None and mime.startswith('text/'):  # Only open text-like files
            self._commChannel.sigOpenFileFromPath.emit(itemPath)

    def deleteItem(self, itemPath):
        if guitools.askYesNoQuestion(self._widget,
                                     'Delete?',
                                     f'Are you sure you want to delete'
                                     f' "{os.path.basename(itemPath)}"? It will be moved to your'
                                     f' system\'s trash directory if possible.'):
            send2trash(os.path.abspath(itemPath))

    def setRootPath(self, rootPath):
        if os.path.isdir(rootPath):
            self._rootPath = rootPath
            self._widget.setRootPath(rootPath)

    def browse(self):
        rootPath = guitools.askForFolderPath(self._widget, defaultFolder=self._rootPath)
        if rootPath:
            self.setRootPath(rootPath)

    def openRootInOS(self):
        ostools.openFolderInOS(self._rootPath)


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
