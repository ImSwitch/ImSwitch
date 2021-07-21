*************
api.imcontrol
*************

.. class:: api.imcontrol

   These functions are available in the api.imcontrol object. 

   .. method:: getDetectorNames()

      Returns the device names of all detectors. These device names can
      be passed to other detector-related functions. 

   .. method:: getLaserNames()

      Returns the device names of all lasers. These device names can be
      passed to other laser-related functions. 

   .. method:: getPositionerNames()

      Returns the device names of all positioners. These device names can
      be passed to other positioner-related functions. 

   .. method:: getPositionerPositions()

      Returns the positions of all positioners. 

   .. method:: loadScanParamsFromFile(filePath)

      Loads scanning parameters from the specified file. 

   .. method:: movePositioner(positionerName, axis, dist)

      Moves the specified positioner axis by the specified number of
      micrometers. 

   .. method:: runScan(hasStarted=False)

      Runs a scan with the set scanning parameters. 

   .. method:: saveScanParamsToFile(filePath)

      Saves the set scanning parameters to the specified file. 

   .. method:: setDetectorBinning(detectorName, binning)

      Sets binning value for the specified detector. 

   .. method:: setDetectorParameter(detectorName, parameterName, value)

      Sets the specified detector-specific parameter to the specified
      value. 

   .. method:: setDetectorROI(detectorName, frameStart, shape)

      Sets the ROI for the specified detector. frameStart is a tuple
      (x0, y0) and shape is a tuple (width, height). 

   .. method:: setDetectorToRecord(detectorName)

      Sets which detectors to record. One can also pass -1 as the
      argument to record the current detector, or -2 to record all detectors.
      

   .. method:: setLaserActive(laserName, active)

      Sets whether the specified laser is powered on. 

   .. method:: setLaserValue(laserName, value)

      Sets the value of the specified laser, in the units that the laser
      uses. 

   .. method:: setLiveViewActive(active)

      Sets whether the LiveView is active and updating. 

   .. method:: setLiveViewCrosshairVisible(visible)

      Sets whether the LiveView crosshair is visible. 

   .. method:: setLiveViewGridVisible(visible)

      Sets whether the LiveView grid is visible. 

   .. method:: setPositioner(positionerName, axis, position)

      Moves the specified positioner axis to the specified position. 

   .. method:: setPositionerStepSize(positionerName, stepSize)

      Sets the step size of the specified positioner to the specified
      number of micrometers. 

   .. method:: setRecFilename(filename)

      Sets the name of the file to record to. This only sets the name of
      the file, not the full path. One can also pass None as the argument to
      use a default time-based filename. 

   .. method:: setRecFolder(folderPath)

      Sets the folder to save recordings into. 

   .. method:: setRecModeScanOnce()

      Sets the recording mode to record a single scan. 

   .. method:: setRecModeScanTimelapse(secondsToRec, freqSeconds)

      Sets the recording mode to record a timelapse of scans. 

   .. method:: setRecModeSpecFrames(numFrames)

      Sets the recording mode to record a specific number of frames. 

   .. method:: setRecModeSpecTime(secondsToRec)

      Sets the recording mode to record for a specific amount of time.
      

   .. method:: setRecModeUntilStop()

      Sets the recording mode to record until recording is manually
      stopped. 

   .. method:: signals()

      Returns signals that can be used with e.g. the getWaitForSignal
      action. Currently available signals are:
      
      - acquisitionStarted
      - acquisitionStopped
      - recordingStarted
      - recordingEnded
      - scanEnded
      

   .. method:: snapImage()

      Take a snap and save it to a .tiff file at the set file path. 

   .. method:: startRecording()

      Starts recording with the set settings to the set file path. 

   .. method:: stepPositionerDown(positionerName, axis)

      Moves the specified positioner axis in negative direction by its
      set step size. 

   .. method:: stepPositionerUp(positionerName, axis)

      Moves the specified positioner axis in positive direction by its
      set step size. 

   .. method:: stopRecording()

      Stops recording. 

