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
        try: self.ledMatrix = self._master.LEDMatrixsManager[self._master.LEDMatrixsManager.getAllDeviceNames()[0]]
        except: self.ledMatrix = None

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
        self.start_service(service_id, token="")

    async def on_shutdown(self, app):
        # close peer connections
        coros = [pc.close() for pc in self.pcs]
        await asyncio.gather(*coros)
        self.pcs.clear()

    def on_init(self, peer_connection):
        @peer_connection.on("track")
        def on_track(track):
            self.__logger.debug(f"Track {track.kind} received")
            peer_connection.addTrack(
                VideoTransformTrack(detector=self.detector)
            )
            @track.on("ended")
            def on_ended():
                self.__logger.debug(f"Track {track.kind} ended")


    def setLaserActive(self, laserId=0, value=0, context=None):
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

    def setLaserValue(self, laserId=0, value=0, context=None):
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

    def setLEDValue(self, ledId=0, value=0, context=None):
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

    def getImage(self, path="Default.tif", context=None):
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

    def setPosition(self, value, axis, is_absolute=True, is_blocking=True, context=None):
        """
        Moves the microscope stage in the specified axis by a certain distance.

        Args:
            value (float): The physical distance to move the stage by.
            axis (str): The axis along which the stage should be moved. Valid values are 'X', 'Y', 'Z', and 'A'.
            is_absolute (bool, optional): Specifies whether the movement should be relative or absolute. Default is True (absolute).
            is_blocking (bool, optional): Specifies whether the function should block until the stage has arrived at the destination. Default is True.
            context (dict, optional): Context information containing user details.

        Returns:
            None

        Example Use:
            # Move the stage 10000 µm in the positive X direction in absolute coordinates and wait for the stage to arrive.
            self.setPosition(value=10000, axis="X", is_absolute=True, is_blocking=True, context=context)

            # move the stage 10000 µm in the negative Y direction in relative coordinates and return immediately.
            self.setPosition(value=-10000, axis="Y", is_absolute=False, is_blocking=False, context=context)

        Notes:
            - Successful movement requires supported axis.
            - Positive values move stage forward, negative values move it backward.
            - `is_absolute=True` for absolute position, `is_absolute=False` for relative distance.
            - `is_blocking=True` waits until stage arrives, `is_blocking=False` initiates and returns.

        Explanation:
            This function allows moving the microscope stage along the 'x', 'y', 'z', or 'a' axis by a certain distance. "\
            "Use 'value' for the distance, 'is_absolute' for absolute or relative coordinates, and 'is_blocking' to control waiting behavior. "\
            "Ensure valid axis values and stage support.
        """
        self._logger.debug(f"Moving stage to {value} along {axis}")
        self.stages.move(value=value, axis=axis, is_absolute=is_absolute, is_blocking=is_blocking)

    def start_service(self, service_id, server_url="https://ai.imjoy.io/", workspace=None, token=None):
        client_id = service_id + "-client"
        self.__logger.debug(f"Starting service...")
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
                "name": "openUC2 Microscope",
                "description": "OpenUC2 Microscope Interface: Precise control over openuc2 microscope.",# Monochrome camera, laser, LED matrix, focusing stage, XY stage. Easy sample manipulation, accurate autofocus, fluorescence microscopy. LED matrix enhances phase contrast. High-quality grayscale imaging. Unparalleled precision.",
                "config":{
                    "visibility": "public",
                    "run_in_executor": True,
                    "require_context": True,
                },
                "type": "microscope",
                "move": self.setPosition,
                "setLaserActive": self.setLaserActive,
                "setLaserValue": self.setLaserValue,
                "setLEDValue": self.setLEDValue,
                "getImage": self.getImage
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
        self.__logger.debug(
            f"Service (client_id={client_id}, service_id={service_id}) started successfully, available at https://ai.imjoy.io/{server.config.workspace}/services"
        )
        self.__logger.debug(f"You can access the webrtc stream at https://oeway.github.io/webrtc-hypha-demo/?service_id={service_id}")




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
        img = self.detector.getLatestFrame()
        if img is not None:
            if len(img.shape)<3:
                img = np.array((img,img,img))
                img = np.transpose(img, (1,2,0))
            img = img/np.max(img)
            img = img*255
            img = np.uint8(img)
            #img = np.random.randint(0, 155, (150, 300, 3)).astype('uint8')
        else:
            img = np.random.randint(0, 155, (150, 300, 3)).astype('uint8')
        from skimage import data, color
        from skimage.transform import rescale, resize, downscale_local_mean
        img = resize(img, (img.shape[0] // 4, img.shape[1] // 4, img.shape[2]),
                            anti_aliasing=True)
        img = np.uint8(img*255)
        new_frame = VideoFrame.from_ndarray(img, format="bgr24")
        new_frame.pts = self.count # frame.pts
        self.count+=1
        new_frame.time_base = fractions.Fraction(1, 1000)
        return new_frame



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