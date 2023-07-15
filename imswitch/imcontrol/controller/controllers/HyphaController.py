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
import tifffile as tif

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
        
        # grab all necessary hardware elements
        self.stages = self._master.positionersManager[self._master.positionersManager.getAllDeviceNames()[0]]
        self.lasers = self._master.lasersManager[self._master.lasersManager.getAllDeviceNames()[0]]
        self.ledMatrix = self._master.ledMatricesManager[self._master.ledMatricesManager.getAllDeviceNames()[0]]
        
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


    def laserActivate(self, laserId=0, value=0):
        """
        Activates or deactivates a laser by setting its enabled state.

        Args:
            laserId (int, optional): The ID of the laser to activate or deactivate. Default is 0.
            value (int, optional): The value to set for the laser's enabled state. Default is 0.

        Returns:
            None

        Explanation:
            This function allows you to activate or deactivate a laser for fluorescence imaging by setting its enabled state.
            The laser to be controlled is specified by its laserId. By default, if no laserId is provided, 
            the function operates on the laser with ID 0.

            The enabled state of the laser is determined by the value parameter. If value is set to 1, the laser is activated,
            enabling it to emit light. If value is set to 0, the laser is deactivated, disabling its emission.

            Please note that this function does not return any value.
        """
        self.lasers[laserId].setEnabled(value)
        
    def laserValue(self, laserId=0, value=0):
        """
        Sets the value of a laser.

        Args:
            laserId (int, optional): The ID of the laser whose value is to be set. Default is 0.
            value (int, optional): The value to set for the laser. Default is 0.

        Returns:
            None

        Explanation:
            This function allows you to set the value of a laser. The laser to be controlled is specified by its laserId.
            By default, if no laserId is provided, the function operates on the laser with ID 0.

            The specific meaning of the value parameter may vary depending on the laser system being used. In general, it
            represents the desired output or intensity level of the laser. The interpretation of the value is specific to
            the laser system and should be consulted in the system's documentation.

            Please note that this function does not return any value.
        """    
        self.lasers[laserId].setValue(value)
        
    def ledValue(self, ledId=0, value=0):
        """
        Sets the value of an LED in an LED matrix.

        Args:
            ledId (int, optional): The ID of the LED in the matrix whose value is to be set. Default is 0.
            value (int, optional): The value to set for the LED. Default is 0.

        Returns:
            None

        Explanation:
            This function allows you to set the value of an LED in an LED matrix. The LED to be controlled is specified by its
            ledId. By default, if no ledId is provided, the function operates on the LED with ID 0.

            The value parameter represents the desired state or intensity of the LED. The interpretation of the value is specific
            to the LED matrix system being used and should be consulted in the system's documentation.

            Please note that this function does not return any value.
        """
        self.ledMatrix[ledId].setValue(value)
    
    def snapImage(self, path="Default.tif"):
        """
        Captures a single microscopic image and saves it to a specified path.

        Args:
            path (str, optional): The path to save the captured image. Default is "Default.tif".

        Returns:
            numpy.ndarray: The captured microscopic image as a NumPy array.

        Notes:
            - The function captures a single image using the microscope's detector.
            - The captured image is saved as a TIFF file at the specified path.
            - If no path is provided, the image is saved as "Default.tif" in the current working directory.
            - The captured image is also returned as a NumPy array.

        Raises:
            IOError: If there is an error saving the image to the specified path.

        Explanation:
            This function allows you to capture a single microscopic image using the microscope's detector. The captured image
            is saved as a TIFF file at the specified path. By default, if no path is provided, the image is saved as "Default.tif"
            in the current working directory.

            After capturing the image, it is returned as a NumPy array. This allows you to further process or analyze the image
            using the rich capabilities of the NumPy library.

            Please note that if there is an error saving the image to the specified path, an IOError will be raised. Make sure
            that the specified path is valid and that you have the necessary write permissions to save the image.
        """
        mImage = self.detector.getLatestFrame()
        tif.imsave(path,mImage)
        return mImage
        
    def move(self, value, axis, is_absolute=True, is_blocking=True):
        """
        Moves the microscope stage in the specified axis by a certain distance.

        Args:
            value (float): The physical distance to move the stage by.
            axis (str): The axis along which the stage should be moved. Valid values are 'X', 'Y', 'Z', and 'A'.
            is_absolute (bool, optional): Specifies whether the movement should be relative or absolute.
                                        If True (default), the movement is performed in absolute coordinates.
                                        If False, the movement is performed in relative coordinates.
            is_blocking (bool, optional): Specifies whether the function should block until the stage has arrived at the destination.
                                        If True (default), the function will wait until the stage has arrived.
                                        If False, the function will not wait and return immediately after initiating the movement.

        Returns:
            None

        Raises:
            ValueError: If an invalid axis is provided.

        Notes:
            - The stage must support the specified axis for the movement to be successful.
            - The value represents the physical distance to move the stage by. Positive values move the stage in the positive direction
            along the specified axis, while negative values move the stage in the negative direction.
            - If is_absolute is True, the value represents the absolute position to move the stage to along the specified axis.
            If is_absolute is False, the value represents the relative distance to move the stage from its current position.
            - If is_blocking is True, the function will wait until the stage has arrived at the destination before returning.
            If is_blocking is False, the function will initiate the movement and return immediately.

        Explanation:
            This function allows you to move a microscope stage in the specified axis by a certain distance. The stage can be moved
            along the 'x', 'y', 'z', or 'a' axis. The distance is specified by the 'value' parameter, which represents the physical
            distance to move the stage by. Positive values move the stage in the positive direction along the specified axis,
            while negative values move the stage in the negative direction.

            By default, the movement is performed in absolute coordinates. This means that if 'is_absolute' is set to True (default),
            the value represents the absolute position to move the stage to along the specified axis. However, you can also choose
            to perform the movement in relative coordinates by setting 'is_absolute' to False. In this case, the value represents
            the relative distance to move the stage from its current position.

            Additionally, you can control whether the function blocks until the stage has arrived at the destination. If 'is_blocking'
            is set to True (default), the function will wait until the stage has arrived at the destination before returning. This
            can be useful if you want to ensure that the stage has completed the movement before executing further instructions.
            On the other hand, if 'is_blocking' is set to False, the function will initiate the movement and return immediately
            without waiting for the stage to arrive.

            Please note that if an invalid axis is provided, a ValueError will be raised. Make sure to use one of the valid axis
            values: 'X', 'Y', 'Z', or 'A'. Also, ensure that the microscope stage supports the specified axis for the movement
            to be successful.

        """
        print(f"Moving stage to {value} along {axis}")
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
                "laserActivate": self.laserActivate,
                "laserValue": self.laserValue,
                "ledValue": self.ledValue,
                "snapImage": self.snapImage,
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