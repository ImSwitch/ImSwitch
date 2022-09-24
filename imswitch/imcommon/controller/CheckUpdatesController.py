import os
import traceback

import requests
from luddite import get_version_pypi
from packaging import version
import subprocess


import imswitch
from imswitch.imcommon.framework import Signal, Thread
from imswitch.imcommon.model import initLogger
from .basecontrollers import WidgetController


class CheckUpdatesController(WidgetController):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__logger = initLogger(self)

        self.thread = CheckUpdatesThread()
        self.thread.sigFailed.connect(self._widget.showFailed)
        self.thread.sigNoUpdate.connect(self._widget.showNoUpdateAvailable)
        self.thread.sigNewVersionPyInstaller.connect(self._widget.showPyInstallerUpdate)
        self.thread.sigNewVersionPyPI.connect(self._widget.showPyPIUpdate)

    def __del__(self):
        self.thread.quit()
        self.thread.wait()
        if hasattr(super(), '__del__'):
            super().__del__()

    def checkForUpdates(self):
        """ Check for updates on a separate thread. """

        if self.thread.isRunning():
            self.thread.quit()
            self.thread.wait()

        self._widget.resetUpdateInfo()
        self.thread.start()


class CheckUpdatesThread(Thread):
    sigFailed = Signal()
    sigNoUpdate = Signal()
    sigNewVersionPyInstaller = Signal(str)  # (latestVersion)
    sigNewVersionPyPI = Signal(str)  # (latestVersion)

    def __init__(self):
        super().__init__()
        self.__logger = initLogger(self, tryInheritParent=True)

    def run(self):
        currentVersion = imswitch.__version__
        try:
            if 'IMSWITCH_IS_BUNDLE' in os.environ and os.environ['IMSWITCH_IS_BUNDLE'] == '1':
                # Installed from bundle - check GitHub
                releaseResponse = requests.get(
                    'https://api.github.com/repos/openUC2/ImSwitch/releases/latest'
                )
                latestVersion = releaseResponse.json()['tag_name'].lstrip('v')
                latestVersionDate = releaseResponse.json()['published_at'].split('T')[0]
                
                if version.parse(latestVersion) > version.parse(currentVersion):
                    self.sigNewVersionPyInstaller.emit(latestVersion)
                else:
                    self.sigNoUpdate.emit()
            else:
                # Not installed from bundle - check PyPI
                latestVersion = get_version_pypi('ImSwitch')
                if version.parse(latestVersion) > version.parse(currentVersion):
                    self.sigNewVersionPyPI.emit(latestVersion)
                else:
                    self.sigNoUpdate.emit()
        except Exception:
            self.__logger.warning(traceback.format_exc())
            self.sigFailed.emit()
            
    def getCurrentCommitDate(self):
        return str(subprocess.check_output(['git', 'log', '-n', '1', '--pretty=tformat:%h-%ad', '--date=short']).strip()).split("-")[-3:]



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
