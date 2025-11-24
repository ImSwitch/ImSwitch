*************
api.imcontrol
*************

.. class:: api.imcontrol

   These functions are available in the api.imcontrol object. 

   .. method:: getDetectorNames() -> List[str]

      Returns the device names of all detectors. These device names can
      be passed to other detector-related functions. 

   .. method:: getLaserNames() -> List[str]

      Returns the device names of all lasers. These device names can be
      passed to other laser-related functions. 

   .. method:: getPositionerNames() -> List[str]

      Returns the device names of all positioners. These device names can
      be passed to other positioner-related functions. 

   .. method:: getPositionerPositions() -> Dict[str, Dict[str, float]]

      Returns the positions of all positioners. 

   .. method:: loadScanParamsFromFile(filePath: str) -> None #comment from Simone: I tink originally from basecontroller, now also scancontrollerpointscan (I guess make sure only one is in the setup)

      Loads scanning parameters from the specified file.

   .. method:: changeScanCenterPos(positionerName: str, centerPos: float) -> None #new from Simone

      set the center of the scan 

   .. method:: changed3StepDelayPar(d3StepDelayPar: float) -> None #new from Simone

      set the d3Stepdelay parameter (additional parameter rom the pointscan widget, mostly relevant for the polarization during scan)

   .. method:: changeScanSize(positionerName: str, size: float) -> None

      change scan size of positioner

   .. method:: movePositioner(positionerName: str, axis: str, dist: float) -> None

      Moves the specified positioner axis by the specified number of
      micrometers. 

   .. method:: runScan() -> None

      Runs a scan with the set scanning parameters. 
   
   .. method:: saveScanParamsToFile(filePath: str) -> None

      Saves the set scanning parameters to the specified file. 

   .. method:: setDetectorBinning(detectorName: str, binning: int) -> None

      Sets binning value for the specified detector. 

   .. method:: setDetectorParameter(detectorName: str, parameterName: str, value: Any) -> None

      Sets the specified detector-specific parameter to the specified
      value. 

   .. method:: setDetectorROI(detectorName: str, frameStart: Tuple[int, int], shape: Tuple[int, int]) -> None

      Sets the ROI for the specified detector. frameStart is a tuple
      (x0, y0) and shape is a tuple (width, height). 

   .. method:: setDetectorToRecord(detectorName: Union[List[str], str, int], multiDetectorSingleFile: bool = False) -> None

      Sets which detectors to record. One can also pass -1 as the
      argument to record the current detector, or -2 to record all detectors.
      

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

   .. method:: setPositioner(positionerName: str, axis: str, position: float) -> None

      Moves the specified positioner axis to the specified position. 

   .. method:: setPositionerStepSize(positionerName: str, stepSize: float) -> None

      Sets the step size of the specified positioner to the specified
      number of micrometers. 

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

   .. method:: signals() -> Mapping[str, imswitch.imcommon.framework.qt.Signal]

      Returns signals that can be used with e.g. the getWaitForSignal
      action. Currently available signals are:
      
      - acquisitionStarted
      - acquisitionStopped
      - recordingStarted
      - recordingEnded
      - scanEnded
      
      They can be accessed like this: api.imcontrol.signals().scanEnded
      

   .. method:: snapImage() -> None

      Take a snap and save it as the selected file format at the set file path. 

   .. method:: startRecording() -> None

      Starts recording with the set settings to the set file path. 

   .. method:: stepPositionerDown(positionerName: str, axis: str) -> None

      Moves the specified positioner axis in negative direction by its
      set step size. 

   .. method:: stepPositionerUp(positionerName: str, axis: str) -> None

      Moves the specified positioner axis in positive direction by its
      set step size. 

   .. method:: stopRecording() -> None

      Stops recording. 
   
   .. method:: setMask(maskMode: str) -> None 
      
      Sets SLM Mask to Gaussian or Donut or etc. Available: Donut, TopHat, Half, Gauss, Hex, Quad, Split, Black

   .. method:: loadParams() -> None

      Loads saved SLM parameters from file
   
   .. method:: toggleSLMDisplay(bool) -> None

      Enable SLM display end thereby turn on

   .. method:: moveAbs(name: str, pos: str) -> None or float?

      Get rotator with name to move to posisition pos

   .. method:: changeRotationParameters(rotationPars: List[str])

      change rotation step, start angle and stop angle

   .. method:: loadCalibration(calibname: str) -> None

      load rotation calibration

   .. method:: activateRotScan(activate: bool) -> None

      activate rotation scan on d3 scan axis

   .. method:: getScanParameters() -> None

      From etSTEd controller.
      Load the scan parameters of the scan widget for etSTED
