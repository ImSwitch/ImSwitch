from imswitch.imcontrol.controller.controllers.hypha.hypha_storage import HyphaDataStore
from imswitch.imcontrol.controller.controllers.hypha.hypha_executor import execute_code
from imswitch.imcontrol.controller.basecontrollers import LiveUpdatedController
from imswitch.imcommon.model import initLogger, APIExport
from imswitch import IS_HEADLESS
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
import numpy as np
import numpy as np
from av import VideoFrame
from imjoy_rpc.hypha.sync import connect_to_server, register_rtc_service, login
import aiortc
import cv2
from aiortc import MediaStreamTrack, RTCPeerConnection, RTCSessionDescription, RTCConfiguration

import asyncio
import logging
import os
import asyncio
import threading
from aiohttp import web
from aiortc import RTCPeerConnection, RTCSessionDescription
from aiortc.contrib.media import MediaPlayer, MediaRelay, MediaStreamTrack
from aiortc.rtcrtpsender import RTCRtpSender
from av import VideoFrame
import fractions
import numpy as np
from pydantic import BaseModel, Field
import tifffile as tif
import time
from imswitch.imcommon.model import dirtools
from datetime import datetime
from typing import Optional

ROOT = os.path.dirname(__file__)

logger = logging.getLogger("pc")
pcs = set()

relay = None
webcam = None

class MyMicroscope(object):
    '''
    Generalized microscopy object that will interact with the chatbot
    If you want to use this object, you need to implement the following functions:
    - move_stage
    - set_illumination
    - snap_image
    - record_image

    TODO: Should we provide Schemas alongside the functions? Make it generic (e.g. in the process when generating the swagger API?)
    '''

    def __init__(self, stage, illumination, camera, specialFcts=None):
        self.stage = stage
        self.illumination = illumination
        self.camera = camera
        self.specialFcts = specialFcts

    def move_stage(self, distance, is_absolute, axis, speed):
        return self.stage.move(value=distance, is_absolute=is_absolute, axis=axis, speed=speed)

    def set_illumination(self, channel, intensity):
        # TODO: implement mChannel
        self.illumination.setEnabled(True*bool(intensity))
        return self.illumination.setValue(intensity)

    def snap_image(self, exposure=None, gain=None):
        # TODO: Implement the epxosure/gain values
        return self.camera.getLatestFrame()

    def home(self, axis):
        return self.stage.home(axis)

    def autofocus(self, minZ, maxZ, stepSize):
        try:
            self.autofocus = self.specialFcts["autofocus"]
            valueRange = (maxZ-minZ)
            valueSteps = stepSize
            return self.autofocus(valueRange, valueSteps)
        except Exception as e:
            return e

    def scan_stage(self, startX, endX, speed, axis, lightsource, lightsourceIntensity):
        try:
            self.scan = self.specialFcts["scan_stage"]
            return self.scan(startX, endX, speed, axis, lightsource, lightsourceIntensity)
        except Exception as e:
            return e

    def scan_stage_tiles(self, numberTilesX, numberTilesY, stepSizeX, stepSizeY, nTimes, tPeriod, illuSource, initPosX, initPosY, isStitchAshlar, isStitchAshlarFlipX, isStitchAshlarFlipY):
        try:
            self.scan_tiles = self.specialFcts["scan_stage_tiles"]
            return self.scan_tiles(numberTilesX, numberTilesY, stepSizeX, stepSizeY, nTimes, tPeriod, illuSource, initPosX, initPosY, isStitchAshlar, isStitchAshlarFlipX, isStitchAshlarFlipY)
        except Exception as e:
            return e

        # Signal(int, int, int, int, int, int, str, int, int, bool, bool, bool)
        # (numberTilesX, numberTilesY, stepSizeX, stepSizeY, nTimes, tPeriod, illuSource, initPosX, initPosY, isStitchAshlar, isStitchAshlarFlipX, isStitchAshlarFlipY)
        # self._commChannel.sigStartTileBasedTileScanning.emit()

    def scan_lightsheet(self, startX, endX, speed, axis, lightsource, lightsourceIntensity):
        try:
            self.scan_lightsheet = self.specialFcts["scan_lightsheet"]
            return self.scan_lightsheet(startX, endX, speed, axis, lightsource, lightsourceIntensity)
        except Exception as e:
            return e

if IS_HEADLESS:
    QThread = object
    pyqtSignal = None
else:
    from PyQt5.QtCore import QThread, pyqtSignal

class AsyncioThread(QThread):
    # We need this in order to get asynchronous behavior in the HyphaController
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

        # create datastorer for data transfer between Hypha and the microscope; also serves as long-term memory for data/results
        self.datastore = HyphaDataStore()

        # connect signals
        if not IS_HEADLESS:
            self._widget.sigLoginHypha.connect(self._loginHypha)

        '''
        assign hardware functions
        '''
        # Grab all necessary hardware elements
        # This should be control-software agnostic
        self.stageNames = self._master.positionersManager.getAllDeviceNames()
        self.stage = self._master.positionersManager[self.stageNames[0]]   # Positioner Object
        self.laserNames = self._master.lasersManager.getAllDeviceNames()
        self.laser = self._master.lasersManager[self.laserNames[0]]         # Illumination Object
        self.detectorNames = self._master.detectorsManager.getAllDeviceNames()
        self.detector = self._master.detectorsManager[self.detectorNames[0]]
        try: self.ledMatrix = self._master.LEDMatrixsManager[self._master.LEDMatrixsManager.getAllDeviceNames()[0]]
        except: self.ledMatrix = None

        # Misc
        self._videoThread = None

        # add special functions to the API
        self.specialFcts = {}
        self.specialFcts["scan_stage_tiles"] = lambda numberTilesX, numberTilesY, stepSizeX, stepSizeY, nTimes, tPeriod, illuSource, initPosX, initPosY, isStitchAshlar, isStitchAshlarFlipX, isStitchAshlarFlipY: self._commChannel.sigStartTileBasedTileScanning.emit(numberTilesX, numberTilesY, stepSizeX, stepSizeY, nTimes, tPeriod, illuSource, initPosX, initPosY, isStitchAshlar, isStitchAshlarFlipX, isStitchAshlarFlipY)
        self.specialFcts["scan_lightsheet"] = lambda startX, endX, speed, axis, lightsource, lightsourceIntensity: self._commChannel.sigStartLightSheet.emit(startX, endX, speed, axis, lightsource, lightsourceIntensity)
        self.specialFcts["autofocus"] = lambda valueRange, valueSteps: self._commChannel.sigAutoFocus.emit(valueRange, valueSteps) # move up/down around the current positio at certain stepsize

        # create microscope object
        self.mMicroscope = MyMicroscope(stage=self.stage,
                                        illumination=self.laser,
                                        camera=self.detector,
                                        specialFcts=self.specialFcts)


    def _loginHypha(self):
        '''
        Function that opens the connection to the Hypha server.
        It also returns the URL to be opened in the GUI to interact with it.
        #
        # TODO: Create ID based on user input
        #   if self._isConnected:
        #       return'''
        service_id = "UC2ImSwitch"
        #server_url = "http://localhost:9000"
        #server_url = "https://ai.imjoy.io/"
        server_url = "https://chat.bioimage.io"
        self.connecto_to_server_asyncio(service_id, server_url)

    def update(self, detectorName, im, init, isCurrentDetector):
        """ Update with new detector frame. """
        pass

    def connecto_to_server_asyncio(self, service_id, server_url="https://chat.bioimage.io"):
        '''
        This function starts the asyncio thread and
        connects to the hypha server in the background and awaits an established connection
        server_url: str - the URL of the server
        service_id: str - the ID of the service
        '''
        loop = asyncio.get_event_loop()
        self.service_id = service_id
        self.server_url = server_url
        self.asyncio_thread = AsyncioThread(loop)
        self.asyncio_thread.started.connect(self.on_asyncio_thread_started)
        self.asyncio_thread.start()

    def on_asyncio_thread_started(self):
        # Perform any necessary setup after the asyncio thread has started
        # Connect to the server and start the service
        logging.basicConfig(level=logging.DEBUG)
        self.start_service(self.service_id, self.server_url)

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

    #@APIExport(runOnUIThread=True)
    def start_service(self, service_id, server_url="https://chat.bioimage.io", workspace=None, token=None):
        '''
        This logs into the Hypha Server and starts the service.
        It also registers the extensions that will hook up the microsocpe to the chatbot

        service_id: str - the ID of the service that will be replied by the server when you log in
        server_url: str - the URL of the server
        workspace: str - the workspace of the server
        token: str - the token to log in to the server and will be replied by the server when you log in

        '''
        self.__logger.debug(f"Starting service...")
        client_id = service_id + "-client"

        def autoLogin(message):
            # automatically open default browser and return the login token
            webbrowser.open(message['login_url']) # TODO: pass login token to qtwebview
            print(f"Please open your browser and login at: {message['login_url']}")

        try:
            token = login({"server_url": server_url,
                       "login_callback": autoLogin,
                       "timeout": 10})
        except Exception as e:
            # probably timeout error - not connected to the Internet?
            self.__logger.error(e)
            return "probably timeout error - not connected to the Internet?"
        server = connect_to_server(
            {
            "server_url": server_url,
            "token": token}
            )
        # initialize datastorer for image saving and data handling outside the chat prompts, resides on the hypha server
        self.datastore.setup(server, service_id="data-store")
        svc = server.register_service(self.getMicroscopeControlExtensionDefinition())
        self.hyphaURL = f"https://bioimage.io/chat?server={server_url}&extension={svc.id}"
        try:
            # open the chat window in the browser to interact with the herin created connection
            webbrowser.open(self.hyphaURL)
            self._widget.setChatURL(url=f"https://bioimage.io/chat?token={token}&assistant=Skyler&server={server_url}&extension={svc.id}")
            self._isConnected = True
        except:
            pass
        print(f"Extension service registered with id: {svc.id}, you can visit the chatbot at {self.hyphaURL}, and the service at: {server_url}/{server.config.workspace}/services/{svc.id.split(':')[1]}")

        if 0:
            # FIXME: WEBRTC-related stuff, need to reimplement this!
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



    # TODO: push/pull the schema similar to a property in the class
    # TODO: Differentiate into hacker/beginner mode
    def get_schema(self):
        '''
        Explanation: the function (e.g. "move_stage") is connected to the Schema (e.g. MoveStage.schema())
        The Schema contains the doc strings and information for the chatbot to construct the response and hardware control
        '''

        return {
            "snap_image": SnapImageInput.schema(),
            "record_video": RecordingVideo.schema(),
            "home_stage": HomeStageInput.schema(),
            "move_stage": MovePositionerInput.schema(),
            "set_illumination": SetIlluminationInput.schema(),
            "autofocus": AutoFocusInput.schema(),
            "script_executor": ScriptExecutor.schema(),
            "lightsheet_scan": LightsheetScan.schema(),
            "stage_scan": StageScanInput.schema(),
            # get current position of the stage, get illumination state, get detector state, get temperature, etc
            #"get_config": GetMicroscopeConfig.schema(), # STage Limits, Available Illumination, Available Detectors, Dictionary of config
            #"set_camera_config": CameraSettings.schema(), # set exposure, set gain, set binning, set ROI, set color mode, set frame rate, fov, sample size
            #"led_matrix": LEDMatrix.schema(),
            #"get_status": GetPosition.schema(),
            #"get_camera_config": GetCameraSettings.schema(), # get exposure, get gain, get binning, get ROI, get color mode, get frame rate
            #"set_message_dict": MessagingExchange.schema(),
            #"get_message_dict": MessagingExchange.schema(),
            #"create_qttabwidget": CreateQTTabWidget.schema(),
            #"get_illumination": GetIllumination.schema(),

        }

    def create_qttabwidget(self, kwargs):
        '''
        Create a QTTabWidget with a WebView to display the chatbot.
        '''
        if kwargs is None:
            return
        config = CreateQTTabWidget(**kwargs)

    def move_stage(self, kwargs=None):
        '''Move the stage to a specified position, the unit of distance is micrometers.'''
        if kwargs is not None:
            config = MovePositionerInput(**kwargs)
        distance = config.distance
        is_absolute = config.is_absolute
        axis = config.axis
        speed = config.speed
        return self.mMicroscope.move_stage(distance, is_absolute, axis, speed)

    def autofocus(self, kwargs=None):
        '''
        Perform an autofocus of the microscope increase sharpness of the image.
        '''
        if kwargs is None:
            return
        config = AutoFocusInput(**kwargs)
        minZ = config.minZ
        maxZ = config.maxZ
        stepSize = config.stepSize
        return self.mMicroscope.autofocus(minZ, maxZ, stepSize)

    def home_stage(self, kwargs):
        '''
        moves axis to 0 position and re-calibrates the position
        '''
        config = HomeStageInput(**kwargs)
        axis = config.axis
        return self.mMicroscope.home(axis=axis)


    async def script_executor(self, kwargs):
        """

        """
        self.scope = self
        config = ScriptExecutor(**kwargs)
        locals_dict = locals()
        try:
            print(config.script)
            result = await execute_code(self.datastore, config.script, locals_dict)
            if 0:
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
        return self.mMicroscope.set_illumination(mChannel, mIntensity)

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
        self.mMicroscope.scan_lightsheet(startX, endX, speed, axis, lightsource, lightsourceIntensity)
        return "Started light-sheet scanning!"


    def stage_scan(self, kwargs=None):
        '''
        This performs tile-based scanning of a microscopy sample.
        '''
        if kwargs is None:
            return
        config = StageScanInput(**kwargs)
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
        return self.mMicroscope.scan_stage_tiles(numberTilesX, numberTilesY, stepSizeX, stepSizeY,
                                                 nTimes, tPeriod, illuSource, initPosX, initPosY,
                                                 isStitchAshlar, isStitchAshlarFlipX, isStitchAshlarFlipY)

    def record_video(self, kwargs=None):
        '''
        record frames as fast as possible and save them as a "video" (TIF) to disk
        '''
        record_video = RecordingVideo(**kwargs)
        duration = record_video.duration
        filepath = record_video.filepath
        framerate = record_video.framerate
        stop = record_video.stop

        class VideoThread(threading.Thread):
            def __init__(self, duration, filepath, framerate):
                self.duration = duration
                self.filepath = filepath
                # check if the file exists and if it has a tif extension
                if not self.filepath.endswith(".tif"):
                    self.filepath = self.filepath + ".tif"
                # if the folder does not exist, create it
                if not os.path.exists(os.path.dirname(self.filepath)):
                    os.makedirs(os.path.dirname(self.filepath))
                self.framerate = framerate
                self.stop = False
                threading.Thread.__init__(self)

            def run(self):
                mStartTime = time.time()
                while time.time()-mStartTime < self.duration and not self.stop:
                    mFrame = self.detector.getLatestFrame()
                    tif.imsave(self.filepath, mFrame, append=True)
                    time.sleep(1/self.framerate)

            def stop(self):
                self.stop = True

        if stop and self._videoThread is not None:
            # stop the video recording
            self._videoThread.stop()
            return

        if self._videoThread is None:
            self._videoThread = VideoThread(duration, filepath, framerate)
            self._videoThread.start()


    def snap_image(self, kwargs=None):
        '''
        snap an image, store it eventually, return it eventually or process it eventually
        '''

        # parse the schema
        config = SnapImageInput(**kwargs)
        mExposureTime = config.exposure = 100
        mFilePath = config.filepath
        imageProcessingFunction = config.imageProcessingFunction
        return_image = config.returnAsNumpy
        mImage = self.mMicroscope.snap_image(mExposureTime)
        returnMessage = {}

        def packImageToDatastore(mImage):
            '''
            helper function to send image to hyphastore and restore the URL
            '''
            processedImage = np.uint8(mImage)
            if len(processedImage.shape)>2:
                bgr_img = np.stack((processedImage,)*3, axis=-1)  # Duplicate grayscale data across 3 channels to simulate BGR format.
            else:
                bgr_img = cv2.cvtColor(processedImage, cv2.COLOR_GRAY2BGR)
            _, png_image = cv2.imencode('.png', bgr_img)
            file_id = self.datastore.put('file', png_image.tobytes(), 'snapshot.png', "Captured microscope image in PNG format")
            print(f'The image is snapped and saved as {self.datastore.get_url(file_id)}')
            return self.datastore.get_url(file_id)

        if mFilePath:
            try:
                # check if the file exists and if it has a tif extension
                if not mFilePath.endswith(".tif"):
                    mFilePath = mFilePath + ".tif"
                # if the folder does not exist, create it
                dirPath  = os.path.join(dirtools.UserFileDirs.Root, 'recordings', datetime.now().strftime("%Y_%m_%d-%I-%M-%S_%p") )
                if not os.path.exists(dirPath):
                    os.makedirs(dirPath)
                # save an image as a tif
                tif.imsave(os.path.join(dirPath,mFilePath), mImage)
                returnMessage["imagePath"] = os.path.join(dirPath,mFilePath)
                self.__logger.debug(f"Image saved as {os.path.join(dirPath,mFilePath)}")
            except Exception as e:
                return "Error saving image: "+str(e)

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

            # directly return the image
            imageURL = packImageToDatastore(processedImage)
            returnMessage["imageURL"] = imageURL
            if return_image:
                processedImage
            return returnMessage

        except Exception as e:
            return "Error processing image: "+str(e)

    '''
    def set_message_dict(self, kwargs):
        """Store key and value pairs between consecutive message exchanges and chatbot sessions. Messages will be added to the
        message dictionary and will be stored accross chat entries and chatbot sessions."""
        config = MessagingExchange(**kwargs)

        # for all entries in the message dictionary config.message, add them to the message_dict
        self.message_dict_entry.update(config.message)

        return "Set and update the message dictionary!"
    '''
    #def get_message_dict(self, kwargs):
    #    '''Retrieve the message dictionary. The message dictionary stores key and value pairs between consecutive message exchanges and chatbot sessions.'''
    #    return self.message_dict_entry

    def getMicroscopeControlExtensionDefinition(self):
            return {
            "_rintf": True,
            "type": "bioimageio-chatbot-extension",
            "id": "UC2_microscope",
            "name": "UC2 Microscope Control",
            "description": "Control the microscope based on the user's request. Move the microscope stage, control the illumination, snap an image, and process it. Use the scriptexecutor for executing tasks. Display received images as markdown in the chat window",
            "get_schema": self.get_schema,
            "config": {"run_in_executor": True},
            "tools": {
                "snap_image": self.snap_image,
                "record_video": self.record_video,
                "home_stage": self.home_stage,
                "move_stage": self.move_stage,
                "set_illumination": self.set_illumination,
                #"set_message_dict": self.set_message_dict,
                #"get_message_dict": self.get_message_dict,
                "script_executor": self.script_executor,
                "lightsheet_scan": self.scan_lightsheet,
                "stage_scan": self.stage_scan,
                "create_qttabwidget": self.create_qttabwidget,
                "autofocus": self.autofocus,
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
    Executes a Python script within the HyphaController class to control a microscope, accessible via 'self'. Scripts can orchestrate complex workflows using methods provided for microscope manipulation, incorporating loops and conditions. The script must be safe, without malicious elements, local file manipulation, or network access. Key methods include e.g.:
    - `self.move_stage(kwargs)` using MoveToPositionInput.schema() for xyz movement.
    - `self.set_illumination(kwargs)` using SetIlluminationInput.schema() to adjust illumination (0-1023).
    - `self.snap_image(kwargs)` using SnapImageInput.schema() to capture or process images.
    Execution results are stored in a 'result' variable for chatbot feedback. Scripts can import known libraries (e.g., time, numpy) for additional functionality.
    """
    script: str = Field(description="The Python script to execute.")
    context: dict = Field(description="Context information containing user details.")

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
    gain: int = Field(description="Set the microscope camera's gain. A higher gain can increase sensitivity, especailly helpful in low light settings ")
    filepath: Optional[str]  = Field(description="The path to save the captured image. It will be a tif, so the extension does not need to be added. If None, it is not saved")
    imageProcessingFunction: str = Field(description="The Python function to use for processing the image. Default is empty. image is the 2D array from the detector Example: def processImage(image): return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY). Avoid returning images since this is too much bandwidth. Return parameters from the function instead. Avoid using cv2")
    returnAsNumpy: bool = Field(description="Return the image as a numpy array if True, else return the URl to the image in the Hypha DataStore. If you need to display it in the chat, keep it False to return the datastore ")

class RecordingVideo(BaseModel):
    '''
    Record a video from the microscope camera for a specified duration and save it to a specified file path.
    '''
    duration: int = Field(description="The duration of the video recording in seconds.")
    filepath: str = Field(description="The path to save the recorded video. It will be a tif, so the extension does not need to be added. If None, it is not saved.")
    framerate: int = Field(description="The frame rate of the video. Default is 30 fps.")
    stop: bool = Field(description="Stop any ongoing video.")

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


class StageScanInput(BaseModel):
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

class AutoFocusInput(BaseModel):
    """Perform an autofocus of the microscope increase sharpness of the image."""
    minZ: float = Field(description="The minimum Z position to scan. Example: minZ=-100")
    maxZ: float = Field(description="The maximum Z position to scan. Example: maxZ=100")
    stepSize: float = Field(description="The step size to move the stage. Example: stepSize=10")

class SetIlluminationInput(BaseModel):
    """Set the illumination of the microscope."""
    channel: int = Field(description="Set the channel of the illumination. The value should choosed from this list: [0, 1, 2, 3] ")
    intensity: float = Field(description="Set the intensity of the illumination. The value should be between 0 and 100; ")

class HomeStageInput(BaseModel):
    """Home the stage."""
    axis: str = Field(description="The axis to home. Default is X. Available options are: X, Y, Z, A.")

class MovePositionerInput(BaseModel):
    """Move the stage either to a specific position or relative, the unit of distance is micrometers. """
    distance: float = Field(description="The distance to move the stage if is_absolute is false, otherwise the position in absolute coordinates. The unit is micrometers.")
    is_absolute: bool = Field(description="Move the stage to an absolute position if True, otherwise move by a relative distance.")
    axis: str = Field(description="The axis to move. Default is X. Available options are: X, Y, Z, A.")
    speed: float = Field(description="The speed of the stage movement. The unit is micrometers per second. Default is 1000")

class CreateQTTabWidget(BaseModel):
    """Create a QT widget that executes a formely created function string on a button press.
    an example widget:
    from qtpy import QtWidgets
    def _execute():
        self.start_service("UC2_microscope")
    self._widget.tab3 = QtWidgets.QWidget()
    self._widget.mButtonExecute = QtWidgets.QPushButton('Execute')
    self._widget.mButtonExecute.clicked.connect(_execute)
    self._widget.tab3_layout = QtWidgets.QVBoxLayout(self._widget.tab3)
    self._widget.tab3_layout.addWidget(self._widget.mButtonExecute)"""
    functionString: str = Field(description="The function string to execute.")
    qtWidgetFunctionString: str = Field(description="The function string to define the QT Widget that triggers the execution of the function coming from the chat bot. The widget has to be integrated into: self._widget.tab3")
    buttonText: str = Field(description="The text to display on the button.")

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


if __name__ == "__main__":
    # connect to hypha service
    mHyphaController = HyphaController()
    mHyphaController._loginHypha()


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
