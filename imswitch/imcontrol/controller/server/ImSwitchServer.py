import Pyro5
import Pyro5.server
from imswitch.imcommon.framework import Worker
from imswitch.imcommon.model import initLogger
from ._serialize import register_serializers
from useq import MDASequence
import time
import numpy as np


class ImSwitchServer(Worker):

    def __init__(self, channel, setupInfo):
        super().__init__()

        self.__logger = initLogger(self, tryInheritParent=True)
        self._channel = channel
        self._name = setupInfo.pyroServerInfo.name
        self._host = setupInfo.pyroServerInfo.host
        self._port = setupInfo.pyroServerInfo.port

        self._paused = False
        self._canceled = False

    def run(self):
        self.__logger.debug("Started server with URI -> PYRO:" + self._name + "@" + self._host + ":" + str(self._port))
        try:
            Pyro5.config.SERIALIZER = "msgpack"

            register_serializers()

            Pyro5.server.serve(
                {self: self._name},
                use_ns=False,
                host=self._host,
                port=self._port,
            )

        except:
            self.__loger.error("Couldn't start server.")
        self.__logger.debug("Loop Finished")

    def stop(self):
        self._daemon.shutdown()

    @Pyro5.server.expose
    def exec(self, module, func, params):
        self._channel.sigBroadcast.emit(module, func, params)

    @Pyro5.server.expose
    def get_image(self, detectorName=None) -> np.ndarray:
        return self._channel.get_image(detectorName)


# Copyright (C) 2021, Talley Lambert
# All rights reserved.

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
