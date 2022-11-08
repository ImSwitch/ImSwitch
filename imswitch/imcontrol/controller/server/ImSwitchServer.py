import Pyro5
import Pyro5.server
from imswitch.imcommon.framework import Worker
from imswitch.imcommon.model import initLogger
from ._serialize import register_serializers
from fastapi import FastAPI
import uvicorn
import inspect

app = FastAPI()


class ImSwitchServer(Worker):

    def __init__(self, api, setupInfo):
        super().__init__()

        self.__logger = initLogger(self, tryInheritParent=True)
        self._api = api
        self._name = setupInfo.pyroServerInfo.name
        self._host = setupInfo.pyroServerInfo.host
        self._port = setupInfo.pyroServerInfo.port

        self._paused = False
        self._canceled = False

    def run(self):
        self.createAPI()
        uvicorn.run(app)
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

    @app.get("/")
    def createAPI(self):
        api_dict = self._api._asdict()
        functions = api_dict.keys()

        def includeAPI(str, func):
            @app.get(str)
            def wrapper(*args, **kwargs):
                return func(*args, **kwargs)

            return wrapper

        def includePyro(func):
            @Pyro5.server.expose
            def wrapper(*args, **kwargs):
                func.apply_defaults()
                return func

            return wrapper

        for f in functions:
            func = api_dict[f]
            self.__logger.debug(inspect.signature(inspect.unwrap(func)))
            module = inspect.unwrap(func).__module__.split('.')[-1]
            self.func = includePyro(includeAPI("/"+module+"/"+f, func))


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
