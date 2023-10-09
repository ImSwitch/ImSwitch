from typing import Mapping

import numpy as np
from imswitch.imcommon.framework import Signal, SignalInterface
from imswitch.imcommon.model import pythontools, APIExport, SharedAttributes
from imswitch.imcommon.model import initLogger


class CommunicationChannel(SignalInterface):
    """
    Communication Channel is a class that handles the communication between Master Controller
    and Widgets, or between Widgets.
    """

    sigUpdateImage = Signal(
        str, np.ndarray, bool, list, bool
    ) # (detectorName, image, init, scale, isCurrentDetector)
    """Signal emitted when a new image is available.
    
   - detectorName (``str``): The name of the detector that produced the image
   - image (``numpy.ndarray``): The image data as a numpy array
   - init (``bool``): Whether the image is the first image of a new acquisition
   - scale (``list``): The scale of the image as a list of two floats, [xScale, yScale]
   - isCurrentDetector (``bool``): Whether the image is from the currently selected detector
   """

    sigAcquisitionStarted = Signal()
    """ Signal emitted when acquisition is started. """

    sigAcquisitionStopped = Signal()
    """ Signal emitted when acquisition is stopped. """

    sigScriptExecutionFinished = Signal()
    """ Signal emitted when script from the ``ImScripting`` module has finished execution. """

    sigAdjustFrame = Signal(object)  # (shape)
    """ Signal emitted when the frame size is changed. 
    
    - shape (``tuple(int, int, int, int)``): new detector shape (``x``, ``y``, ``width``, ``height``)
    """

    sigDetectorSwitched = Signal(str, str)  # (newDetectorName, oldDetectorName)
    """ Signal emitted when the detector is switched from the user interface.
    
    - newDetectorName (``str``): The name of the new detector
    - oldDetectorName (``str``): The name of the old detector
    """

    sigGridToggled = Signal(bool)  # (enabled)
    """ Signal emitted when the grid is toggled from the user interface.
    
    - enabled (``bool``): Whether the grid is enabled
    """

    sigCrosshairToggled = Signal(bool)  # (enabled)
    """ Signal emitted when the crosshair is toggled from the user interface.
    
    - enabled (``bool``): Whether the crosshair is enabled    
    """

    sigAddItemToVb = Signal(object)  # (item)
    """ Signal emitted when an item is added to the image viewer.
    
    - item (``object``): The item to add
    """

    sigRemoveItemFromVb = Signal(object)  # (item)
    """ Signal emitted when an item is removed from the image viewer.
    
    - item (``object``): The item to remove
    """

    sigRecordingStarted = Signal()
    """ Signal emitted when recording is started.
    """

    sigRecordingEnded = Signal()
    """ Signal emitted when recording is ended.
    """

    sigUpdateRecFrameNum = Signal(int)  # (frameNumber)
    """ Signal emitted when the recording frame number is updated.
    
    - frameNumber (``int``): The new frame number
    """

    sigUpdateRecTime = Signal(int)  # (recTime)
    """ Signal emitted when the recording time is updated.
    
    - recTime (``int``): The new recording time
    """

    sigMemorySnapAvailable = Signal(
        str, np.ndarray, object, bool
    )  # (name, image, filePath, savedToDisk)
    """ Signal emitted when an image snap is available.
    
    - name (``str``): The name of the snap
    - image (``numpy.ndarray``): The image data as a numpy array
    - filePath (``object``): The file path of the snap
    - savedToDisk (``bool``): Whether the snap was saved to disk
    """

    sigRunScan = Signal(bool, bool)  # (recalculateSignals, isNonFinalPartOfSequence)
    """ Signal emitted when a scan is run.
    
    - recalculateSignals (``bool``): Whether the signals should be recalculated
    - isNonFinalPartOfSequence (``bool``): Whether the scan is a non-final part of a sequence
    """

    sigAbortScan = Signal()
    """ Signal emitted when a scan is aborted.
    """

    sigScanStarting = Signal()
    """ Signal emitted when a scan is starting.
    """

    sigScanBuilt = Signal(object)  # (deviceList)
    """ Signal emitted when a scan sequence has been prepared and is ready to be executed.
    
    - deviceList (``object``): The list of devices involved in the scan sequence.
    """

    sigScanStarted = Signal()
    """ Signal emitted when a scan is started.
    """

    sigScanDone = Signal()
    """ Signal emitted when a scan is done.
    """

    sigScanEnded = Signal()
    """ Signal emitted when a scan is ended.
    """

    sigSLMMaskUpdated = Signal(object)  # (mask)
    """ Signal emitted when the SLM mask is updated.
    
    - mask (``object``): The new SLM mask
    """

    sigToggleBlockScanWidget = Signal(bool)
    """ Signal emitted when the scan widget is blocked or unblocked.
    
    - blocked (``bool``): Whether the scan widget is blocked
    """

    sigSnapImg = Signal()
    """ Signal emitted when a snap is requested.
    """

    sigSnapImgPrev = Signal(str, np.ndarray, str)  # (detector, image, nameSuffix)
    """ Signal emitted when an image preview is to be sent.
    
    - detector (``str``): The name of the detector
    - image (``numpy.ndarray``): The image data as a numpy array
    - nameSuffix (``str``): The name suffix of the image
    """

    sigRequestScanParameters = Signal()
    """ Signal emitted when scan parameters are requested.
    """

    sigSendScanParameters = Signal(dict, dict, object)  # (analogParams, digitalParams, scannerList)
    """ Signal emitted when scan parameters are sent.
    
    - analogParams (``dict``): The analog parameters
    - digitalParams (``dict``): The digital parameters
    - scannerList (``object``): The list of scanners
    """

    sigSetAxisCenters = Signal(object, object)  # (axisDeviceList, axisCenterList)
    """ Signal emitted when the axis centers are set.
    
    - axisDeviceList (``object``): The list of axis devices
    - axisCenterList (``object``): The list of axis centers
    """

    sigStartRecordingExternal = Signal()
    """ TBD
    """

    sigRequestScanFreq = Signal()
    """ Signal emitted when the scan frequency is requested.
    """
    
    sigSendScanFreq = Signal(float)  # (scanPeriod)
    """ Signal emitted when the scan frequency is sent.
    
    - scanPeriod (``float``): The scan frequency in seconds
    """
    
    sigSaveFocus = Signal()
    """ Signal emitted when the focus is saved.
    """

    sigScanFrameFinished = Signal()  # TODO: emit this signal when a scanning frame finished, maybe in scanController if possible? Otherwise in APDManager for now, even if that is not general if you want to do camera-based experiments. Could also create a signal specifically for this from the scan curve generator perhaps, specifically for the rotation experiments, would that be smarter?
    """ Signal emitted when the scanning of a frame is finished.
    """
    
    sigUpdateRotatorPosition = Signal(str)  # (rotatorName)
    """ Signal emitted when the rotator position is updated.
    
    - rotatorName (``str``): The name of the rotator
    """

    sigSetSyncInMovementSettings = Signal(str, float)  # (rotatorName, position)
    """ Signal emitted when the sync-in movement settings are set.
    
    - rotatorName (``str``): The name of the rotator
    - position (``float``): The new rotor position
    """

    sigNewFrame = Signal()
    """ Signal emitted when a new frame is available.
    """

    # useq-schema related signals
    sigSetXYPosition = Signal(float, float)
    sigSetZPosition = Signal(float)
    sigSetExposure = Signal(float)
    sigSetSpeed = Signal(float)

    @property
    def sharedAttrs(self):
        return self.__sharedAttrs

    def __init__(self, main, setupInfo):
        super().__init__()
        self.__main = main
        self.__sharedAttrs = SharedAttributes()
        self.__logger = initLogger(self)
        self._scriptExecution = False
        self.__main._moduleCommChannel.sigExecutionFinished.connect(self.executionFinished)

    def getCenterViewbox(self):
        """ Returns the center point of the viewbox, as an (x, y) tuple. """
        if 'Image' in self.__main.controllers:
            return self.__main.controllers['Image'].getCenterViewbox()
        else:
            raise RuntimeError('Required image widget not available')

    def getDimsScan(self):
        if 'Scan' in self.__main.controllers:
            return self.__main.controllers['Scan'].getDimsScan()
        else:
            raise RuntimeError('Required scan widget not available')

    def getNumScanPositions(self):
        if 'Scan' in self.__main.controllers:
            return self.__main.controllers['Scan'].getNumScanPositions()
        else:
            raise RuntimeError('Required scan widget not available')

    def get_image(self, detectorName=None):
        return self.__main.controllers['View'].get_image(detectorName)

    @APIExport(runOnUIThread=True)
    def acquireImage(self) -> None:
        image = self.get_image()
        self.output.append(image)

    def runScript(self, text):
        self.output = []
        self._scriptExecution = True
        self.__main._moduleCommChannel.sigRunScript.emit(text)

    def executionFinished(self):
        self.sigScriptExecutionFinished.emit()
        self._scriptExecution = False

    def isExecuting(self):
        return self._scriptExecution

    @APIExport()
    def signals(self) -> Mapping[str, Signal]:
        """ Returns signals that can be used with e.g. the getWaitForSignal
        action. Currently available signals are:

         - acquisitionStarted
         - acquisitionStopped
         - recordingStarted
         - recordingEnded
         - scanEnded

        They can be accessed like this: api.imcontrol.signals().scanEnded
        """

        return pythontools.dictToROClass({
            'acquisitionStarted': self.sigAcquisitionStarted,
            'acquisitionStopped': self.sigAcquisitionStopped,
            'recordingStarted': self.sigRecordingStarted,
            'recordingEnded': self.sigRecordingEnded,
            'scanEnded': self.sigScanEnded,
            'saveFocus': self.sigSaveFocus
        })


# Copyright (C) 2020-2022 ImSwitch developers
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
