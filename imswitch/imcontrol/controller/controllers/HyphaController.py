import numpy as np

try:
    import NanoImagingPack as nip
    isNIP = True
except:
    isNIP = False
    
import argparse
import asyncio
import logging
import os
import uuid
import fractions

import numpy as np
from av import VideoFrame
from imjoy_rpc.hypha.sync import connect_to_server, register_rtc_service
import aiortc
from aiortc import MediaStreamTrack, RTCPeerConnection, RTCSessionDescription, RTCConfiguration
from imswitch.imcommon.framework import Signal, Thread, Worker, Mutex
from imswitch.imcontrol.view import guitools
from imswitch.imcommon.model import initLogger
from ..basecontrollers import LiveUpdatedController
from PyQt5.QtCore import QThread, pyqtSignal

import asyncio
import logging
import os
import asyncio
import threading
from aiohttp import web

from aiohttp import web
from aiortc import RTCPeerConnection, RTCSessionDescription
from aiortc.contrib.media import MediaPlayer, MediaRelay, MediaStreamTrack
from aiortc.rtcrtpsender import RTCRtpSender
from av import VideoFrame
import fractions
import numpy as np

ROOT = os.path.dirname(__file__)

logger = logging.getLogger("pc")
pcs = set()

relay = None
webcam = None


class AsyncioThread(QThread):
    started = pyqtSignal()

    def __init__(self, loop):
        super().__init__()
        self.loop = loop

    def run(self):
        asyncio.set_event_loop(self.loop)
        self.started.emit()
        self.loop.run_forever()

class HyphaController(LiveUpdatedController):
    """ Linked to HyphaWidget."""

    sigImageReceived = Signal()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__logger = initLogger(self)
        self.frame = np.zeros((150, 300, 3)).astype('uint8')
        
        self.asyncio_thread = None

        # rtc-related
        self.pcs = set()
        host = "0.0.0.0"
        port = 8080

        self.ssl_context = None
        
        # TODO: Create ID based on user input 
        service_id = "UC2ImSwitch"
        server_url = "http://localhost:9000"
        server_url = "https://ai.imjoy.io/"
        
        self.stages = self._master.positionersManager[self._master.positionersManager.getAllDeviceNames()[0]]
        
        # get the first detector to stream data
        self.detector_names = self._master.detectorsManager.getAllDeviceNames()
        self.detector = self._master.detectorsManager[self.detector_names[0]]
        
        # start the service
        self.start_asyncio_thread(server_url, service_id)
        
    def update(self, detectorName, im, init, isCurrentDetector):
        """ Update with new detector frame. """
        pass
    
    def start_asyncio_thread(self, server_url, service_id):
        loop = asyncio.get_event_loop()
        self.asyncio_thread = AsyncioThread(loop)
        self.asyncio_thread.started.connect(self.on_asyncio_thread_started)
        self.asyncio_thread.start()

    def on_asyncio_thread_started(self):
        # Perform any necessary setup after the asyncio thread has started
        # Connect to the server and start the service
        service_id="aiortc-demo"
        logging.basicConfig(level=logging.DEBUG)
        self.start_service(service_id)

    async def on_shutdown(self, app):
        # close peer connections
        coros = [pc.close() for pc in self.pcs]
        await asyncio.gather(*coros)
        self.pcs.clear()

    def on_init(self, peer_connection):
        @peer_connection.on("track")
        def on_track(track):
            print(f"Track {track.kind} received")
            peer_connection.addTrack(
                VideoTransformTrack(detector=self.detector)
            )
            @track.on("ended")
            def on_ended():
                print(f"Track {track.kind} ended")

    # def move(self, direction, context=None):
        
    #     if message == "right":
    #         self.stages.move(value=100, axis="X", is_absolute=True, is_blocking=True)
    #     if message == "left":
    #         self.stages.move(value=-100, axis="X", is_absolute=True, is_blocking=True)
    #     if message == "up":
    #         self.stages.move(value=100, axis="Y", is_absolute=True, is_blocking=True)
    #     if message == "down":
    #         self.stages.move(value=-100, axis="Y", is_absolute=True, is_blocking=True)                        
    #     # pc.transport.send(message.encode())
    #     channel.send("completed")

    def move(self, value, axis, is_absolute=True, is_blocking=True):
        """A fuction to move the microscope stage, .... <------------change this
        # <--------- the limit of the stage are ...
        Args:
            value (number): the distance to move, ..
            axis (str): _description_
            is_absolute (bool, optional): ...
            is_blocking (bool, optional): ...
        """
        self.stages.move(value=value, axis=axis, is_absolute=is_absolute, is_blocking=is_blocking)
        
    def start_service(self, service_id, server_url="https://ai.imjoy.io/", workspace=None, token=None):
        client_id = service_id + "-client"
        print(f"Starting service...")
        server = connect_to_server(
            {
                "client_id": client_id,
                "server_url": server_url,
                "workspace": workspace,
                "token": token,
            }
        )
        server.register_service(
            {
                "id": "microscope-control",
                "name": "Microscope Control", # <------------change this
                "description": "Control the microscope stage", # <------------change this
                "config":{
                    "visibility": "protected",
                    "run_in_executor": True,
                    "require_context": True,   
                },
                "type": "microscope",
                "move": self.move,
                # <------------add more functions here
            }
        )
        # print("Workspace: ", workspace, "Token:", await server.generate_token({"expires_in": 3600*24*100}))
        coturn = server.get_service("coturn")
        ice_servers = coturn.get_rtc_ice_servers()
        register_rtc_service(
            server,
            service_id=service_id,
            config={
                "visibility": "public",
                "ice_servers": ice_servers,
                "on_init": self.on_init,
            },
        )
        print(
            f"Service (client_id={client_id}, service_id={service_id}) started successfully, available at https://ai.imjoy.io/{server.config.workspace}/services"
        )
        print(f"You can access the webrtc stream at https://oeway.github.io/webrtc-hypha-demo/?service_id={service_id}")




class VideoTransformTrack(MediaStreamTrack):
    """
    A video stream track that transforms frames from an another track.
    """

    kind = "video"

    def __init__(self, detector):
        super().__init__()  # don't forget this!
        self.count = 0
        self.detector = detector

    async def recv(self):
        # frame = await self.track.recv()
        img = self.detector.getLatestFrame().astype('uint8')
        if img is not None:
            if len(img.shape)<3:
                img = np.array((img,img,img))
                img = np.transpose(img, (1,2,0))
            #img = np.random.randint(0, 155, (150, 300, 3)).astype('uint8')
        else:
            img = np.random.randint(0, 155, (150, 300, 3)).astype('uint8')
        new_frame = VideoFrame.from_ndarray(img, format="bgr24")
        new_frame.pts = self.count # frame.pts
        self.count+=1
        new_frame.time_base = fractions.Fraction(1, 1000)
        return new_frame



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