import glob
from sys import platform
# used to be, but actions will replace this with the current release TAG -> >2.1.0
__version__ = "2.1.0"
__httpport__ = 8001
__ssl__ = True

IS_HEADLESS = False
DEFAULT_SETUP_FILE = None
DEFAULT_CONFIG_PATH = None
DEFAULT_DATA_PATH = None

# Copyright (C) 2020-2023 ImSwitch developers
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
