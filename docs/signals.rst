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
   self._commChannel.sigSendScanParameters.connect(lambda analogParams, digitalParams, positionersScan: self.assignScanParameters(analogParams, digitalParams, positionersScan))

See below for a list of all available signals in the CommunicationChannel currently, with their emission points.

List of available signals
==============================

.. autoclassconheader:: imswitch.imcontrol.controller.CommunicationChannel.sigUpdateImage(str, np.ndarray, bool, list, bool)
Origin: each ``DetectorManager``, through ``DetectorsManager`` and ``MasterController``
Connections: ``ImageController``, ``EtSTEDController``, ``AlignXYController``, ``AlignAverageController``
Content: (detectorName, image, init, scale, isCurrentDetector)
Explanation: Emitted when the image of a detector is update (camera frame pulled, point-detector image updated etc.), and is used to e.g. update the live view.

.. autoclassconheader:: imswitch.imcontrol.controller.CommunicationChannel.sigAcquisitionStarted()
Origin: 
Connections: -
Content: 
Explanation: 

.. autoclassconheader:: imswitch.imcontrol.controller.CommunicationChannel.sigAcquisitionStopped()
Origin: 
Connections: -
Content: 
Explanation: 

.. autoclassconheader:: imswitch.imcontrol.controller.CommunicationChannel.sigScriptExecutionFinished()
Origin: 
Connections: -
Content: 
Explanation: 
    
.. autoclassconheader:: imswitch.imcontrol.controller.CommunicationChannel.sigAdjustFrame(object)
Origin: 
Connections: -
Content: 
Explanation: 
    
.. autoclassconheader:: imswitch.imcontrol.controller.CommunicationChannel.sigDetectorSwitched(str, str)
Origin: 
Connections: -
Content: 
Explanation: 
    
.. autoclassconheader:: imswitch.imcontrol.controller.CommunicationChannel.sigGridToggled(bool)
Origin: 
Connections: 
Content: 
Explanation: 
    
.. autoclassconheader:: imswitch.imcontrol.controller.CommunicationChannel.sigCrosshairToggled(bool)
Origin: 
Connections: 
Content: 
Explanation: 
    
.. autoclassconheader:: imswitch.imcontrol.controller.CommunicationChannel.sigAddItemToVb(object)
Origin: 
Connections: 
Content: 
Explanation: 
    
.. autoclassconheader:: imswitch.imcontrol.controller.CommunicationChannel.sigRemoveItemFromVb(object)
Origin: 
Connections: 
Content: 
Explanation: 
    
.. autoclassconheader:: imswitch.imcontrol.controller.CommunicationChannel.sigRecordingStarted()
Origin: 
Connections: 
Content: 
Explanation: 
    
.. autoclassconheader:: imswitch.imcontrol.controller.CommunicationChannel.sigRecordingEnded()
Origin: 
Connections: 
Content: 
Explanation: 
    
.. autoclassconheader:: imswitch.imcontrol.controller.CommunicationChannel.sigUpdateRecFrameNum(int)
Origin: 
Connections: 
Content: 
Explanation: 
    
.. autoclassconheader:: imswitch.imcontrol.controller.CommunicationChannel.sigUpdateRecTime(int)
Origin: 
Connections: 
Content: 
Explanation: 
    
.. autoclassconheader:: imswitch.imcontrol.controller.CommunicationChannel.sigMemorySnapAvailable(str, np.ndarray, object, bool)
Origin: 
Connections: 
Content: 
Explanation: 
    
.. autoclassconheader:: imswitch.imcontrol.controller.CommunicationChannel.sigRunScan(bool, bool)
Origin: 
Connections: 
Content: 
Explanation: 
    
.. autoclassconheader:: imswitch.imcontrol.controller.CommunicationChannel.sigAbortScan()
Origin: 
Connections: 
Content: 
Explanation: 
    
.. autoclassconheader:: imswitch.imcontrol.controller.CommunicationChannel.sigScanStarting()
Origin: 
Connections: 
Content: 
Explanation: 
    
.. autoclassconheader:: imswitch.imcontrol.controller.CommunicationChannel.sigScanBuilt(object)
Origin: 
Connections: 
Content: 
Explanation: 
    
.. autoclassconheader:: imswitch.imcontrol.controller.CommunicationChannel.sigScanStarted()
Origin: 
Connections: 
Content: 
Explanation: 
    
.. autoclassconheader:: imswitch.imcontrol.controller.CommunicationChannel.sigScanDone()
Origin: 
Connections: 
Content: 
Explanation: 

.. autoclassconheader:: imswitch.imcontrol.controller.CommunicationChannel.sigScanEnded()
Origin: 
Connections: 
Content: 
Explanation: 

.. autoclassconheader:: imswitch.imcontrol.controller.CommunicationChannel.sigSLMMaskUpdated(object)
Origin: 
Connections: 
Content: 
Explanation: 

.. autoclassconheader:: imswitch.imcontrol.controller.CommunicationChannel.sigToggleBlockScanWidget(bool)
Origin: 
Connections: 
Content: 
Explanation: 

.. autoclassconheader:: imswitch.imcontrol.controller.CommunicationChannel.sigSnapImg()
Origin: 
Connections: 
Content: 
Explanation: 

.. autoclassconheader:: imswitch.imcontrol.controller.CommunicationChannel.sigSnapImgPrev(str, np.ndarray, str)
Origin: 
Connections: 
Content: 
Explanation: 

.. autoclassconheader:: imswitch.imcontrol.controller.CommunicationChannel.sigRequestScanParameters()
Origin: 
Connections: 
Content: 
Explanation: 

.. autoclassconheader:: imswitch.imcontrol.controller.CommunicationChannel.sigSendScanParameters(dict, dict, object)
Origin: 
Connections: 
Content: 
Explanation: 

.. autoclassconheader:: imswitch.imcontrol.controller.CommunicationChannel.sigSetAxisCenters(object, object)
Origin: 
Connections: 
Content: 
Explanation: 

.. autoclassconheader:: imswitch.imcontrol.controller.CommunicationChannel.sigStartRecordingExternal()
Origin: 
Connections: 
Content: 
Explanation: 

.. autoclassconheader:: imswitch.imcontrol.controller.CommunicationChannel.sigRequestScanFreq()
Origin: 
Connections: 
Content: 
Explanation: 

.. autoclassconheader:: imswitch.imcontrol.controller.CommunicationChannel.sigSendScanFreq(float)
Origin: 
Connections: 
Content: 
Explanation: 

.. autoclassconheader:: imswitch.imcontrol.controller.CommunicationChannel.sigSaveFocus()
Origin: 
Connections: 
Content: 
Explanation: 

.. autoclassconheader:: imswitch.imcontrol.controller.CommunicationChannel.sigScanFrameFinished()
Origin: 
Connections: 
Content: 
Explanation: 

.. autoclassconheader:: imswitch.imcontrol.controller.CommunicationChannel.sigUpdateRotatorPosition(str)
Origin: 
Connections: 
Content: 
Explanation: 

.. autoclassconheader:: imswitch.imcontrol.controller.CommunicationChannel.sigSetSyncInMovementSettings(str, float)
Origin: 
Connections: 
Content: 
Explanation: 

.. autoclassconheader:: imswitch.imcontrol.controller.CommunicationChannel.sigNewFrame()
Origin: 
Connections: 
Content: 
Explanation: 

