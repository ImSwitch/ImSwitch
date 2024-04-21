import threading
import Pyro5
import Pyro5.server
from Pyro5.api import expose

from imswitch.imcommon.framework import Worker
from imswitch.imcommon.model import initLogger
from ._serialize import register_serializers
from fastapi.middleware.cors import CORSMiddleware
from io import BytesIO
import numpy as np
from PIL import Image
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
import imswitch
import uvicorn
from functools import wraps
import os
import socket 
import time
import zeroconf
from zeroconf import ServiceInfo, Zeroconf
import socket
from fastapi.middleware.cors import CORSMiddleware
from http.server import HTTPServer, BaseHTTPRequestHandler
import os
import threading

app = FastAPI()
app.add_middleware(HTTPSRedirectMiddleware)

origins = [
    "http://localhost:8001",
    "http://localhost:8000",
    "http://localhost",
    "http://localhost:8080",
    "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
class ImSwitchServer(Worker):

    def __init__(self, api, setupInfo):
        super().__init__()
        
        self._api = api
        self._name = setupInfo.pyroServerInfo.name
        self._host = setupInfo.pyroServerInfo.host
        self._port = setupInfo.pyroServerInfo.port

        self._paused = False
        self._canceled = False

        self.__logger =  initLogger(self)
        
        # start broadcasting server IP
        self.startmdns()

    def run(self):
        # serve the fastapi
        self.createAPI()
        
        # To operate remotely we need to provide https
        # openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365
        # uvicorn your_fastapi_app:app --host 0.0.0.0 --port 8001 --ssl-keyfile=./key.pem --ssl-certfile=./cert.pem
        _baseDataFilesDir = os.path.join(os.path.dirname(os.path.realpath(imswitch.__file__)), '_data')
        print(os.path.join(_baseDataFilesDir,"ssl", "key.cert"))
        
        def run_server():
            uvicorn.run(app, host="0.0.0.0", port=8001, ssl_keyfile=os.path.join(_baseDataFilesDir,"ssl", "key.pem"), ssl_certfile=os.path.join(_baseDataFilesDir,"ssl", "cert.pem"))

        server_thread = threading.Thread(target=run_server)
        server_thread.start()
        
        self.__logger.debug("Started server with URI -> PYRO:" + self._name + "@" + self._host + ":" + str(self._port))
        try:
            Pyro5.config.SERIALIZER = "msgpack"

            def print_exposed_methods(obj):
                if hasattr(obj, '__pyroExposed__'):
                    for method in obj.__pyroExposed__:
                        print(method)
            print("Exposed methods:")
            print_exposed_methods(self)
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
        self.__logger.debug("Stopping ImSwitchServer")
        self._daemon.shutdown()
        print("Unregistering...")
        zeroconf.unregister_service(self.info)
        zeroconf.close()


    def get_ip(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(('10.255.255.255', 1))
            IP = s.getsockname()[0]
        except Exception:
            IP = '127.0.0.1'
        finally:
            s.close()
        return IP

    def startmdns(self):
        service_type = "_https._tcp.local."  # Changed to HTTPS
        service_name = "imswitch._https._tcp.local."
        server_ip = self.get_ip()
        server_port = 8001  # Change to your server's port

        self.info = ServiceInfo(
            service_type,
            service_name,
            addresses=[socket.inet_aton(server_ip)],
            port=server_port,
            properties={},
        )

        zeroconf = Zeroconf()
        print(f"Registering service {service_name}, type {service_type}, at {server_ip}:{server_port}")
        try:
            zeroconf.register_service(self.info)
        except Exception as e:
            print(f"Failed to register service: {e}")
        

    #@expose
    def testMethod(self):
        return "Hello World"
    
    @app.get("/")
    def createAPI(self):
        api_dict = self._api._asdict()
        functions = api_dict.keys()

        def includeAPI(str, func):
            @app.get(str)
            @wraps(func)
            async def wrapper(*args, **kwargs):
                return func(*args, **kwargs)
            return wrapper

        def includePyro(func):
            @expose
            def wrapper(*args, **kwargs):
                return func(*args, **kwargs)
            return wrapper

        for f in functions:
            func = api_dict[f]
            if hasattr(func, 'module'):
                module = func.module
            else:
                module = func.__module__.split('.')[-1]
            self.func = includePyro(includeAPI("/"+module+"/"+f, func))

# Dynamically add functions to the exposed object
#https://chat.openai.com/c/40db1be0-b85c-4043-8f1a-074dcb70bc09
'''
for func_name in dir(my_module):
    if not func_name.startswith("_"):  # Filter out magic methods or private methods
        func = getattr(my_module, func_name)
        if callable(func):
            setattr(MyService.exposed_MyExposedObject, 'exposed_' + func_name, staticmethod(func))
'''
# Copyright (C) 2020-2024 ImSwitch developers
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
