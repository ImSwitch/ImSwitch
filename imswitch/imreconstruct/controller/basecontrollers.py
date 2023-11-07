from imswitch.imcommon.controller import WidgetController, WidgetControllerFactory


class ImRecWidgetControllerFactory(WidgetControllerFactory):
    """ Factory class for creating a ImRecWidgetController object. """

    def __init__(self, commChannel, moduleCommChannel):
        super().__init__(commChannel=commChannel, moduleCommChannel=moduleCommChannel)


class ImRecWidgetController(WidgetController):
    """ Superclass for all ImRecWidgetController. """

    def __init__(self, commChannel, *args, **kwargs):
        # Protected attributes, which should only be accessed from controller and its subclasses
        self._commChannel = commChannel

        # Init superclass
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
