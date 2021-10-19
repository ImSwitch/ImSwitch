# -*- coding: utf-8 -*-

"""
Alvium Vimba camera implementation of the VimbaCameraStreamer class.

**NOTES:**

Still port used for image capture.
Preview port reserved for onboard GPU preview.

Video port:

* Splitter port 0: Image capture (if `use_video_port == True`)
* Splitter port 1: Streaming frames
* Splitter port 2: Video capture
* Splitter port 3: [Currently unused]

VimbaCameraStreamer streams at video_resolution

Camera capture resolution set to stream_resolution in frames()

Video port uses that resolution for everything. If a different resolution
is specified for video capture, this is handled by the resizer.

Still capture (if use_video_port == False) uses pause_stream
to temporarily increase the capture resolution.
"""

import logging
import time
import threading
from PIL import Image, ImageDraw
from datetime import datetime

# Type hinting
from typing import BinaryIO, Tuple, Union

import numpy as np

# Vimba camera interface
import from control.vimbapy.vicamera as vicamera

from from control.vimbapy.base import BaseCamera
from openflexure_microscope.utilities import json_to_ndarray, ndarray_to_json

# MAIN CLASS
class VimbaCameraStreamer(BaseCamera):
    """Implementation of VimbaCameraStreamer."""

    vicamera_settings_keys = [
        "framerate",
        "exposure_time",
        "gain",
        "blacklevel",
    ]

    nEmptyFrames = 0

    def __init__(self):
        # Run BaseCamera init
        BaseCamera.__init__(self)

        #: :py:class:`vicamera.vicamera`: Attached vicamera object
        self.vicamera: vicamera.vicamera = vicamera.vicamera()

        # Store state of VimbaCameraStreamer
        self.preview_active: bool = False

        # Reset variable states
        self.set_zoom(1.0)

        #: tuple: Resolution for image captures
        self.image_resolution: Tuple[int, int] = tuple(self.vicamera.MAX_RESOLUTION)
        #: tuple: Resolution for stream and video captures
        self.stream_resolution: Tuple[int, int] = (832, 624)
        #: tuple: Resolution for numpy array captures
        self.numpy_resolution: Tuple[int, int] = (1312, 976)

        self.jpeg_quality: int = 100  #: int: JPEG quality
        self.mjpeg_quality: int = 75  #: int: MJPEG quality
        self.mjpeg_bitrate: int = -1  #: int: MJPEG quality
        self.framerate: int = 10      #: int: Framerate in FPS
        # Solid bitrate options:
        # -1: Maximum
        # 25000000: High
        # 17000000: Normal
        # 5000000: Low (may impact fast AF)
        # 2500000: Very low (may impact fast AF)

        # Start camera streaming (it is always producing frames, OFM needs to grab latest)
        self.start_preview()

        # Start streaming
        self.stop: bool = False  # Used to indicate that the stream loop should break
        self.start_worker()
        # Wait until frames are available
        logging.info("Waiting for frames")
        self.stream.new_frame.wait()
        logging.debug("Camera initialised")



    @property
    def camera(self):
        logging.warning(
            "VimbaCameraStreamer.camera is deprecated. Replace with VimbaCameraStreamer.vicamera"
        )
        return self.vicamera

    @property
    def configuration(self) -> dict:
        """The current camera configuration."""
        return {"board": self.vicamera.revision}

    @property
    def state(self) -> dict:
        """The current read-only camera state."""
        return {}

    def close(self):
        """Close the Raspberry Pi VimbaCameraStreamer."""
        # Stop stream recording
        self.stop_stream()
        # Run BaseCamera close method
        super().close()
        # Detach Pi camera
        if self.vicamera:
            self.vicamera.stop_preview()
            self.vicamera.close()

    # HANDLE SETTINGS
    def read_settings(self) -> dict:
        """
        Return config dictionary of the VimbaCameraStreamer.
        """
        conf_dict: dict = {
            "stream_resolution": self.stream_resolution,
            "image_resolution": self.image_resolution,
            "numpy_resolution": self.numpy_resolution,
            "jpeg_quality": self.jpeg_quality,
            "mjpeg_quality": self.mjpeg_quality,
            "mjpeg_bitrate": self.mjpeg_bitrate,
            "vicamera": {},
        }

        # Include a subset of vicamera properties. Excludes lens shading table
        for key in VimbaCameraStreamer.vicamera_settings_keys:
            try:
                value = getattr(self.vicamera, key)
                logging.debug("Reading vicamera().%s: %s", key, value)
                conf_dict["vicamera"][key] = value
            except AttributeError:
                logging.debug("Unable to read vicamera attribute %s", (key))


        return conf_dict

    def update_settings(self, config: dict):
        """
        Write a config dictionary to the VimbaCameraStreamer config.

        The passed dictionary may contain other parameters not relevant to
        camera config. Eg. Passing a general config file will work fine.

        Args:
            config (dict): Dictionary of config parameters.
        """

        logging.debug("VimbaCameraStreamer: Applying config:")
        logging.debug(config)

        with self.lock(timeout=None):

            # Apply valid config params to vicamera object
            if not self.record_active:  # If not recording a video

                # vicamera parameters
                if "vicamera" in config:  # If new settings are given
                    self.apply_vicamera_settings(
                        config["vicamera"], pause_for_effect=True
                    )

                # VimbaCameraStreamer parameters
                for key, value in config.items():  # For each provided setting
                    if (key != "vicamera") and hasattr(self, key):
                        setattr(self, key, value)
            else:
                raise Exception(
                    "Cannot update camera config while recording is active."
                )

    def apply_vicamera_settings(
        self, settings_dict: dict, pause_for_effect: bool = True
    ):
        """

        Args:
            settings_dict (dict): Dictionary of properties to apply to the :py:class:`vicamera.vicamera`: object
            pause_for_effect (bool): Pause tactically to reduce risk of timing issues
        """
        # Set exposure time
        if "exposure_time" in settings_dict:
            logging.debug(
                "Applying exposure_time: %s", (settings_dict["exposure_time"])
            )
            self.vicamera.setExposureTime(settings_dict["exposure_time"])

        # Set gain 
        if "gain" in settings_dict:
            logging.debug(
                "Applying gain: %s", (settings_dict["gain"])
            )
            self.vicamera.setGain(settings_dict["gain"])
 
        # Set blacklevel
        if "blacklevel" in settings_dict:
            logging.debug(
                "Applying blacklevel: %s", (settings_dict["blacklevel"])
            )
            self.vicamera.setBlacklevel(settings_dict["blacklevel"])
 
         # Set blacklevel
        if "framerate" in settings_dict:
            logging.debug(
                "Applying framerate for displaying purposes: %s", (settings_dict["framerate"])
            )
            self.framerate = settings_dict["framerate"]
 

    def start_worker(self, **_) -> bool:
        """Start the background camera thread if it isn't running yet."""
        self.stop = False

        if not self.stream_active:
            # Start background frame thread
            self.thread = threading.Thread(target=self._thread)
            self.thread.daemon = True
            self.thread.start()
        return True

    def stop_worker(self, timeout: int = 5) -> bool:
        """Flag worker thread for stop. Waits for thread close or timeout."""
        logging.debug("Stopping worker thread")
        timeout_time = time.time() + timeout

        if self.stream_active:
            self.stop = True
            self.thread.join()  # Wait for stream thread to exit
            logging.debug("Waiting for stream thread to exit.")

        while self.stream_active:
            if time.time() > timeout_time:
                logging.debug("Timeout waiting for worker thread close.")
                raise TimeoutError("Timeout waiting for worker thread close.")
            else:
                time.sleep(1/self.framerate)
        return True

    def _thread(self):
        """Camera background thread."""
        # Set the camera object's frame iterator
        logging.debug("Entering worker thread.")

        self.stream_active = True

        while True:
            # Only serve frames at 1fps
            time.sleep(1/self.framerate)
            # Generate new dummy image
            self.grab_latestframe()

            try:
                if self.stop is True:
                    logging.debug("Worker thread flagged for stop.")
                    break

            except AttributeError:
                pass

        logging.debug("BaseCamera worker thread exiting...")
        # Set stream_activate state
        self.stream_active = False

    def start_recording(self, output: Union[str, BinaryIO], video_framerate=20):
        """Start recording.

        Start a new video recording, writing to a output object.

        Args:
            output: String or file-like object to write capture data to
            fmt (str): Format of the capture.
            quality (int): Video recording quality.

        Returns:
            output_object (str/BytesIO): Target object.

        """
        # TODO: Not yet implemented
        with self.lock(timeout=5):
            # Start recording method only if a current recording is not running
            if not self.record_active:

                # Start the camera video recording on port 2
                logging.info("Recording to %s", (output))

                self.vicamera.start_recording(
                    output,
                    video_framerate=video_framerate
                )

                # Update state
                self.record_active = True

                return output

            else:
                logging.warning(
                    "Cannot start a new recording\
                    until the current recording has stopped."
                )
                return None

    def stop_recording(self):
        """Stop the last started video recording on splitter port 2."""
        with self.lock(timeout=5):
            # Stop the camera video recording on port 2
            logging.info("Stopping recording")
            self.vicamera.stop_recording()
            logging.info("Recording stopped")

            # Update state
            self.record_active = False

    def grab_latestframe(self):

        # Create a dummy image to serve in the stream
        myframe = self.vicamera.getLatestFrame(is_raw=False)

        if not self.vicamera.getCameraConnected():
            if self.nEmptyFrames > 50:
                # Check if camera is running or not, TODO: VERY HACKY!
                # Essentially reconnect the thread instead of unplugging the camera?
                self.reconnect()
                self.nEmptyFrames = 0
            else:
                self.nEmptyFrames += 1

        if myframe is None:
            myframe = np.zeros((self.stream_resolution[1], self.stream_resolution[0]))

        else:
            myframe = np.squeeze(myframe)
        myframe = myframe[0:self.stream_resolution[1],0:self.stream_resolution[0]] # TODO: MAKE this fulscreen            
        image = Image.fromarray(np.uint8(myframe/np.max(myframe)*255))
        draw = ImageDraw.Draw(image)
        draw.text(
            (20, 70),
            "Alvium Camera connected: {}".format(
                datetime.now().strftime("%d/%m/%Y, %H:%M:%S")
            ),
        )
        
        # HACKY since there is no GUI: TODO: CHANGE
        if self.mjpeg_bitrate is not -1:
            self.mjpeg_quality = int(self.mjpeg_bitrate//1e5)
        else:
            self.mjpeg_quality = 10

        image.save(self.stream, format="JPEG", quality=self.mjpeg_quality)
        
    def set_zoom(self, zoom_value: Union[float, int] = 1.0) -> None:
        """
        Change the camera zoom, handling re-centering and scaling.
        """
        pass
        
        '''
        TODO: Want to implement this for VIMBA?
        with self.lock(timeout=None):
            self.zoom_value = float(zoom_value)
            if self.zoom_value < 1:
                self.zoom_value = 1
            # Richard's code for zooming !
            fov = self.vicamera.zoom
            centre = np.array([fov[0] + fov[2] / 2.0, fov[1] + fov[3] / 2.0])
            size = 1.0 / self.zoom_value
            # If the new zoom value would be invalid, move the centre to
            # keep it within the camera's sensor (this is only relevant
            # when zooming out, if the FoV is not centred on (0.5, 0.5)
            for i in range(2):
                if np.abs(centre[i] - 0.5) + size / 2 > 0.5:
                    centre[i] = 0.5 + (1.0 - size) / 2 * np.sign(centre[i] - 0.5)
            logging.info("setting zoom, centre %s, size %s", centre, size)
            new_fov = (centre[0] - size / 2, centre[1] - size / 2, size, size)
            self.vicamera.zoom = new_fov



        '''


    def start_preview(
        self, fullscreen: bool = True, window: Tuple[int, int, int, int] = None
    ):
        """Start the USB3 driven Alvium camera preview."""
        with self.lock(timeout=1):
            try:
                if not self.vicamera.preview:
                    logging.debug("Starting preview")
                    self.vicamera.start_preview(fullscreen=fullscreen, window=window, preview_resolution=self.stream_resolution)
                else:
                    logging.debug("Resizing preview")
                    if window:
                        self.vicamera.set_window(window)
                    if fullscreen:
                        self.vicamera.set_fullscreen(fullscreen)
                self.preview_active = True
            except Exception as e:
                logging.error(
                    "Error Vymba. Exception: %s",
                    (e),
                )

    def stop_preview(self):
        """Stop the on board GPU camera preview."""
        with self.lock(timeout=1):
            if self.vicamera.preview:
                #self.vicamera.stop_preview()
                self.preview_active = False

    
    def start_stream(self) -> None:
        logging.info("Starting Stream")
        pass        
        """
        Sets the camera resolution to the video/stream resolution, and starts recording if the stream should be active.
        
        with self.lock(timeout=None):
            # Reduce the resolution for video streaming
            try:
                # TODO: ADD the proper logic
                logging.info("Starting stream vicamera")
                self.vicamera._check_recording_stopped()  # pylint: disable=W0212
            except Exception as e :
                logging.info(
                    "Error while changing resolution: Recording already running? Exception: %s", (e)
                )
            else:
                self.vicamera.resolution = self.stream_resolution
                # Sprinkled a sleep to prevent camera getting confused by rapid commands
                time.sleep(0.2)

            # If the stream should be active
            try:
                # Start recording on stream port
                self.vicamera.start_recording(
                    self.stream,
                    format="mjpeg",
                    quality=self.mjpeg_quality,
                    bitrate=self.mjpeg_bitrate,  # RWB: disable bitrate control
                    # (bitrate control makes JPEG size less good as a focus
                    # metric)
                    splitter_port=1,
                )
            except Exception as e:
                logging.info("Error while starting preview: Recording already running. Exception: %s",(e))
            else:
                self.stream_active = True
                logging.debug(
                    "Started MJPEG stream at %s on port %s", self.stream_resolution, 1
                )
        """
    def stop_stream(self) -> None:
        logging.info("Stopping Stream")
        pass
        """
        Sets the camera resolution to the still-image resolution, and stops recording if the stream is active.

        Args:
            splitter_port (int): Splitter port to stop recording on
        
        with self.lock:
            # Stop the camera video recording on port 1
            try:
                self.vicamera.stop_recording(splitter_port=1)
            except Exception as e:
                logging.info("Not recording on splitter_port 1, Exception: %s",(e))
            else:
                self.stream_active = False
                logging.info(
                    "Stopped MJPEG stream on port %s. Switching to %s.",
                    1,
                    self.image_resolution,
                )

            # Increase the resolution for taking an image
            time.sleep(
                0.2
            )  # Sprinkled a sleep to prevent camera getting confused by rapid commands
            self.vicamera.resolution = self.image_resolution
        """

    def capture(
        self,
        output: Union[str, BinaryIO],
        fmt: str = "jpeg",
        use_video_port: bool = False,
        resize: Tuple[int, int] = None,
        bayer: bool = True,
        thumbnail: Tuple[int, int, int] = None,
    ):
        """
        Capture a still image to a StreamObject.

        Defaults to JPEG format.
        Target object can be overridden for development purposes.

        Args:
            output: String or file-like object to write capture data to
            fmt: Format of the capture.
            use_video_port: Capture from the video port used for streaming. Lower resolution, faster.
            resize: Resize the captured image.
            bayer: Store raw bayer data in capture
            thumbnail: Dimensions and quality (x, y, quality) of a thumbnail to generate, if supported

        Returns:
            output_object (str/BytesIO): Target object.
        """
        with self.lock:
            logging.info("Capturing to %s", (output))


            # Check if camera is running or not, TODO: VERY HACKY!
            # Essentially reconnect the thread instead of unplugging the camera?
            if not self.vicamera.getCameraConnected():
                self.reconnect()


            # Set resolution and stop stream recording if necessary
            #if not use_video_port:
            #    self.stop_stream()
            
            self.vicamera.capture(
                output,
                format=fmt,
                quality=self.jpeg_quality,
                resize=resize,
                bayer=(not use_video_port) and bayer,
                use_video_port=use_video_port,
                thumbnail=thumbnail,
            )

            

            # Set resolution and start stream recording if necessary
            #if not use_video_port:
            #    self.start_stream()

            return output
    
    def reconnect(self):
        logging.debug("Restarting camera thread - No camera attached?")
        self.vicamera.stop_preview()
        self.vicamera.close()
        del self.vicamera
        self.vicamera = vicamera.vicamera()
        self.vicamera.start_preview()

    def array(self, use_video_port: bool = True) -> np.ndarray:
        """Capture an uncompressed still RGB image to a Numpy array.

        Args:
            use_video_port (bool): Capture from the video port used for streaming. Lower resolution, faster.
            resize ((int, int)): Resize the captured image.

        Returns:
            output_array (np.ndarray): Output array of capture
        """
        with self.lock:
            logging.debug("Creating VIMBAnpArray")
            array = self.vicamera.capture(output="numpy")
            return array
