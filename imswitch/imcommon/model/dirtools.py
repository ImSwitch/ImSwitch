import os
import platform
from abc import ABC
from pathlib import Path
from shutil import copy2

import imswitch

from xdg import xdg_config_home, xdg_data_home


def _getWindowsDir():
    try:
        import ctypes.wintypes
        CSIDL_PERSONAL = 5  # Documents
        SHGFP_TYPE_CURRENT = 0  # Current value

        buf = ctypes.create_unicode_buffer(ctypes.wintypes.MAX_PATH)
        ctypes.windll.shell32.SHGetFolderPathW(0, CSIDL_PERSONAL, 0,
                                               SHGFP_TYPE_CURRENT, buf)

        return Path(buf.value)
    except ImportError:
        pass
    # TOOD: How can we ensure that configuration files are updated automatically..


def _getImSwitchDir(config: bool = False) -> str:
    """Returns an XDG compatible data/config folder on Linux, the user's
    documents folder on Windows or their home folder if they are using another
    operating system.

    """
    if platform.system() == 'Linux':
        # return XDG compatible directory,
        # see https://www.freedesktop.org/wiki/Specifications/basedir-spec/
        if config:
            return xdg_config_home() / 'ImSwitch'
        else:
            return xdg_data_home() / 'ImSwitch'

    else:
        # on any other OS put data and configs into same folder
        if platform.system(
        ) == 'Windows':  # Windows system, try to return documents directory
            # TODO why would these files not go into .AppData\Roaming?
            # (or whatever the right windows location is)
            basepath = _getWindowsDir()
        else:
            # TODO make case for macOS and return recommended paths
            basepath = Path('~').expanduser()

        if config:
            return basepath / 'ImSwitch/config'
        else:
            return basepath / 'ImSwitch/data'


def getImSwitchConfigDir():
    return _getImSwitchDir(config=True)


def getImSwitchDataDir():
    return _getImSwitchDir(config=False)


_baseDataFilesDir = Path(imswitch.__file__).resolve() / '_data'
_baseUserConfigFilesDir = getImSwitchConfigDir()
_baseUserDataFilesDir = getImSwitchDataDir()


def initUserFilesIfNeeded() -> None:
    """ Initializes all directories that will be used to store user data and
    copies example files. """

    # Initialize directories
    for userDataFileDir in UserDataFileDirs.list():
        os.makedirs(userDataFileDir, exist_ok=True)

    for userConfigFileDir in UserConfigFileDirs.list():
        os.makedirs(userConfigFileDir, exist_ok=True)

    # Copy default files to user directories
    UserConfigFileDirs.copyDefaults()
    UserDataFileDirs.copyDefaults()


class FileDirs(ABC):
    """ Base class for directory catalog classes. """

    DefaultDataPath: Path

    @classmethod
    def list(cls):
        """ Returns all directories in the catalog. """
        return [
            cls.__dict__.get(name) for name in dir(cls)
            if not callable(getattr(cls, name)) and not name.startswith('_')
        ]

    @classmethod
    def copyDefaults(cls):
        """Copy default files to user directories."""

        for filePath in cls.DefaultDataPath.glob('**/*'):
            if not filePath.is_file():
                continue

            relativeFilePath = filePath.relative_to(cls.DefaultDataPath)
            copyDestination = cls.Root / relativeFilePath

            if os.path.exists(copyDestination):
                continue  # Don't overwrite existing files

            try:
                os.makedirs(copyDestination.parent, exist_ok=True)
            # Directory path (or part of it) exists as a file
            except FileExistsError:
                continue

            copy2(filePath, copyDestination)


class DataFileDirs(FileDirs):
    """ Catalog of directories that contain program data/library/resource
    files. """
    Root = _baseDataFilesDir
    Libs = _baseDataFilesDir / 'libs'
    UserDefaults = _baseDataFilesDir / 'user_defaults'
    Data = _baseDataFilesDir / 'user_defaults/data'
    Configs = _baseDataFilesDir / 'user_defaults/configs'
    Scripts = _baseDataFilesDir / 'user_defaults/data/scripts'

    @classmethod
    def copyDefaults(cls):
        # do nothing as this class represents the defaults itself
        pass


class UserDataFileDirs(FileDirs):
    """ Catalog of directories that contain user data files. """
    DefaultDataPath = DataFileDirs.Data
    Root = _baseUserDataFilesDir


class UserConfigFileDirs(FileDirs):
    """ Catalog of directories that contain user configuration files. """
    DefaultDataPath = DataFileDirs.Configs
    Root = _baseUserConfigFilesDir


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
