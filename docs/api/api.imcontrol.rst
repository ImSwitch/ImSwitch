*************
api.imcontrol
*************

.. class:: api.imcontrol

   These functions are available in the api.imcontrol object. 

   .. method:: acquireImage() -> None

   .. method:: calibrateObjective()

   .. method:: changeScanPower(laserName, laserValue)

   .. method:: executeFunction(code: str)

   .. method:: getCurrentObjective()

   .. method:: getDetectorNames() -> List[str]

      Returns the device names of all detectors. These device names can
      be passed to other detector-related functions. 

   .. method:: getLaserNames() -> List[str]

      Returns the device names of all lasers. These device names can be
      passed to other laser-related functions. 

   .. method:: getVariable(variable_name: str)

   .. method:: get_image() -> starlette.responses.StreamingResponse

   .. method:: moveToObjectiveID(objectiveID, posObjective1=None, posObjective2=None)

   .. method:: post_json(path: str, payload: dict) -> str

      Sends the specified command to the RS232 device and returns a
      string encoded from the received bytes. 

   .. method:: sendTrigger(triggerId: int)

      Sends a trigger puls through external device 

   .. method:: send_serial(payload: str) -> str

      Sends the specified command to the RS232 device and returns a
      string encoded from the received bytes. 

   .. method:: setAllLED(state=None, intensity=None)

   .. method:: setAllLEDOff()

   .. method:: setAllLEDOn()

   .. method:: setDetectorBinning(detectorName: str, binning: int) -> None

      Sets binning value for the specified detector. 

   .. method:: setDetectorExposureTime(detectorName: str = None, exposureTime: float = 1) -> None

      Sets the exposure time for the specified detector. 

   .. method:: setDetectorGain(detectorName: str = None, gain: float = 0) -> None

      Sets the gain for the specified detector. 

   .. method:: setDetectorParameter(detectorName: str, parameterName: str, value: Any) -> None

      Sets the specified detector-specific parameter to the specified
      value. 

   .. method:: setDetectorROI(detectorName: str, frameStart: Tuple[int, int], shape: Tuple[int, int]) -> None

      Sets the ROI for the specified detector. frameStart is a tuple
      (x0, y0) and shape is a tuple (width, height). 

   .. method:: setDetectorToRecord(detectorName: Union[List[str], str, int], multiDetectorSingleFile: bool = False) -> None

      Sets which detectors to record. One can also pass -1 as the
      argument to record the current detector, or -2 to record all detectors.
      

   .. method:: setIntensity(intensity=None)

   .. method:: setLED(LEDid, state=None)

   .. method:: setLaserActive(laserName: str, active: bool) -> None

      Sets whether the specified laser is powered on. 

   .. method:: setLaserValue(laserName: str, value: Union[int, float]) -> None

      Sets the value of the specified laser, in the units that the laser
      uses. 

   .. method:: setLiveViewActive(active: bool) -> None

      Sets whether the LiveView is active and updating. 

   .. method:: setLiveViewCrosshairVisible(visible: bool) -> None

      Sets whether the LiveView crosshair is visible. 

   .. method:: setLiveViewGridVisible(visible: bool) -> None

      Sets whether the LiveView grid is visible. 

   .. method:: setRecFilename(filename: Optional[str]) -> None

      Sets the name of the file to record to. This only sets the name of
      the file, not the full path. One can also pass None as the argument to
      use a default time-based filename. 

   .. method:: setRecFolder(folderPath: str) -> None

      Sets the folder to save recordings into. 

   .. method:: setRecModeScanOnce() -> None

      Sets the recording mode to record a single scan. 

   .. method:: setRecModeScanTimelapse(lapsesToRec: int, freqSeconds: float, timelapseSingleFile: bool = False) -> None

      Sets the recording mode to record a timelapse of scans. 

   .. method:: setRecModeSpecFrames(numFrames: int) -> None

      Sets the recording mode to record a specific number of frames. 

   .. method:: setRecModeSpecTime(secondsToRec: Union[int, float]) -> None

      Sets the recording mode to record for a specific amount of time.
      

   .. method:: setRecModeUntilStop() -> None

      Sets the recording mode to record until recording is manually
      stopped. 

   .. method:: setSpecial(pattern, intensity=255, getReturn=False)

   .. method:: snapImage(output: bool = False, toList: bool = True) -> Optional[list]

      
      Take a snap and save it to a .tiff file at the set file path. 
      output: if True, return the numpy array of the image as a list if toList is True, or as a numpy array if toList is False
      toList: if True, return the numpy array of the image as a list, otherwise return it as a numpy array
      

   .. method:: snapImageToPath(fileName: str = '.')

      Take a snap and save it to a .tiff file at the given fileName. 

   .. method:: snapNumpyToFastAPI(detectorName: str = None, resizeFactor: float = 1) -> starlette.responses.Response

      
      Taking a snap and return it as a FastAPI Response object.
      detectorName: the name of the detector to take the snap from. If None, take the snap from the first detector.
      resizeFactor: the factor by which to resize the image. If <1, the image will be downscaled, if >1, nothing will happen.
      

   .. method:: startRecording() -> None

      Starts recording with the set settings to the set file path. 

   .. method:: stopRecording() -> None

      Stops recording. 

   .. method:: video_feeder() -> starlette.responses.StreamingResponse

      
      return a generator that converts frames into jpeg's reads to stream
      

