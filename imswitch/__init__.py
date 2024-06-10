import glob
from sys import platform
# used to be, but actions will replace this with the current release TAG ->1.2.9
__version__ = "1.2.9"
__httpport__ = 8002
__ssl__ = False

if platform == "linux" or platform == "linux2":
    IS_HEADLESS = True
else:
    IS_HEADLESS = False


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
