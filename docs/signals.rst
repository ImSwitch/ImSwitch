*******************************
Communication channel signals
*******************************

The main way of defferent controllers to communicate with eachother in the ImSwitch structure is through the 
communication channel. Here, signals are implemented that can be emitted and read from every widget controller
throughout ImSwitch, as the communication channel is always passed when a controller instance is created.

The signals already defined in the communication channel are used by various controllers,
some have just a single connection while some are used by multiple controllers. The signals listed here can be 
extended if need be, if there is a function of a newly implemented widget that requires a new signal type. 
The signals additionally can take any objects to be sent through with the signal, defined in the signal definition
with the required object type. 
In order to implement a new signal connection, three steps have to be followed.

1. Create signal in the CommunicationChannel, with any object tpyes that should be sent with the signal emission.
2. Create an emission of the signal in the controller where the signal should originate.
3. Create a reading of the signal in the controller where the signal should be read, and connect it to a function.

An example of this implementation is ``sigSendScanParameters``, that can send all scan acquisition parameters from a 
ScanController to the EtSTEDController:

In communication channel:

.. code-block:: python

   sigSendScanParameters = Signal(dict, dict, object)

Emission of signal:

.. code-block:: python

   self._commChannel.sigSendScanParameters.emit(self._analogParameterDict, self._digitalParameterDict, self._positionersScan)

Connection of signal:

.. code-block:: python

   self._commChannel.sigSendScanParameters.connect(
      lambda analogParams, digitalParams, positionersScan: self.assignScanParameters(analogParams, digitalParams, positionersScan)
   )


See below for a list of all available signals in the CommunicationChannel currently, with their emission points.

List of available signals
==============================

.. currentmodule:: imswitch.imcontrol.controller.CommunicationChannel
.. attribute:: CommunicationChannel.sigUpdateImage(str, np.ndarray, bool, list, bool)

- Origin: each ``DetectorManager``, through ``DetectorsManager`` and ``MasterController``
- Connections: ``ImageController``, ``EtSTEDController``, ``AlignXYController``, ``AlignAverageController``
- Content: (``detectorName``, ``image``, ``init``, ``scale``, ``isCurrentDetector``)
- Explanation: emitted when the image of a detector is update (camera frame pulled, point-detector image updated etc.), and is used to e.g. update the live view.

.. attribute:: CommunicationChannel.sigAcquisitionStarted()

- Origin: each ``DetectorManager``, through ``DetectorsManager`` and ``MasterController``
- Connections: \\
- Content: \\
- Explanation: emitted all detectors start acquiring

.. attribute:: CommunicationChannel.sigAcquisitionStopped()

- Origin: each ``DetectorManager``, through ``DetectorsManager`` and ``MasterController``
- Connections: \\
- Content: \\
- Explanation: emitted all detectors stop acquiring

.. attribute:: CommunicationChannel.sigScriptExecutionFinished()

- Origin: ``CommunicationChannel``
- Connections: ``WatcherController``
- Content: \\
- Explanation: emitted when script from the ``ImScripting`` module has finished execution

.. attribute:: CommunicationChannel.sigAdjustFrame(object)
    
- Origin: ``SettingsController``
- Connections: ``ImageController``
- Content: ``tuple(int, int, int, int)`` with new detector shape (``x``, ``y``, ``width``, ``height``)
- Explanation: emitted when a detector has changed the current ROI

.. attribute:: CommunicationChannel.sigDetectorSwitched(str, str)

- Origin: ``SettingsController``
- Connections: ``DetectorsManager`` through ``MasterController``
- Content: ``newDetectorName``, ``oldDetectorName``
- Explanation: emitted when a different detector is selected from the GUI list of available detectors

.. attribute:: CommunicationChannel.sigGridToggled(bool)
    
- Origin: ``ViewWidget`` through ``ViewController``
- Connections: ``ImageController``
- Content: ``True`` if grid activated, ``False`` otherwise
- Explanation: emitted when the grid is toggled on or off in the image viewer

.. attribute:: CommunicationChannel.sigCrosshairToggled(bool)
    
- Origin: ``ViewWidget`` through ``ViewController``
- Connections: ``ImageController``
- Content: ``True`` if crosshair activated, ``False`` otherwise
- Explanation: emitted when the crosshair is toggled on or off in the image viewer

.. attribute:: CommunicationChannel.sigAddItemToVb(object)
    
- Origin: 

  - ``SettingsController``
  - ``EtSTEDController``
  - ``BeadRecController``
  - ``AlignXYController``
  - ``AlignmentLineController``
  - ``AlignAverageController``
- Connections: ``ImageController``
- Content: ``item`` dependent on specific controller implementation
- Explanation: adds a new item to the image viewer

.. attribute:: CommunicationChannel.sigRemoveItemFromVb(object)

- Origin: \\
- Connections: ``ImageController``
- Content: ``item`` dependent on specific controller implementation
- Explanation: removes an item from the image viewer

.. attribute:: CommunicationChannel.sigRecordingStarted()
    
- Origin: ``RecordingManager``, passing first by ``RecordingController`` and then ``MasterController``
- Connections: \\
- Content: \\
- Explanation: emitted when a new recording is started

.. attribute:: CommunicationChannel.sigRecordingEnded()

- Origin: ``RecordingManager``, passing first by ``RecordingController`` and then ``MasterController``
- Connections: ``EtSTEDController``
- Content: \\
- Explanation: emitted when a recording is ended

.. attribute:: CommunicationChannel.sigUpdateRecFrameNum(int)
    
- Origin: ``RecordingController`` through ``MasterController``
- Connections: \\
- Content: ``frameNum`` of the current recording
- Explanation: emitted when the frame number of the current recording is updated (in case of a stack recording)

.. attribute:: CommunicationChannel.sigUpdateRecTime(int)

- Origin: ``RecordingController`` through ``MasterController``
- Connections: \\
- Content: ``recTime`` of the current recording
- Explanation: emitted when the recording time of the current recording is updated (in case of a time recording)

.. attribute:: CommunicationChannel.sigMemorySnapAvailable(str, np.ndarray, object, bool)

- Origin: 
- Connections: TBD
- Content: 
- Explanation: 

.. attribute:: CommunicationChannel.sigRunScan(bool, bool)

- Origin: 
- Connections: TBD
- Content: 
- Explanation: 

.. attribute:: CommunicationChannel.sigAbortScan()

- Origin: 
- Connections: TBD
- Content: 
- Explanation: 

.. attribute:: CommunicationChannel.sigScanStarting()

- Origin: 
- Connections: TBD
- Content: 
- Explanation: 

.. attribute:: CommunicationChannel.sigScanBuilt(object)

- Origin: 
- Connections: TBD
- Content: 
- Explanation: 

.. attribute:: CommunicationChannel.sigScanStarted()

- Origin: 
- Connections: TBD
- Content: 
- Explanation: 

.. attribute:: CommunicationChannel.sigScanDone()

- Origin: 
- Connections: TBD
- Content: 
- Explanation: 

.. attribute:: CommunicationChannel.sigScanEnded()

- Origin: 
- Connections: TBD
- Content: 
- Explanation: 

.. attribute:: CommunicationChannel.sigSLMMaskUpdated(object)

- Origin: 
- Connections: TBD
- Content: 
- Explanation: 

.. attribute:: CommunicationChannel.sigToggleBlockScanWidget(bool)

- Origin: 
- Connections: TBD
- Content: 
- Explanation: 

.. attribute:: CommunicationChannel.sigSnapImg()

- Origin: 
- Connections: TBD
- Content: 
- Explanation: 

.. attribute:: CommunicationChannel.sigSnapImgPrev(str, np.ndarray, str)

- Origin: 
- Connections: TBD
- Content: 
- Explanation: 

.. attribute:: CommunicationChannel.sigRequestScanParameters()

- Origin: 
- Connections: TBD
- Content: 
- Explanation: 

.. attribute:: CommunicationChannel.sigSendScanParameters(dict, dict, object)

- Origin: 
- Connections: TBD
- Content: 
- Explanation: 

.. attribute:: CommunicationChannel.sigSetAxisCenters(object, object)

- Origin: 
- Connections: TBD
- Content: 
- Explanation: 

.. attribute:: CommunicationChannel.sigStartRecordingExternal()

- Origin: 
- Connections: TBD
- Content: 
- Explanation: 

.. attribute:: CommunicationChannel.sigRequestScanFreq()

- Origin: 
- Connections: TBD
- Content: 
- Explanation: 

.. attribute:: CommunicationChannel.sigSendScanFreq(float)

- Origin: 
- Connections: TBD
- Content: 
- Explanation: 

.. attribute:: CommunicationChannel.sigSaveFocus()

- Origin: 
- Connections: TBD
- Content: 
- Explanation: 

.. attribute:: CommunicationChannel.sigScanFrameFinished()

- Origin: 
- Connections: TBD
- Content: 
- Explanation: 

.. attribute:: CommunicationChannel.sigUpdateRotatorPosition(str)

- Origin: 
- Connections: TBD
- Content: 
- Explanation: 

.. attribute:: CommunicationChannel.sigSetSyncInMovementSettings(str, float)

- Origin: 
- Connections: TBD
- Content: 
- Explanation: 

.. attribute:: CommunicationChannel.sigNewFrame()

- Origin: 
- Connections: TBD
- Content: 
- Explanation: 

