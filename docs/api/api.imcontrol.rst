.. role:: raw-html-m2r(raw)
   :format: html


class **api.imcontrol** (builtins.object)  
-----------------------------------------------

These functions are available in the api.imcontrol object.  

Methods defined here:  

**getDetectorNames** () from
imswitch.imcontrol.controller.controllers.SettingsController.SettingsController

Returns the device names of all detectors. These device names can\ :raw-html-m2r:`<br>`
be passed to other detector-related functions.

**getLaserNames** () from
imswitch.imcontrol.controller.controllers.LaserController.LaserController

Returns the device names of all lasers. These device names can be\ :raw-html-m2r:`<br>`
passed to other laser-related functions.

**getPositionerNames** () from
imswitch.imcontrol.controller.controllers.PositionerController.PositionerController

Returns the device names of all positioners. These device names can\ :raw-html-m2r:`<br>`
be passed to other positioner-related functions.

**getPositionerPositions** () from
imswitch.imcontrol.controller.controllers.PositionerController.PositionerController

Returns the positions of all positioners.

**loadScanParamsFromFile** (filePath) from
imswitch.imcontrol.controller.controllers.ScanController.ScanController

Loads scanning parameters from the specified file.

**movePositioner** (positionerName, axis, dist) from
imswitch.imcontrol.controller.controllers.PositionerController.PositionerController

Moves the specified positioner axis by the specified number of\ :raw-html-m2r:`<br>`
micrometers.

**runScan** (hasStarted=False) from
imswitch.imcontrol.controller.controllers.ScanController.ScanController

Runs a scan with the set scanning parameters.

**saveScanParamsToFile** (filePath) from
imswitch.imcontrol.controller.controllers.ScanController.ScanController

Saves the set scanning parameters to the specified file.

**setDetectorBinning** (detectorName, binning) from
imswitch.imcontrol.controller.controllers.SettingsController.SettingsController

Sets binning value for the specified detector.

**setDetectorParameter** (detectorName, parameterName, value) from
imswitch.imcontrol.controller.controllers.SettingsController.SettingsController

Sets the specified detector-specific parameter to the specified\ :raw-html-m2r:`<br>`
value.

**setDetectorROI** (detectorName, frameStart, shape) from
imswitch.imcontrol.controller.controllers.SettingsController.SettingsController

Sets the ROI for the specified detector. frameStart is a tuple\ :raw-html-m2r:`<br>`
(x0, y0) and shape is a tuple (width, height).

**setDetectorToRecord** (detectorName) from
imswitch.imcontrol.controller.controllers.RecordingController.RecordingController

Sets which detectors to record. One can also pass -1 as the\ :raw-html-m2r:`<br>`
argument to record the current detector, or -2 to record all detectors.

**setLaserActive** (laserName, active) from
imswitch.imcontrol.controller.controllers.LaserController.LaserController

Sets whether the specified laser is powered on.

**setLaserValue** (laserName, value) from
imswitch.imcontrol.controller.controllers.LaserController.LaserController

Sets the value of the specified laser, in the units that the laser\ :raw-html-m2r:`<br>`
uses.

**setLiveViewActive** (active) from
imswitch.imcontrol.controller.controllers.ViewController.ViewController

Sets whether the LiveView is active and updating.

**setLiveViewCrosshairVisible** (visible) from
imswitch.imcontrol.controller.controllers.ViewController.ViewController

Sets whether the LiveView crosshair is visible.

**setLiveViewGridVisible** (visible) from
imswitch.imcontrol.controller.controllers.ViewController.ViewController

Sets whether the LiveView grid is visible.

**setPositioner** (positionerName, axis, position) from
imswitch.imcontrol.controller.controllers.PositionerController.PositionerController

Moves the specified positioner axis to the specified position.

**setPositionerStepSize** (positionerName, stepSize) from
imswitch.imcontrol.controller.controllers.PositionerController.PositionerController

Sets the step size of the specified positioner to the specified\ :raw-html-m2r:`<br>`
number of micrometers.

**setRecFilename** (filename) from
imswitch.imcontrol.controller.controllers.RecordingController.RecordingController

Sets the name of the file to record to. This only sets the name of\ :raw-html-m2r:`<br>`
the file, not the full path. One can also pass None as the argument to\ :raw-html-m2r:`<br>`
use a default time-based filename.

**setRecFolder** (folderPath) from
imswitch.imcontrol.controller.controllers.RecordingController.RecordingController

Sets the folder to save recordings into.

**setRecModeScanOnce** () from
imswitch.imcontrol.controller.controllers.RecordingController.RecordingController

Sets the recording mode to record a single scan.

**setRecModeScanTimelapse** (secondsToRec, freqSeconds) from
imswitch.imcontrol.controller.controllers.RecordingController.RecordingController

Sets the recording mode to record a timelapse of scans.

**setRecModeSpecFrames** (numFrames) from
imswitch.imcontrol.controller.controllers.RecordingController.RecordingController

Sets the recording mode to record a specific number of frames.

**setRecModeSpecTime** (secondsToRec) from
imswitch.imcontrol.controller.controllers.RecordingController.RecordingController

Sets the recording mode to record for a specific amount of time.

**setRecModeUntilStop** () from
imswitch.imcontrol.controller.controllers.RecordingController.RecordingController

Sets the recording mode to record until recording is manually\ :raw-html-m2r:`<br>`
stopped.

**signals** () from
imswitch.imcontrol.controller.CommunicationChannel.CommunicationChannel

Returns signals that can be used with e.g. the getWaitForSignal\ :raw-html-m2r:`<br>`
action. Currently available signals are:  


* acquisitionStarted  
* acquisitionStopped  
* recordingStarted  
* recordingEnded  
* scanEnded

**snapImage** () from
imswitch.imcontrol.controller.controllers.RecordingController.RecordingController

Take a snap and save it to a .tiff file at the set file path.

**startRecording** () from
imswitch.imcontrol.controller.controllers.RecordingController.RecordingController

Starts recording with the set settings to the set file path.

**stepPositionerDown** (positionerName, axis) from
imswitch.imcontrol.controller.controllers.PositionerController.PositionerController

Moves the specified positioner axis in negative direction by its\ :raw-html-m2r:`<br>`
set step size.

**stepPositionerUp** (positionerName, axis) from
imswitch.imcontrol.controller.controllers.PositionerController.PositionerController

Moves the specified positioner axis in positive direction by its\ :raw-html-m2r:`<br>`
set step size.

**stopRecording** () from
imswitch.imcontrol.controller.controllers.RecordingController.RecordingController

Stops recording.

----

Data descriptors defined here:  

**\ **dict**\ **

dictionary for instance variables (if defined)

**\ **weakref**\ **

list of weak references to the object (if defined)
