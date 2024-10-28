import numpy as np

try:
    import NanoImagingPack as nip
    isNIP = True
except:
    isNIP = False
    
from imswitch.imcommon.framework import Signal, Thread, Worker, Mutex
from imswitch.imcontrol.view import guitools
from imswitch.imcommon.model import initLogger
from ..basecontrollers import LiveUpdatedController

import asyncio
import json
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


relay = None
webcam = None


class WebRTCController(LiveUpdatedController):
    """ Linked to WebRTCWidget."""

    sigImageReceived = Signal()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__logger = initLogger(self)
        self.frame = np.zeros((150, 300, 3)).astype('uint8')
        self.updateRate = 10
        self.it = 0
        self.init = False
        self.showPos = False

        # rtc-related
        self.pcs = set()
        host = "0.0.0.0"
        port = 8080

        self.ssl_context = None



        def aiohttp_server():
            app = web.Application()
            app.on_shutdown.append(self.on_shutdown)
            app.router.add_get("/", self.index)
            app.router.add_get("/client.js", self.javascript)
            app.router.add_post("/offer", self.offer)
            runner = web.AppRunner(app)
            return runner


        def run_server(runner):
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(runner.setup())
            site = web.TCPSite(runner, host, port)
            loop.run_until_complete(site.start())
            loop.run_forever()


        t = threading.Thread(target=run_server, args=(aiohttp_server(),))
        t.start()
        self.sigImageReceived.connect(self.displayImage)
        

    async def on_shutdown(self, app):
        # close peer connections
        coros = [pc.close() for pc in self.pcs]
        await asyncio.gather(*coros)
        self.pcs.clear()


    def update(self, detectorName, im, init, isCurrentDetector):
        """ Update with new detector frame. """
        if not isCurrentDetector or not self.active:
            return

        if self.it == self.updateRate:
            self.it = 0
            self.imageComputationWorker.prepareForNewImage(im)
            self.sigImageReceived.emit()
        else:
            self.it += 1

    def displayImage(self, im):
        """ Displays the image in the view. """
        self._widget.setImage(im)
        self.frame

    def force_codec(self, pc, sender, forced_codec):
        kind = forced_codec.split("/")[0]
        codecs = RTCRtpSender.getCapabilities(kind).codecs
        transceiver = next(t for t in pc.getTransceivers() if t.sender == sender)
        transceiver.setCodecPreferences(
            [codec for codec in codecs if codec.mimeType == forced_codec]
        )

    async def index(self, request):
        content = open(os.path.join(ROOT, "index.html"), "r").read()
        return web.Response(content_type="text/html", text=content)

    async def javascript(self, request):
        content = open(os.path.join(ROOT, "client.js"), "r").read()
        return web.Response(content_type="application/self.javascript", text=content)

    async def offer(self, request):
        params = await request.json()
        self.__logger.debug("Start to offer...")
        offer = RTCSessionDescription(sdp=params["sdp"], type=params["type"])

        pc = RTCPeerConnection()
        self.pcs.add(pc)

        @pc.on("connectionstatechange")
        async def on_connectionstatechange():
            self.__logger.debug("Connection state is %s" % pc.connectionState)
            if pc.connectionState == "failed":
                await pc.close()
                self.pcs.discard(pc)

        # open media source
        video = VideoTransformTrack()
        detectorManager = self._master.detectorsManager
        detectorNum1Name = detectorManager.getAllDeviceNames()[0]
        detector =  detectorManager[detectorNum1Name]
        video.setDetector(detector)
        video_sender = pc.addTrack(video)
        self.force_codec(pc, video_sender, "video/H264")
        
        await pc.setRemoteDescription(offer)

        answer = await pc.createAnswer()
        await pc.setLocalDescription(answer)

        return web.Response(
            content_type="application/json",
            text=json.dumps(
                {"sdp": pc.localDescription.sdp, "type": pc.localDescription.type}
            ),
        )










class VideoTransformTrack(MediaStreamTrack):
    """
    A video stream track that transforms frames from an another track.
    """

    kind = "video"

    def __init__(self):
        super().__init__()  # don't forget this!
        self.count = 0
    
    def setDetector(self, detector):
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
