from .ConsoleController import ConsoleController
try:
    from PyQt5 import Qsci
    from .EditorController import EditorController
    isQsciAvailable = True
except:
    isQsciAvailable = False
    
from .FilesController import FilesController
from .OutputController import OutputController
from .basecontrollers import ImScrWidgetController
from imswitch import IS_HEADLESS

class ImScrMainViewController(ImScrWidgetController):
    """ Connected to ImScrMainView. """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

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
