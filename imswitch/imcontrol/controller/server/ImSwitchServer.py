import threading
import Pyro5
import Pyro5.server
from imswitch.imcommon.framework import Worker
from imswitch.imcommon.model import initLogger
from ._serialize import register_serializers
from fastapi.middleware.cors import CORSMiddleware
from io import BytesIO
import numpy as np
from PIL import Image
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
import asyncio
from multiprocessing import Queue
import uvicorn
from functools import wraps
import cv2
import os

from http.server import HTTPServer, BaseHTTPRequestHandler
import os
import threading

app = FastAPI()

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
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


    def run(self):
        
        # serve APP
        self.startAPP()       
            
        # serve the fastapi
        self.createAPI()
        uvicorn.run(app, host="0.0.0.0", port=8000)
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


    # SRC: https://code-maven.com/static-server-in-python
    class StaticServer(BaseHTTPRequestHandler):
    
        def do_GET(self):
            root = os.path.dirname(os.path.abspath(__file__).split("imswitch")[0]+"imswitch/app/public/")
            
            if self.path == '/':
                filename = root + '/index.html'
            else:
                filename = root + self.path
    
            self.send_response(200)
            if filename[-4:] == '.css':
                self.send_header('Content-type', 'text/css')
            elif filename[-5:] == '.json':
                self.send_header('Content-type', 'application/javascript')
            elif filename[-3:] == '.js':
                self.send_header('Content-type', 'application/javascript')
            elif filename[-4:] == '.ico':
                self.send_header('Content-type', 'image/x-icon')
            else:
                self.send_header('Content-type', 'text/html')
            self.end_headers()
            with open(filename, 'rb') as fh:
                html = fh.read()
                #html = bytes(html, 'utf8')
                self.wfile.write(html)
 
    def start_server(self, httpd):
        #print('Starting httpd')
        httpd.serve_forever()
     
    def startAPP(self, server_class=HTTPServer, handler_class=StaticServer, port=5001):
        server_address = ('', port)
        try:
            httpd = server_class(server_address, handler_class)
            t = threading.Thread(target=self.start_server, args=(httpd,))
            t.start()
        
            print('httpd started on port {}'.format(port))
        except Exception as e:
            print('httpd failed to start on port {}'.format(port))
            print(e)
            return



    @app.get("/")
    def createAPI(self):
        api_dict = self._api._asdict()
        functions = api_dict.keys()


        def includeAPI(str, func):
            self.__logger.debug(str)
            self.__logger.debug(func)
            @app.get(str)
            @wraps(func)
            async def wrapper(*args, **kwargs):
                return func(*args, **kwargs)
            return wrapper



        '''
            @Pyro5.server.expose
            def move(self, positionerName=None, axis="X", dist=0) -> np.ndarray:
                return self._channel.move(positionerName, axis=axis, dist=dist)

            @Pyro5.server.expose
            def run_mda(self, sequence: MDASequence) -> None:
                self.__logger.info("MDA Started: {}")
                self._paused = False
                paused_time = 0.0
                t0 = time.perf_counter()  # reference time, in seconds

                def check_canceled():
                    if self._canceled:
                        self.__logger.warning("MDA Canceled: ")
                        self._canceled = False
                        return True
                    return False

                for event in sequence:
                    while self._paused and not self._canceled:
                        paused_time += 0.1  # fixme: be more precise
                        time.sleep(0.1)

                    if check_canceled():
                        break

                    if event.min_start_time:
                        go_at = event.min_start_time + paused_time
                        # We need to enter a loop here checking paused and canceled.
                        # otherwise you'll potentially wait a long time to cancel
                        to_go = go_at - (time.perf_counter() - t0)
                        while to_go > 0:
                            while self._paused and not self._canceled:
                                paused_time += 0.1  # fixme: be more precise
                                to_go += 0.1
                                time.sleep(0.1)

                            if self._canceled:
                                break
                            if to_go > 0.5:
                                time.sleep(0.5)
                            else:
                                time.sleep(to_go)
                            to_go = go_at - (time.perf_counter() - t0)

                    # check canceled again in case it was canceled
                    # during the waiting loop
                    if check_canceled():
                        break

                    self.__logger.info(event.x_pos)

                    # prep hardware
                    if event.x_pos is not None or event.y_pos is not None:
                        x = event.x_pos or self.getXPosition()
                        y = event.y_pos or self.getYPosition()
                        self._channel.sigSetXYPosition.emit(x, y)
                    if event.z_pos is not None:
                        self._channel.sigSetZPosition.emit(event.z_pos)
                    if event.exposure is not None:
                        self._channel.sigSetExposure.emit(event.exposure)

                self.__logger.info("MDA Finished: ")
                pass

        '''


        def includePyro(func):
            @Pyro5.server.expose
            def wrapper(*args, **kwargs):
                return func(*args, **kwargs)
            return wrapper

        for f in functions:
            func = api_dict[f]
            if hasattr(func, 'module'):
                module = func.module
            else:
                module = func.__module__.split('.')[-1]
            self.__logger.debug("/"+module+"/"+f)
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
