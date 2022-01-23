import Pyro5.server
from imswitch.imcommon.model import initLogger
from useq import MDAEvent, MDASequence


class ImSwitchServer(object):

    def __init__(self, channel):
        self._channel = channel
        self.__logger = initLogger(self, tryInheritParent=True)

    @Pyro5.server.expose
    def receive(self, request):
        self.__logger.info(request)

    @Pyro5.server.expose
    def run_mda(self, sequence: MDASequence) -> None:
        pass


# Copyright (C) 2020-2022 ImSwitch developers
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