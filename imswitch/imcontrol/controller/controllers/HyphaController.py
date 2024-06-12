import numpy as np

try:
    import NanoImagingPack as nip
    isNIP = True
except:
    isNIP = False
import webbrowser
import asyncio
import logging
import os
import fractions
import tifffile as tif
from imswitch.imcontrol.controller.controllers.hypha.hypha_storage import HyphaDataStore
import numpy as np
from av import VideoFrame
from imjoy_rpc.hypha.sync import connect_to_server, register_rtc_service, login
import aiortc
import cv2
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
from pydantic import BaseModel, Field

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
        self.isRunning = False

    def run(self):
        if not self.isRunning:
            self.isRunning = True
            asyncio.set_event_loop(self.loop)
            self.started.emit()
            self.loop.run_forever()
        
class HyphaController(LiveUpdatedController):
    """ Linked to HyphaWidget."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__logger = initLogger(self)
        self.frame = np.zeros((150, 300, 3)).astype('uint8')
        self.hyphaURL = ""
        self.asyncio_thread = None

        # rtc-related
        self.pcs = set()
        host = "0.0.0.0"
        port = 8080
        self._isConnected = False

        self.ssl_context = None

        # storer for message dictionary
        self.message_dict = {}

        # grab all necessary hardware elements
        self.stages = self._master.positionersManager[self._master.positionersManager.getAllDeviceNames()[0]]
        self.laserNames = self._master.lasersManager.getAllDeviceNames()
        self.laser = self._master.lasersManager[self.laserNames[0]]
        try: self.ledMatrix = self._master.LEDMatrixsManager[self._master.LEDMatrixsManager.getAllDeviceNames()[0]]
        except: self.ledMatrix = None

        # get the first detector to stream data
        self.detector_names = self._master.detectorsManager.getAllDeviceNames()
        self.detector = self._master.detectorsManager[self.detector_names[0]]

        # connect signals 
        self._widget.sigLoginHypha.connect(self._loginHypha)
        
        # create datastorer
        self.datastore = HyphaDataStore()
        
    def _loginHypha(self):
        # start the service
        # TODO: Create ID based on user input
        #if self._isConnected:
        #    return
        service_id = "UC2ImSwitch"
        server_url = "http://localhost:9000"
        server_url = "https://ai.imjoy.io/"        
        self.start_asyncio_thread(server_url, service_id)

    def update(self, detectorName, im, init, isCurrentDetector):
        """ Update with new detector frame. """
        pass

    def start_asyncio_thread(self, server_url, service_id):
        loop = asyncio.get_event_loop()
        self.service_id = service_id
        self.asyncio_thread = AsyncioThread(loop)
        self.asyncio_thread.started.connect(self.on_asyncio_thread_started)
        self.asyncio_thread.start()

    def on_asyncio_thread_started(self):
        # Perform any necessary setup after the asyncio thread has started
        # Connect to the server and start the service
        logging.basicConfig(level=logging.DEBUG)
        self.start_service(self.service_id)

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

    def start_service(self, service_id, server_url="https://chat.bioimage.io", workspace=None, token=None):
        client_id = service_id + "-client"
        self.__logger.debug(f"Starting service...")
        def autoLogin(message):
            # automatically open default browser 
            webbrowser.open(message['login_url']) # TODO: pass login token to qtwebview
            print(f"Please open your browser and login at: {message['login_url']}")
        token = login({"server_url": server_url, 
                       "login_callback": autoLogin, 
                       "timeout": 10})
        server = connect_to_server(
            {
            "server_url": server_url,
            "token": token}
            )
        self.datastore.setup(server, service_id="data-store")
        svc = server.register_service(self.getExtensionDefinition())
        self.hyphaURL = f"https://bioimage.io/chat?server={server_url}&extension={svc.id}"
        try:
            webbrowser.open(self.hyphaURL)
            self._widget.setChatURL(url=f"https://bioimage.io/chat?token={token}&assistant=Skyler&server={server_url}&extension={svc.id}")
            self._isConnected = True
        except:
            pass
        print(f"Extension service registered with id: {svc.id}, you can visit the chatbot at {self.hyphaURL}, and the service at: {server_url}/{server.config.workspace}/services/{svc.id.split(':')[1]}")
        
        if 0:
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
        
        
    def get_schema(self):
        return {
            "move_by_distance": MoveByDistanceInput.schema(),
            "snap_image": SnapImageInput.schema(),
            "home_stage": HomeStage.schema(),
            "move_to_position": MoveToPositionInput.schema(),
            "set_illumination": SetIlluminationInput.schema(),
            "set_message_dict": MessagingExchange.schema(),
            "get_message_dict": MessagingExchange.schema(),
            "script_executor": ScriptExecutor.schema(), 
            "lightsheet_scan": LightsheetScan.schema(),
            "slide_scan": SlideScanInput.schema()
        }

    def move_stage_by_distance(self, kwargs):
        '''move the stage by a specified distance, the unit of distance is micrometers, so you need to input the distance in millimeters.'''
        config = MoveByDistanceInput(**kwargs)
        if config.x: self.setPosition(value=config.x, axis="X", is_absolute=False, is_blocking=True)
        if config.y: self.setPosition(value=config.y, axis="Y", is_absolute=False, is_blocking=True)
        if config.z: self.setPosition(value=config.z, axis="Z", is_absolute=False, is_blocking=True)
        return "Moved the stage a relative distance!"

    def move_to_position(self, kwargs=None, x=None, y=None, z=None):
        '''Move the stage to a specified position, the unit of distance is micrometers.'''
        if kwargs is not None:            
            config = MoveToPositionInput(**kwargs)
            x = config.x
            y = config.y
            z = config.z
        elif x is not None and y is not None and z is not None:
            pass
        return self.move_to_position_exec(x, y, z)

    def move_to_position_exec(self, x, y, z):
        if x: self.setPosition(value=x, axis="X", is_absolute=True, is_blocking=True)
        if y: self.setPosition(value=y, axis="Y", is_absolute=True, is_blocking=True)
        if z: self.setPosition(value=z, axis="Z", is_absolute=True, is_blocking=True)
        return "Moved the stage to the specified position!"

    def home_stage(self, kwargs):
        config = HomeStage(**kwargs)
        axis = config.axis
        if axis == "X":
            self._master.positionersManager[self._master.positionersManager.getAllDeviceNames()[0]].home_X()
        elif axis == "Y":
            self._master.positionersManager[self._master.positionersManager.getAllDeviceNames()[0]].home_Y()
        elif axis == "Z":
            self._master.positionersManager[self._master.positionersManager.getAllDeviceNames()[0]].home_Z()
        elif axis == "A":
            self._master.positionersManager[self._master.positionersManager.getAllDeviceNames()[0]].home_A()
            
        return "Homed the stage!"

    def setPosition(self, value, axis, is_absolute=True, is_blocking=True):
        """
        Moves the microscope stage in the specified axis by a certain distance.

        Example Use:
            # Move the stage 10000 µm in the positive X direction in absolute coordinates and wait for the stage to arrive.
            self.setPosition(value=10000, axis="X", is_absolute=True, is_blocking=True)

            # move the stage 10000 µm in the negative Y direction in relative coordinates and return immediately.
            self.setPosition(value=-10000, axis="Y", is_absolute=False, is_blocking=False)

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

    def script_executor(self, kwargs):
        """

        """
        self.scope = self
        config = ScriptExecutor(**kwargs)
        locals_dict = locals()
        try:
            exec(config.script, globals(), locals_dict)
            # Access the result
            result = locals_dict.get('result')            
        except Exception as e:
            print(f"Script execution failed: {e}")
            result = f"Script execution failed: {e}"
        return result
        

    def set_illumination(self, kwargs):
        '''
        Set the illumination of the microscope
        '''
        config = SetIlluminationInput(**kwargs)
        mChannel = config.channel
        mIntensity = config.intensity
        return self.set_illuimination_exec(mChannel, mIntensity)
        
    def set_illuimination_exec(self, mChannel, mIntensity):
        '''
        Set the illumination of the microscope without the schema.
        '''
        try:
            self.laserName = self._master.lasersManager.getAllDeviceNames()[mChannel]
            self._master.lasersManager[self.laserName].setEnabled(True*bool(mIntensity))
            self._master.lasersManager[self.laserName].setValue(mIntensity)
            return "Set the illumination!"
        except Exception as e:
            return "Error setting illumination: "+str(e)
        
    def scan_lightsheet(self, kwargs=None):
        '''
        This performs a light-sheet volumetric scan.
        '''
        #sigStartLightSheet = Signal(float, float, float, str, str, float) # (startX, endX, speed, axis, lightsource, lightsourceIntensity)
        if kwargs is None:
            return
        config = LightsheetScan(**kwargs)
        startX = config.startX
        endX = config.endX
        speed = config.speed
        axis = config.axis
        lightsource = config.lightsource
        lightsourceIntensity = config.lightsourceIntensity
        self._commChannel.sigStartLightSheet.emit(startX, endX, speed, axis, lightsource, lightsourceIntensity)
        return "Started light-sheet scanning!"
        
    
    def scan_slide(self, kwargs=None):
        '''
        This performs tile-based scanning of a slide.
        '''
        if kwargs is None:
            return 
        
        config = SlideScanInput(**kwargs)
        numberTilesX = config.numberTilesX
        numberTilesY = config.numberTilesY
        stepSizeX = config.stepSizeX
        stepSizeY = config.stepSizeY
        nTimes = config.nTimes
        tPeriod = config.tPeriod
        illuSource = config.illuSource
        initPosX = config.initPosX
        initPosY = config.initPosY
        isStitchAshlar = config.isStitchAshlar
        isStitchAshlarFlipX = config.isStitchAshlarFlipX
        isStitchAshlarFlipY = config.isStitchAshlarFlipY
        
        # Signal(int, int, int, int, int, int, str, int, int, bool, bool, bool) # (numberTilesX, numberTilesY, stepSizeX, stepSizeY, nTimes, tPeriod, illuSource, initPosX, initPosY, isStitchAshlar, isStitchAshlarFlipX, isStitchAshlarFlipY)
        self._commChannel.sigStartTileBasedTileScanning.emit(numberTilesX, numberTilesY, stepSizeX, stepSizeY, nTimes, tPeriod, illuSource, initPosX, initPosY, isStitchAshlar, isStitchAshlarFlipX, isStitchAshlarFlipY)
        return "Started slide scanning!"

    def snap_image(self, kwargs=None):
        '''
        '''
        if kwargs is None:
            return self.detector.getLatestFrame()
        
        config = SnapImageInput(**kwargs)
        mExposureTime = config.exposure = 100
        mFilePath = config.filepath 
        imageProcessingFunction = config.imageProcessingFunction 
        return self.snap_image_exec(config, mExposureTime, mFilePath, imageProcessingFunction)
    
    def snap_image_exec(self, config=None, mExposureTime:int=100, mFilePath:str="./", imageProcessingFunction:str=""):
        '''
        Captures a single image and processes it using a Python function provided as a string.
        '''
        # Step 1: Capture Image
        self._logger.debug("getProcessedImages - functionstring: "+imageProcessingFunction)
        mImage = self.detector.getLatestFrame()
        
        
        # TODO: Generate thumbnail and send to datastorage
        
        # Step 2: Load and Execute Python Function from String
        try:
            if imageProcessingFunction and imageProcessingFunction !=  "":
                # Define a default processImage function in case exec fails
                def processImage(image):
                    return image

                # TODO: We should check if the function is valid before executing it to avoid security issues
                
                # Execute the function string
                exec(imageProcessingFunction, globals(), locals())

                # Step 3: Process the Image
                fctName = imageProcessingFunction.split("def ")[1].split("(")[0]
                processedImage = locals()[fctName](mImage)
            else:
                processedImage = mImage

            # Step 3: Save the Image
            # check if processedImage is an image
            processedImage = np.uint8(processedImage)
            if len(processedImage.shape)>2:
                bgr_img = np.stack((processedImage,)*3, axis=-1)  # Duplicate grayscale data across 3 channels to simulate BGR format.
            else:
                bgr_img = cv2.cvtColor(processedImage, cv2.COLOR_GRAY2BGR)
            _, png_image = cv2.imencode('.png', bgr_img)        
            file_id = self.datastore.put('file', png_image.tobytes(), 'snapshot.png', "Captured microscope image in PNG format")
            print(f'The image is snapped and saved as {self.datastore.get_url(file_id)}')
            return self.datastore.get_url(file_id)

            '''
            if type(processedImage)==np.ndarray and len(processedImage.shape)>1:    
                if config is not None and config.returnAsNumpy:
                    return processedImage
                if not os.path.exists(os.path.dirname(mFilePath)):
                    os.makedirs(os.path.dirname(mFilePath))
                tif.imsave(mFilePath+".tif",processedImage)
                self._commChannel.sigDisplayImageNapari.emit(mFilePath, processedImage, False) # layername, image, isRGB
                return "Image saved at "+mFilePath+".tif"
            else:
            '''
            
        except Exception as e:
            return "Error processing image: "+str(e)

    def set_message_dict(self, kwargs):
        '''Store key and value pairs between consecutive message exchanges and chatbot sessions. Messages will be added to the 
        message dictionary and will be stored accross chat entries and chatbot sessions.'''
        config = MessagingExchange(**kwargs)
        
        # for all entries in the message dictionary config.message, add them to the message_dict
        self.message_dict_entry.update(config.message)
    
        return "Set and update the message dictionary!"

    def get_message_dict(self, kwargs):
        '''Retrieve the message dictionary. The message dictionary stores key and value pairs between consecutive message exchanges and chatbot sessions.'''
        return self.message_dict_entry

    def getExtensionDefinition(self):
            return {
            "_rintf": True,
            "type": "bioimageio-chatbot-extension",
            "id": "UC2_microscope",
            "name": "UC2 Microscope Control",
            "description": "Control the microscope based on the user's request. Now you can move the microscope stage, control the illumination, snap an image and process it.",
            "get_schema": self.get_schema,
            "tools": {
                "move_by_distance": self.move_stage_by_distance,
                "snap_image": self.snap_image,
                "home_stage": self.home_stage,
                "move_to_position": self.move_to_position,
                "set_illumination": self.set_illumination,
                "set_message_dict": self.set_message_dict,
                "get_message_dict": self.get_message_dict,
                "script_executor": self.script_executor, 
                "lightsheet_scan": self.scan_lightsheet, 
                "slide_scan": self.scan_slide
            }
        }
            


class MessagingExchange(BaseModel):
    # TODO: make this more generic
    '''
    self.dataStore = {}
    self.dataStore["image_1"] = np.ones((100,100))
    '''
    """Store key and value pairs between consecutive message exchanges and chatbot sessions."""
    message: dict = Field(description="The message to store in the exchange with a key that will be stored accross chat entries and values that can be anything.")
      
class ScriptExecutor(BaseModel):
    """
    Executes a Python script within the HyphaController class to control a microscope, accessible via 'self' or 'scope'. Scripts can orchestrate complex workflows using methods provided for microscope manipulation, incorporating loops and conditions. The script, a string of safe Python code, must not contain malicious elements, manipulate local files, or access the network. Key methods include:
    - "move_to_position" using MoveToPositionInput.schema() for xyz movement in absolute or relative terms.
    - "set_illumination" using SetIlluminationInput.schema() to adjust illumination between 0 and 1023.
    - "snap_image" using SnapImageInput.schema() to capture or process images. 
    Execution results are stored in a 'result' variable for feedback to the chatbot. Scripts have access to HyphaController's methods and local variables.
    The script must be safe to execute!
    """   
    script: str = Field(description="The Python script to execute.")
    context: dict = Field(description="Context information containing user details.")


class MoveByDistanceInput(BaseModel):
    """Move the stage by a specified distance, the unit of distance is millimeters, so you need to input the distance in millimeters."""
    x: float = Field(description="Move the stage along X axis.")
    y: float = Field(description="Move the stage along Y axis.")
    z: float = Field(description="Move the stage along Z axis.")

class SnapImageInput(BaseModel):
    #TODO: Docstring should be below 4000 characters
    #TODO: individual elements should be below 1024
    #TODO: in case we need additional information >= create a read-the-docs function
    #TODO: Don't define the arguments -> already in schema; only describe what the function is doing
    #TODO: Keep the examples!
    '''
    Snap an image from the microscope and process it using a provided Python function.

    Example:
        pythonFunctionString = """
        def processImage(image):
            # Convert to grayscale as an example
            return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        """

        context (dict, optional): Contains user details.

    Notes:
        - Captures a single image with the microscope's detector.
        - The processing function should have the following structure:
            def processImage(image):
                # Optional library imports
                processedImage = fu(image)
                # Image processing code
                return processedImage
            where 'image' is a 2D numpy array input and 'processedImage' is the output.
    '''
    exposure: int = Field(description="Set the microscope camera's exposure time. and the time unit is ms, so you need to input the time in miliseconds.")
    filepath: str = Field(description="The path to save the captured image. It will be a tif, so the extension does not need to be added. ")
    imageProcessingFunction: str = Field(description="The Python function to use for processing the image. Default is empty. image is the 2D array from the detector Example: def processImage(image): return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY). Avoid returning images since this is too much bandwidth. Return parameters from the function instead. Avoid using cv2") 
    returnAsNumpy: bool = Field(description="Return the image as a numpy array. Default is False and the image will be saved under filepath.")
                 
class LightsheetScan(BaseModel):
    '''
    This performs a light-sheet volumetric scan 
    '''                        
    startX: float = Field(description="The starting position in the lightsheet scanning  direction. Example: startX=-1000")
    endX: float = Field(description="The end position in the lightsheet scanning direction. Example: startX=1000")
    speed: float = Field(description="The speed of the scan. Example: speed=1000")
    axis: str = Field(description="The axis to scan. Example: axis='A'")
    lightsource: str = Field(description="The lightsource to use. Example: lightsource='Laser'")
    lightsourceIntensity: float = Field(description="The intensity of the lightsource. Example: lightsourceIntensity=100")
    

class SlideScanInput(BaseModel):
    '''
    This performs a slide scan 
    '''
    #sigStartTileBasedTileScanning = Signal(int, int, int, int, int, int, str, int, int, int, bool, bool, bool) 
    # (numberTilesX, numberTilesY, stepSizeX, stepSizeY, nTimes, tPeriod, illuSource, initPosX, initPosY, isStitchAshlar, isStitchAshlarFlipX, isStitchAshlarFlipY)
    numberTilesX: int = Field(description="The number of tiles in the X direction. Example: numberTilesX=3")
    numberTilesY: int = Field(description="The number of tiles in the Y direction. Example: numberTilesY=3")
    stepSizeX: int = Field(description="The step size in the X direction. If None, ImSwitch will calculate the correct spacing for you. Example: stepSizeX=None")
    stepSizeY: int = Field(description="The step size in the Y direction. If None, ImSwitch will calculate the correct spacing for you. Example: stepSizeY=None")
    nTimes: int = Field(description="The number of times to repeat the scan. Example: nTimes=1")
    tPeriod: int = Field(description="The time period between each scan. Example: tPeriod=1")
    illuSource: str = Field(description="The illumination source to use. Example: illuSource=None")
    initPosX: int = Field(description="The initial position in the X direction. If None the microscope will take the current position. Example: initPosX=None")
    initPosY: int = Field(description="The initial position in the Y direction. If None the microscope will take the current position. Example: initPosY=None") 
    isStitchAshlar: bool = Field(description="Stitch the tiles using the software Ashlar. Example isStitchAshlar=True")
    isStitchAshlarFlipX: bool = Field(description="Flip the tiles along the X axis. Example isStitchAshlarFlipX=True")
    isStitchAshlarFlipY: bool = Field(description="Flip the tiles along the Y axis. Example isStitchAshlarFlipY=False")
    
class SetIlluminationInput(BaseModel):
    """Set the illumination of the microscope."""
    channel: int = Field(description="Set the channel of the illumination. The value should choosed from this list: [0, 1, 2, 3] ")
    intensity: float = Field(description="Set the intensity of the illumination. The value should be between 0 and 100; ")

class HomeStage(BaseModel):
    """Home the stage."""
    home: int = Field(description="Home the stage and set position to zero.")
    axis: str = Field(description="The axis to home. Default is X. Available options are: X, Y, Z, A.")
class MoveToPositionInput(BaseModel):
    """Move the stage to a specified position, the unit of distance is millimeters. The limit of """
    x: float = Field(description="Move the stage to the specified position along X axis.")
    y: float = Field(description="Move the stage to the specified position along Y axis.")
    z: float = Field(description="Move the stage to the specified position along Z axis.")

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
