import os
import subprocess
import sys


def openFolderInOS(folderPath):
    """ Open a folder in the OS's default file browser. """
    try:
        if sys.platform == 'darwin':
            subprocess.check_call(['open', folderPath])
        elif sys.platform == 'linux':
            subprocess.check_call(['xdg-open', folderPath])
        elif sys.platform == 'win32':
            os.startfile(folderPath)
    except FileNotFoundError or subprocess.CalledProcessError as err:
        raise OSToolsError(err)


def restartSoftware(module='imswitch'):
    """ Restarts the software. """
    os.execv(sys.executable, ['"' + sys.executable + '"', '-m', module])


class OSToolsError(Exception):
    pass


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
