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

.. autoattribute:: CommunicationChannel.sigUpdateImage
   :annotation: = Signal(detectorName, image, init, scale, isCurrentDetector)

.. autoattribute:: CommunicationChannel.sigAcquisitionStarted
   :annotation: = Signal()

.. autoattribute:: CommunicationChannel.sigAcquisitionStopped
   :annotation: = Signal()

.. autoattribute:: CommunicationChannel.sigScriptExecutionFinished
   :annotation: = Signal()

.. autoattribute:: CommunicationChannel.sigAdjustFrame
   :annotation: = Signal(shape)

.. autoattribute:: CommunicationChannel.sigDetectorSwitched
   :annotation: = Signal(oldDetector, newDetector)

.. autoattribute:: CommunicationChannel.sigGridToggled
   :annotation: = Signal(enabled)

.. autoattribute:: CommunicationChannel.sigCrosshairToggled
   :annotation: = Signal(enabled)

.. autoattribute:: CommunicationChannel.sigAddItemToVb
   :annotation: = Signal(item)

.. autoattribute:: CommunicationChannel.sigRemoveItemFromVb
   :annotation: = Signal(item)

.. autoattribute:: CommunicationChannel.sigRecordingStarted
   :annotation: = Signal()

.. autoattribute:: CommunicationChannel.sigRecordingEnded
   :annotation: = Signal()

.. autoattribute:: CommunicationChannel.sigUpdateRecFrameNum
   :annotation: = Signal(frameNum)

.. autoattribute:: CommunicationChannel.sigUpdateRecTime
   :annotation: = Signal(recTime)
   
.. autoattribute:: CommunicationChannel.sigMemorySnapAvailable(str, np.ndarray, object, bool)
   :annotation: = Signal(name, image, filePath, savedToDisk)

.. autoattribute:: CommunicationChannel.sigRunScan
   :annotation: = Signal(recalculateSignals, isNonFinalPartOfSequence)

.. autoattribute:: CommunicationChannel.sigAbortScan
   :annotation: = Signal()

.. autoattribute:: CommunicationChannel.sigScanStarting
   :annotation: = Signal()

.. autoattribute:: CommunicationChannel.sigScanBuilt
   :annotation: = Signal(scan)

.. autoattribute:: CommunicationChannel.sigScanStarted
   :annotation: = Signal()

.. autoattribute:: CommunicationChannel.sigScanDone
   :annotation: = Signal()

.. autoattribute:: CommunicationChannel.sigScanEnded
   :annotation: = Signal()

.. autoattribute:: CommunicationChannel.sigSLMMaskUpdated
   :annotation: = Signal(mask)

.. autoattribute:: CommunicationChannel.sigToggleBlockScanWidget
   :annotation: = Signal(blocked)

.. autoattribute:: CommunicationChannel.sigSnapImg
   :annotation: = Signal()

.. autoattribute:: CommunicationChannel.sigSnapImgPrev
   :annotation: = Signal(detector, image, nameSuffix)

.. autoattribute:: CommunicationChannel.sigRequestScanParameters
   :annotation: = Signal()

.. autoattribute:: CommunicationChannel.sigSendScanParameters
   :annotation: = Signal(analogParams, digitalParams, scannerList)

.. autoattribute:: CommunicationChannel.sigSetAxisCenters
   :annotation: = Signal(axisDeviceList, axisCenterList)


.. autoattribute:: CommunicationChannel.sigStartRecordingExternal
   :annotation: = Signal()

.. autoattribute:: CommunicationChannel.sigRequestScanFreq
   :annotation: = Signal()

.. autoattribute:: CommunicationChannel.sigSendScanFreq
   :annotation: = Signal(scanPeriod)

.. autoattribute:: CommunicationChannel.sigSaveFocus
   :annotation: = Signal()

.. autoattribute:: CommunicationChannel.sigScanFrameFinished
   :annotation: = Signal()

.. autoattribute:: CommunicationChannel.sigUpdateRotatorPosition
   :annotation: = Signal(rotatorName)

.. autoattribute:: CommunicationChannel.sigSetSyncInMovementSettings
   :annotation: = Signal(rotatorName, position)

.. autoattribute:: CommunicationChannel.sigNewFrame
   :annotation: = Signal()
